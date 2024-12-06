import os
import re
import yaml
from .tool import tool, click
from apexms.handlers.project.init import init as init_handler


@tool.command(name="init")
@click.argument("project_name", required=True)
@click.option("--name", "-n", help="Name of the project")
@click.option("--description", "-d", help="Description of the project")
@click.option("--path", "-p", help="Path to the project")
def init(project_name, name, description, path):
    msgs = init_handler(project_name, name, description, path)

    for msg in msgs:
        click.echo(msg)


tool.add_command(init)