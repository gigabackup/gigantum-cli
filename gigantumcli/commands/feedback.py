import webbrowser
import click


@click.command()
def feedback():
    """Open the default web browser to provide feedback.

    /f
    Returns:
        None
    """
    feedback_url = "https://feedback.gigantum.com"
    click.echo("You can provide feedback here: {}".format(feedback_url))
    webbrowser.open_new(feedback_url)
