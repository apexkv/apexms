from .tool import tool, click


@tool.command(name="build", help="Build the project from apexms.config.yaml configuration file")
def build():
    click.echo("Project build")


tool.add_command(build)