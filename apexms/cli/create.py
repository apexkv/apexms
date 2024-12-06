from .tool import tool, click


@tool.command()
def create():
    click.echo("Project created")


tool.add_command(create)