from .tool import tool, click


@tool.command()
def build():
    click.echo("Project build")


tool.add_command(build)