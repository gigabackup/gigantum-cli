import click

from gigantumcli.dockerinterface import DockerInterface
from gigantumcli.utilities import ask_question


@click.command()
@click.option('--yes', '-y', 'accept_confirmation', type=str, is_flag=True, default=False,
              help="Flag to automatically accept all confirmation prompts")
def stop(accept_confirmation=False):
    """Stop Gigantum Client.

    This command will stop and remove all Gigantum managed containers.
    \f

    Args:
        accept_confirmation(bool): Optional Flag indicating if you should skip the confirmation and auto-accept

    Returns:
        None
    """
    docker_obj = DockerInterface()

    if ask_question("Stop all Gigantum managed containers? MAKE SURE YOU HAVE SAVED YOUR WORK FIRST!",
                    accept_confirmation):
        # remove any lingering gigantum managed containers
        docker_obj.cleanup_containers()
    else:
        click.echo("Stop command cancelled")
        return
