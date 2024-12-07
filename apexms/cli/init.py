import os
import re
import yaml
from .tool import tool, click
from apexms.handlers.project import init as init_project


@tool.command(name="init", help="Initialize a new project")
@click.argument("project_name", required=True)
@click.option("--name", "-n", help="Name of the project")
@click.option("--description", "-d", help="Description of the project")
@click.option("--path", "-p", help="Path to the project", default=os.getcwd())
def init(project_name, name, description, path):
    init_project(project_name, name, description, path, click.echo)


tool.add_command(init)