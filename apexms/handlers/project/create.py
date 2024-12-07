import os
import json
from typing import List
import yaml
from apexms.config.parsers import Configuration as ConfigParser
from apexms.utils.tools import generate_password, load_yaml, save_yaml


def create(services:List[str], databases:List[str], path:str, echo):
    config_file_path = os.path.abspath(path)
    config_file = load_yaml(config_file_path)

    config = ConfigParser(**config_file)

    env_list = []
    volume_list = []

    echo()

    for database in databases:
        db_name, db_type = database.split(":")
        db_obj = {
            "name": db_name,
            "type": db_type,
            "networks": [
                "private-network",
            ],
            "volumes": []
        }
        volume_list.append(f"{db_name}-volume")

        db_env = {
                "name": f"{db_name}-env",
                "variables": [],
                "database": db_name,
                "service": None
            }

        if db_type == "mysql":
            db_obj["ports"] = ["3306:3306"]

            db_env["variables"] = [
                f"MYSQL_DATABASE={db_name}db",
                f"MYSQL_USER={db_name}-user",
                f"MYSQL_PASSWORD={generate_password(8)}",
                f"MYSQL_ROOT_PASSWORD={generate_password(8)}",
                "MYSQL_PORT=3306",
            ]    

            db_obj["volumes"].append(f"{db_name}-volume:/var/lib/mysql")
            env_list.append(db_env)

        elif db_type == "postgresql":
            db_obj["ports"] = ["5432:5432"]
            
            db_env["variables"] = [
                f"POSTGRES_DB={db_name}db",
                f"POSTGRES_USER={db_name}-user",
                f"POSTGRES_PASSWORD={generate_password(12)}",
                f"POSTGRES_HOST={db_name}",
                f"POSTGRES_ROOT_PASSWORD={generate_password(12)}",
                "POSTGRES_PORT=5432",
            ]

            db_obj["volumes"].append(f"{db_name}-volume:/var/lib/postgresql/data")
            env_list.append(db_env)

        config.add_database(db_name, db_obj)
        echo(f"Database {db_name} added to config")

    for service in services:
        srvice, db_name = service.split("-") if "-" in service else (service, None)
        api_name, framework = srvice.split(":")

        if db_name not in config.databases and db_name:
            raise ValueError(f"Database {db_name} not found in database list")
        
        # check database environment available in environments list if it available update environment service
        for env in env_list:
            if env["database"] == db_name:
                env["service"] = api_name

        service_obj = {
            "name": api_name,
            "framework": framework,
            "databases": [db_name] if db_name else [],
            "networks": [
                "public-network",
            ]
        }

        if framework == "flask":
            service_obj["port"] = 6000
        elif framework == "fastapi":
            service_obj["port"] = 7000
        elif framework == "django":
            service_obj["port"] = 8000

        if db_name:
            service_obj["networks"].append(f"private-network")

        config.add_service(api_name, service_obj)
        echo(f"Service {api_name} added to config")

    for env in env_list:
        config.add_environment(env["name"], env["variables"], env["service"], env["database"])

    for volume in volume_list:
        config.add_volume(volume)

    config_data = config.model_dump()
    for service in config_data["services"]:
        # need to remove database_list key from every service in services dict
        if "database_list" in config_data["services"][service]:
            del config_data["services"][service]["database_list"]
        # remove repository key from service
        if "repository" in config_data["services"][service]:
            del config_data["services"][service]["repository"]
        
    save_yaml(config_file["metadata"]["project"], config_file_path, config_data)
    echo(f"\nConfig file updated.\nPath: {config_file_path}")
    
