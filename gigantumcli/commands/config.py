import click
from gigantumcli.config import ConfigOverrideFile


@click.group(help="Manage the Client configuration file.")
def config():
    pass


@config.command()
@click.option('--working-dir', '-d', 'working_dir', type=str, default="~/gigantum",
              help="Set the Client working directory (`~/gigantum`).")
def init(working_dir: str = "~/gigantum"):
    """Initialize the Client configuration override file.

    The default Client configuration file that is embedded in the Client can be modified by
    "overriding" values based on the file located at `<working_dir>/.labmanager/config.yaml`. Typically
    this is `~/gigantum/.labmanager/config.yaml`.

    This command writes a configuration override file containing the most frequently needed fields
    with their default values.
    \f

    Args:
        working_dir(str): Working dir for the client

    Returns:
        None
    """
    config_helper = ConfigOverrideFile(working_dir)
    if config_helper.config_exists():
        click.echo("A config file already exists at `{}`. "
                   "Remove this file before trying to init".format(config_helper.config_file))
        raise click.Abort()

    config_helper.write_default_config_override()
    click.echo("Config file written to `{}` with default values.".format(config_helper.config_file))


@config.command('set-auth-mode')
@click.argument('mode', type=click.Choice(['local', 'multi-user']))
@click.option('--working-dir', '-d', 'working_dir', type=str, default="~/gigantum",
              help="Set the Client working directory (`~/gigantum`).")
def set_auth_mode(mode: str, working_dir: str = "~/gigantum"):
    """Set the authentication mode (important for running the Client publicly).

    By default the Client authorization middleware is in "local" mode. This means that
    when logging in some identity data is cached so that the Client can work when disconnected
    from the internet. If you wish to run the Client as a service for multiple users to share
    (sometimes referred to as "multi-tenant mode" in some documentation) you must select the "multi-user"
    middleware mode.
    \f

    Args:
        mode(str): Mode for the auth middleware (local, multi-user)
        working_dir(str): Working dir for the client

    Returns:
        None
    """
    # Translate from user friendly name
    if mode == 'multi-user':
        mode = 'browser'
    config_helper = ConfigOverrideFile(working_dir)
    config_helper.set_auth_middleware_mode(mode)
    click.echo("Config updated. Restart the Client to apply changes.")
