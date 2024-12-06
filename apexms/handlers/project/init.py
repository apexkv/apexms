import re
import os
import yaml


def init(project_name, name, description, path="."):
    config_path = os.path.join(os.getcwd(), "apexms.config.yaml")
    
    if not name:
        name = project_name

    # name must only have letters, numbers, underscores and hyphens
    if not re.match(r"^[a-zA-Z0-9_-]*$", name):
        return ["\nProject name must only have [a-zA-Z0-9_-]\n"]

    # abs path to the project
    abs_path = os.path.abspath(str(path))

    if not os.path.exists(abs_path):
        os.makedirs(abs_path)

    if path:
        config_path = os.path.join(abs_path, "apexms.config.yaml")


    if not description:
        description = f"Project: {name} created with ApexMS"

    # Check if project already initialized
    if os.path.exists(config_path):
        return ["\nProject already initialized\n"]
    
    # Create config file
    config = {
        "metadata":{
            "project": name,
            "version": "1.0.0",
            "description": description,
        },
        "environments":{},
        "services":{},
        "databases":{},
        "networks":["private-network", "public-network"],
        "volumes":{},
        "git":{
            "fullproject":{
                "remoteurl": "",
                "mainbranch": "main",
                "initbranches": ["develop", "feature", "bugfix", "hotfix"],
            }
        },
    }

    config_yaml = yaml.dump(config, indent=4, default_flow_style=False, sort_keys=False)

    # Insert blank lines between top-level keys
    main_keys = list(config.keys())
    for key in reversed(main_keys):
        config_yaml = config_yaml.replace(f"{key}:", f"\n{key}:")

    config_yaml = config_yaml.replace("{}", "")

    with open(config_path, "w") as f:
        f.write(f"# ApexMS Configuration for project: {name}\n")
        f.write(config_yaml)

    return [
        f"\nProject initialized: {name}",
        f"Config Path: {config_path}\n",
    ]