from docker.errors import APIError, ImageNotFound

import click

from gigantumcli.dockerinterface import DockerInterface
from gigantumcli.changelog import ChangeLog
from gigantumcli.utilities import is_running_as_admin


@click.command()
@click.option('--edge', '-e', type=bool, is_flag=True, default=False,
              help="Optional flag indicating if the edge version should be used. Note, you must have access "
                   "to this image and may need to log into DockerHub.")
def install(edge: bool):
    """Install the Gigantum Client Docker Image.

    This command will pull and configure the Gigantum Client Docker Image for the first time. The
    process can take a few minutes depending on your internet speed.
    \f

    Args:
        edge(bool): Flag indicating if the install is stable or edge
    """
    # Make sure user is not root
    if is_running_as_admin():
        raise click.UsageError("Do not run `gigantum install` as root.")

    docker_obj = DockerInterface()
    image_name = docker_obj.image_name(edge)
    try:
        try:
            # Check to see if the image has already been pulled
            docker_obj.client.images.get(image_name)
            raise click.UsageError("Gigantum Client image already installed. Run `gigantum update` instead.")

        except ImageNotFound:
            # Pull for the first time
            print("\nDownloading and installing the Gigantum Client Docker Image. Please wait...\n")
            cl = ChangeLog()
            tag = cl.latest_tag()
            image = docker_obj.client.images.pull(image_name, tag)
            docker_obj.client.api.tag('{}:{}'.format(image_name, tag), image_name, 'latest')

    except APIError:
        click.echo("Failed to pull image! Verify your internet connection and try again.", err=True)
        raise click.Abort()

    short_id = image.short_id.split(':')[1]
    print("\nSuccessfully pulled {}:{}\n".format(image_name, short_id))
