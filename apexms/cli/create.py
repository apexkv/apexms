from .tool import tool, click


@tool.command(name="create", help="Create a new microservices")
def create():
    click.echo("Project created")


tool.add_command(create)