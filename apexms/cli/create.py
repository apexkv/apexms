import os
from .tool import tool, click
from apexms.handlers.project import create as create_project


# services list structure is microservice_name:framework or can extend with - for connect datbase to that microservice database_name:database_type
@tool.command(name="create", help="Create new microservices with a list of services")
@click.argument("services", nargs=-1, required=True)
@click.option("--databases", "-db", help="List of databases to connect with microservices", multiple=True)
@click.option("--path", "-p", help="Path to config file", default=os.getcwd())
def create(services, databases:tuple, path:str):
    path = os.path.join(os.path.abspath(path), "apexms.config.yaml")

    db = []
    for database in databases:
        db.extend(database.split(" "))
    create_project(services, db, path, click.echo)    


tool.add_command(create)