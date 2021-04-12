import click

from gigantumcli.utilities import ask_question
from gigantumcli.server import ServerConfig


@click.group(help="Manage server connections for this Client instance.")
def server():
    pass


@server.command()
@click.argument('url', type=str, nargs=1)
@click.option('--working-dir', '-d', 'working_dir', type=str, default="~/gigantum",
              help="Set the Client working directory (`~/gigantum`).")
def add(url: str, working_dir: str = "~/gigantum"):
    """Add a server to this Client.

    Enter the URL for the server you wish to add to this Client (e.g. https://gigantum.mycompany.com). If the
    server uses self-signed certificates you will be prompted before the server is added. Once added, you can
    log into the server to sync Projects and Datasets.

    \f

    Args:
        url(str): URL to the server
        working_dir(str): Working dir for the client

    Returns:
        None
    """
    server_config = ServerConfig(working_dir=working_dir)
    server_config.add_server(url)
    click.echo("\nServer successfully added. The server will now be available on your Client login page.")


@server.command('list')
@click.option('--working-dir', '-d', 'working_dir', type=str, default="~/gigantum",
              help="Set the Client working directory (`~/gigantum`).")
def list_server(working_dir: str = "~/gigantum"):
    """List configured servers.

    This command will list all servers currently available to this Client.

    \f

    Args:
        working_dir(str): Working dir for the client

    Returns:
        None
    """
    server_config = ServerConfig(working_dir=working_dir)
    server_config.list_servers(should_print=True)


@server.command()
@click.argument('server_id', metavar='ID', type=str, nargs=1)
@click.option('--working-dir', '-d', 'working_dir', type=str, default="~/gigantum",
              help="Set the Client working directory (`~/gigantum`).")
@click.option('--yes', '-y', 'accept_confirmation', type=str, is_flag=True, default=False,
              help="Flag to automatically accept all confirmation prompts")
def remove(server_id: str, working_dir: str = "~/gigantum", accept_confirmation: bool = False) -> None:
    """Remove a server with ID from this Client.

    This command will remove the server with the provided server ID from this
    Client. All data related to this server will be removed locally.
    \f

    Args:
        server_id(str): server ID to remove. Run `gigantum server list` to see all IDs
        working_dir(str): Working dir for the client
        accept_confirmation(bool): Optional Flag indicating if you should skip the confirmation and auto-accept

    Returns:
        None
    """
    server_config = ServerConfig(working_dir=working_dir)
    servers = server_config.list_servers()

    # Make sure the ID exists
    match = [s for s in servers if s[0] == server_id]
    if not match:
        msg = "ID `{}` does not exist. Verify the correct server ID has been provided ".format(server_id) +  \
              "by running `gigantum server list`."
        raise click.UsageError(msg)

    # Verify that they really want to do this
    click.echo()
    click.secho('********* DANGER *********', bg='red', fg='white', bold=True)
    click.echo()
    click.echo("Removing the server `{}` will delete ALL data locally.".format(match[0][1]))
    click.echo("Any changes that have not been synced to the server will be lost!")
    click.echo()
    click.secho('********* DANGER *********', bg='red', fg='white', bold=True)
    click.echo()
    if ask_question("Do you want to proceed?", accept_confirmation):
        # Remove server and make sure CURRENT is set to something valid
        server_config.remove_server(server_id)
    else:
        click.echo("Server remove cancelled.")
        return
