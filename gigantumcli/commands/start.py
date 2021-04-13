import platform
from typing import Optional

from docker.errors import ImageNotFound, NotFound
import os
import webbrowser
import time
import requests
import uuid
import click

from gigantumcli.dockerinterface import DockerInterface
from gigantumcli.commands.install import install
from gigantumcli.config import ConfigOverrideFile
from gigantumcli.utilities import ask_question, is_running_as_admin, get_nvidia_driver_version


def _check_for_api(port: int = 10000, launch_browser: bool = False, timeout: int = 5):
    """Check for the API to be live for up to `timeout` seconds, then optionally launch a browser window

    Args:
        port(int): port the server is running on
        launch_browser(bool): flag indicating if the browser should be launched on success == True
        timeout(int): Number of seconds to wait for the API before returning
    Returns:
        bool: flag indicating if the API is ready
    """
    protocol = "http"
    if port == 443:
        protocol = "https"

    success = False
    for _ in range(timeout):
        time.sleep(1)
        try:
            resp = requests.get("{}://localhost:{}/api/ping?v={}".format(protocol, port, uuid.uuid4().hex),
                                verify=False)

            if resp.status_code == 200:
                success = True
                break
        except requests.exceptions.ConnectionError:
            # allow connection errors, which mean the API isn't up yet.
            pass

    if success is True and launch_browser is True:
        time.sleep(1)
        # If here, things look OK. Start browser
        webbrowser.open_new("{}://localhost:{}".format(protocol, port))

    return success


@click.command()
@click.option('--edge', '-e', type=bool, is_flag=True, default=False,
              help="Flag indicating if the edge version should be used. Note, you must have access "
                   "to this image and may need to log into DockerHub.")
@click.option('--wait', '-w', 'timeout', type=int, default=90,
              help="Number of seconds to wait for the Client to be ready.")
@click.option('--yes', '-y', 'accept_confirmation', is_flag=True, default=False,
              help="Flag to automatically accept all confirmation prompts")
@click.option('--tag', '-t', type=str, default=None,
              help="Provide a tag to explicitly run instead of the latest available.")
@click.option('--port', type=int, default=10000,
              help="Set the port on which the Client web server is exposed (10000).")
@click.option('--external', is_flag=True, default=False,
              help="Set if you wish to run the Client for external access. Default runs on localhost.")
@click.option('--working-dir', '-d', 'working_dir', type=str, default="~/gigantum",
              help="Set the Client working directory (`~/gigantum`).")
@click.pass_context
def start(ctx, edge: bool, timeout: int, tag: Optional[str] = None, port: int = 10000, working_dir: str = "~/gigantum",
          external: bool = False, accept_confirmation: bool = False) -> None:
    """Start Gigantum Client.

    This command will clean-up any lingering Gigantum managed containers and then start the Client on the specified
    port (default 10000).

    Note, only running on localhost:10000 is supported with Gigantum.com. When using a self-hosted server, you can
    use any additional hostnames and ports that have been added to the auth redirect allowlist by the system
    administrator.
    \f

    Args:
        edge(bool): Flag indicating if the install is stable or edge
        timeout: Number of seconds to wait for API to come up
        tag: Tag to run, defaults to latest
        port: port the server runs on
        working_dir: Location to mount as the Gigantum working directory
        external: Optional flag if you want to run on the external network interface (0.0.0.0)
        accept_confirmation: Optional Flag indicating if you should skip the confirmation and auto-accept
    """
    # Make sure user is not root
    if is_running_as_admin():
        raise click.UsageError("Do not run `gigantum start` as root.")

    # Make sure you are in browser mode if running on 80/443
    if external:
        config_file = ConfigOverrideFile(working_dir=working_dir)
        if not config_file.is_browser_middleware_selected():
            click.secho("WARNING: When running the Client with external network access you MUST enable the "
                        "`multi-user` auth mode.", fg='yellow')
            click.secho("Run `gigantum config set-auth-mode multi-user` to configure this.", fg='yellow')
            click.secho("Failure to do so could allow anyone to access a valid user session.", fg='yellow', bold=True)
            raise click.Abort()

    click.echo("Verifying Docker is available...")
    # Check if Docker is running
    docker_obj = DockerInterface()
    image_name = docker_obj.image_name(edge)

    if not tag:
        # Trying to update to the latest version
        tag = 'latest'
    image_name_with_tag = "{}:{}".format(image_name, tag)

    # Check if working dir exists
    working_dir = os.path.expanduser(working_dir)
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)

    # Check if application has been installed
    try:
        docker_obj.client.images.get(image_name_with_tag)
    except ImageNotFound:
        if ask_question("The Gigantum Client Docker image not found. Would you like to install it now?",
                        accept_confirmation):
            ctx.invoke(install, edge=edge)
        else:
            click.echo("Downloading the Gigantum Client Docker image is required to start the Client. "
                       "Please run `gigantum install`.")
            return

    # Check to see if already running
    try:
        if _check_for_api(port=port, launch_browser=False, timeout=1):
            click.echo("Client already running on http://localhost:{}".format(port))
            _check_for_api(port=port, launch_browser=True)
            click.echo("If page does not load, restart by running `gigantum stop` and then `gigantum start` again")
            return

        # remove any lingering gigantum managed containers
        docker_obj.cleanup_containers()

    except NotFound:
        # If here, the API isn't running and an older container isn't lingering, so just move along.
        pass

    # Start
    if external:
        interface = "0.0.0.0"
    else:
        interface = "127.0.0.1"

    port_mapping = {'10000/tcp': (interface, port)}

    # Make sure the container-container share volume exists
    if not docker_obj.share_volume_exists():
        docker_obj.create_share_volume()

    volume_mapping = {docker_obj.share_vol_name: {'bind': '/mnt/share', 'mode': 'rw'}}

    print('Host directory for Gigantum files: {}'.format(working_dir))
    if platform.system() == 'Windows':
        # windows docker has some eccentricities
        # no user ids, we specify a WINDOWS_HOST env var, and need to rewrite the paths for
        # bind-mounting inside the Client (see `dockerize_mount_path()` for details)
        rewritten_path = docker_obj.dockerize_mount_path(working_dir, image_name_with_tag)
        environment_mapping = {'HOST_WORK_DIR': rewritten_path,
                               'WINDOWS_HOST': 1}
        volume_mapping[working_dir] = {'bind': '/mnt/gigantum', 'mode': 'rw'}

    elif platform.system() == 'Darwin':
        # For macOS, use the cached mode for improved performance
        environment_mapping = {'HOST_WORK_DIR': working_dir,
                               'LOCAL_USER_ID':  os.getuid()}
        volume_mapping[working_dir] = {'bind': '/mnt/gigantum', 'mode': 'cached'}
    else:
        # For anything else, just use default mode.
        environment_mapping = {'HOST_WORK_DIR': working_dir,
                               'LOCAL_USER_ID':  os.getuid(),
                               'NVIDIA_DRIVER_VERSION': get_nvidia_driver_version()}
        volume_mapping[working_dir] = {'bind': '/mnt/gigantum', 'mode': 'rw'}

    volume_mapping['/var/run/docker.sock'] = {'bind': '/var/run/docker.sock', 'mode': 'rw'}

    container = docker_obj.client.containers.run(image=image_name_with_tag,
                                                 detach=True,
                                                 name=image_name.replace("/", "."),
                                                 init=True,
                                                 ports=port_mapping,
                                                 volumes=volume_mapping,
                                                 environment=environment_mapping)
    print("Starting, please wait...")
    time.sleep(1)

    # Make sure volumes have mounted properly, by checking for the log file for up to timeout seconds
    success = False
    for _ in range(timeout):
        if os.path.exists(os.path.join(working_dir, '.labmanager', 'logs', 'labmanager.log')):
            success = True
            break

        # Sleep for 1 sec and increment counter
        time.sleep(1)

    if not success:
        msg = "\n\nWorking directory failed to mount! Have you granted Docker access to your user directory?"
        msg = msg + " \nIn both Docker for Mac and Docker for Windows this should be shared by default, but may require"
        msg = msg + " a confirmation from the user."
        msg = msg + "\n\nRun `gigantum stop`, verify your OS and Docker versions are supported, the allowed Docker"
        msg = msg + " volume share locations include `{}`, and try again.".format(working_dir)
        msg = msg + "\n\nIf this problem persists, contact support."

        # Stop and remove the container
        container.stop()
        container.remove()

        click.echo(msg, err=True)
        raise click.Abort()

    # Wait for API to be live before opening the user's browser
    if not _check_for_api(port=port, launch_browser=True, timeout=timeout):
        msg = "\n\nTimed out waiting for Gigantum Client web API! Try restarting Docker and then start again." + \
                "\nOr, increase timeout with --wait option (default is 90 seconds)."

        # Stop and remove the container
        container.stop()
        container.remove()

        click.echo(msg, err=True)
        raise click.Abort()

    if external:
        click.echo("Client running on http://0.0.0.0:{}".format(port))
    else:
        click.echo("Client running on http://localhost:{}".format(port))

