import yaml


def load_yaml(config_file_path:str)->dict:
    # load config file
    with open(config_file_path, "r") as file:
        config_file = yaml.load(file, Loader=yaml.FullLoader)
        if not config_file["environments"]:
            config_file["environments"] = {}
        
        if not config_file["services"]:
            config_file["services"] = {}

        if not config_file["databases"]:
            config_file["databases"] = {}

        if not config_file["networks"]:
            config_file["networks"] = []
        
        if not config_file["volumes"]:
            config_file["volumes"] = []

        if not config_file["git"]:
            config_file["git"] = {
                "repositories": {},
                "fullproject":{
                    "remoteurl": "",
                    "mainbranch": "main",
                    "initbranches": ["develop", "feature", "bugfix", "hotfix"],
                }
            }
        else:
            if "repositories" not in config_file["git"] and "fullproject" not in config_file["git"]:
                config_file["git"]["repositories"] = {}
                config_file["git"]["fullproject"] = {
                    "remoteurl": "",
                    "mainbranch": "main",
                    "initbranches": ["develop", "feature", "bugfix", "hotfix"],
                }        

    return config_file
    
def save_yaml(name:str, config_file_path:str, config_file:dict):
    config_yaml = yaml.dump(config_file, indent=4, default_flow_style=False, sort_keys=False)

    config_yaml = config_yaml.replace("{}", "").replace("[]", "")

    with open(config_file_path, "w") as f:
        f.write(f"# ApexMS Configuration for project: {name}\n")
        f.write(config_yaml)


def generate_password(length:int)->str:
    import random
    import string

    password = ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    return password