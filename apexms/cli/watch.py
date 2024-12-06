import os
import yaml
from .tool import tool, click


@tool.command(name="watch", help="Live watch the configuration file for changes and re-run the project")
@click.option("--path", "-p", help="Path to the configuration file")
def watch(watch):
    click.echo("Watching configuration file for changes...")


tool.add_command(watch)