import click

from gigantumcli.commands.install import install
from gigantumcli.commands.update import update
from gigantumcli.commands.start import start
from gigantumcli.commands.stop import stop
from gigantumcli.commands.feedback import feedback
from gigantumcli.commands.server import server
from gigantumcli.commands.config import config

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(help="A Command Line Interface to manage the Gigantum Client.", context_settings=CONTEXT_SETTINGS)
def cli():
    pass


# Add commands from package
cli.add_command(install)
cli.add_command(update)
cli.add_command(start)
cli.add_command(stop)
cli.add_command(feedback)
cli.add_command(server)
cli.add_command(config)


# Deprecated commands
@cli.command('add-server', hidden=True)
def add_server():
    raise click.UsageError("`gigantum add-server` has been deprecated. Did you mean `gigantum server add`?")


@cli.command('list-servers', hidden=True)
def list_servers():
    raise click.UsageError("`gigantum list-servers` has been deprecated. Did you mean `gigantum server list`?")
# Deprecated commands


if __name__ == '__main__':
    cli()
