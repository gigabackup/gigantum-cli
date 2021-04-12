import sys
from docker.errors import APIError, ImageNotFound
import click

from gigantumcli.dockerinterface import DockerInterface
from gigantumcli.changelog import ChangeLog
from gigantumcli.utilities import ask_question, is_running_as_admin


@click.command()
@click.option('--edge', '-e', type=bool, is_flag=True, default=False,
              help="Flag indicating if the edge version should be used. Note, you must have access "
                   "to this image and may need to log into DockerHub.")
@click.option('--tag', '-t', type=str, default=None,
              help="Provide a tag to explicitly override the latest image tag when updating")
@click.option('--yes', '-y', 'accept_confirmation', type=str, is_flag=True, default=False,
              help="Flag to automatically accept all confirmation prompts")
def update(edge: bool, tag=None, accept_confirmation=False):
    """Check if an update is available for Gigantum Client.

    This command will check if an update is available and display the latest changelog before
    prompting for confirmation. If you proceed, the new Gigantum Client image will be pulled. The
    process can take a few minutes depending on your internet speed.
    \f

    Args:
        edge(bool): Flag indicating if the install is stable or edge
        tag(str): Tag to pull if you wish to override `latest`
        accept_confirmation(bool): Optional Flag indicating if you should skip the confirmation and auto-accept

    Returns:
        None
    """
    # Make sure user is not root
    if is_running_as_admin():
        click.echo("Do not run `gigantum install` as root.", err=True)
        return

    docker_obj = DockerInterface()
    image_name = docker_obj.image_name(edge)
    try:
        cl = ChangeLog()
        if not edge:
            # Normal install, so do checks
            if not tag:
                # Trying to update to the latest version
                tag = cl.latest_tag()

                # Get id of current labmanager install
                try:
                    current_image = docker_obj.client.images.get("{}:latest".format(image_name))
                except ImageNotFound:
                    click.echo("Gigantum Client image not yet installed. Run 'gigantum install' first.")
                    raise click.Abort()
                short_id = current_image.short_id.split(':')[1]

                # Check if there is an update available
                if not cl.is_update_available(short_id):
                    click.echo("Latest version already installed.")
                    sys.exit(0)

            # Get Changelog info for the latest or specified version
            try:
                click.echo(cl.get_changelog(tag))
            except ValueError as err:
                click.echo("Failed to get changelog information: {}".format(err), err=True)
                raise click.Abort()
        else:
            # Edge build, set tag if needed
            if not tag:
                # Trying to update to the latest version
                tag = "latest"

        # Make sure user wants to pull
        if ask_question("Are you sure you want to update?", accept_confirmation):
            # Pull
            click.echo("\nDownloading and installing the Gigantum Client Docker Image. Please wait...\n")
            image = docker_obj.client.images.pull(image_name, tag)

            # Tag to latest locally
            docker_obj.client.api.tag('{}:{}'.format(image_name, tag), image_name, 'latest')
        else:
            click.echo("Update cancelled.")
            raise click.Abort()
    except APIError:
        click.echo("Failed to pull image! Verify your internet connection and try again.", err=True)
        raise click.Abort()

    short_id = image.short_id.split(':')[1]
    click.echo("\nSuccessfully pulled {}:{}\n".format(image_name, short_id))
