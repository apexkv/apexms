from .generator import GenerateDockerCompose, GenerateService
from typing import Dict, List, TypedDict, Union, Literal
from pydantic import BaseModel
import yaml
import json
import os


def get_environments(envList: List[str]):
    environments:List[str] = []
    for key in envList:
        envs = Environments.get(key)
        environments.extend(envs)
    return environments


class MetadataType(TypedDict):
    version: str | float | int | None
    project: str
    description: str | None


class Metadata:
    data: MetadataType = {}
    def __init__(self, metadata: MetadataType):        
        self.project = metadata['project']
        self.version = metadata.get('version', '1.0.0')
        self.description = metadata.get('description', None)
        self.data.update(metadata)


class Environments:
    environments: Dict[str, List[str]] = {}

    def __init__(self, envs: Dict[str, List[str]]):
        self.environments.update(envs)

    @classmethod
    def get(cls, name):
        envs = cls.environments.get(name, [])
        if len(envs) == 0:
            raise ValueError(f"Environments {name} not found")
        return envs


class Networks:
    networks_list: List[str] = []

    def __init__(self, networks: List[str]):
        if len(networks) == 0:
            # default networks
            PUBLIC_NETWORK = 'public-network'
            PRIVATE_NETWORK = 'private-network'
            self.networks = [PUBLIC_NETWORK, PRIVATE_NETWORK]

        self.networks = networks
        for network in networks:
            self.add(network)

    @classmethod
    def add(cls, network: str):
        if network not in cls.networks_list:
            cls.networks_list.append(network)


class Volumes:
    volumes_list: List[str] = []

    def __init__(self, volumes: List[str]):
        self.volumes = volumes
        self.volumes_list.extend(volumes)

    @classmethod
    def add(cls, volume: str):
        if volume not in cls.volumes_list:
            cls.volumes_list.append(volume)


class DatabaseType(TypedDict):
    type: Literal['mysql', 'postgresql']
    image: str
    ports: List[str]
    environments: List[str] | None
    environment: List[str] | None
    volumes: List[str] | None
    networks: List[str] | None


class Database:
    database_list: Dict[str, 'Database'] = {}
    def __init__(self, name: str, database: DatabaseType):
        self.name = name
        self.type = database['type']
        self.ports = database['ports']
        databases_images = {
            'mysql': 'mysql:8.4',
            'postgresql': 'postgres:17',
        }
        self.image = database.get('image', databases_images[self.type])
        # environments key:value list
        self.environments = get_environments(database.get('environments', []))
        self.environments.extend(database.get("environment", []))
        self.volumes = self.__get_default_volumes__(database.get('volumes', []))
        self.networks = Networks(database.get('networks', [])).networks
        self.database_list[name] = self

    def __get_default_volumes__(self, volumes: List[str]):
        if len(volumes) == 0:
            # default volumes
            VOLUME_NAME = f"{self.name}-volume"
            Volumes.add(VOLUME_NAME)

            if self.type == "mysql":
                database_volume = f"{VOLUME_NAME}:/var/lib/mysql"
            elif self.type == "postgresql":
                database_volume = f"{VOLUME_NAME}:/var/lib/postgresql/data"

            return [database_volume]
        return volumes
    
    @classmethod
    def get(cls, name):
        return cls.database_list.get(name, None)


class ServiseType(TypedDict):
    framework: Literal['django', 'flask', 'fastapi']
    port: int
    name: str | None
    environments: List[str] | None
    environment: List[str] | None
    databases: List[str] | None
    networks: List[str] | None
    cache: List[str] | None
    messagebrokers: List[str] | None
    dependon: List[str] | None


class Service:
    services_list: Dict[str, 'Service'] = {}

    def __init__(self, name: str, service: ServiseType):        
        self.name = name
        self.framework: Literal['django', 'flask', 'fastapi'] = service['framework']
        self.port: str | int = service['port']
        # environments key:value list
        self.environments = get_environments(service.get('environments', []))
        self.environments.extend(service.get("environment", []))
        self.image = f"python:3.11.9"
        entrypoints = {
            'django': 'manage.py runserver',
            'flask': 'app.py',
            'fastapi': 'app.py',
        }
        self.entrypoint = entrypoints[self.framework]

        self.networks = list(Networks(service.get('networks', None)).networks)
        self.volumes = service.get('volumes', [])
        self.databases = list(self.__databases__(service.get('databases', [])).keys())
        self.cache = service.get('cache', None)
        self.messagebrokers = service.get('messagebrokers', None)
        self.dependon = service.get('dependon', None)
        self.services_list[name] = self

        self.requirements = self.__set_requirements__()
    
    def __databases__(self, databases: List[str]):
        db_list = {}
        for db in databases:
            db_obj = Database.get(db)
            if db_obj:
                db_list[db] = db_obj
            else:
                db_name = f"{self.name}-db"
                db_network = f"{db_name}-network"

                if db == "mysql":
                    Networks.add(db_network)
                    new_db = Database(db_name, {
                        "type": "mysql",
                        "ports": ["3306:3306"],
                        "environment": [   
                            f"MYSQL_DATABASE={db_name}",
                            f"MYSQL_USER={self.name}-user",
                            "MYSQL_PASSWORD=o4$DR40Hou@YF30o1S!vP",
                            f"MYSQL_HOST={db_name}",
                            "MYSQL_ROOT_PASSWORD=LK4SI2O9@clmsDB4$DR40H",
                        ],
                        "volumes": [],
                        "networks": [db_network]
                    })
                    db_list[db_name] = new_db
                    self.networks.append(db_network)
                    
                elif db == "postgresql":
                    Networks.add(db_network)
                    new_db = Database(db_name, {
                        "type": "postgresql",
                        "ports": ["5432:5432"],
                        "environment": [
                            f"POSTGRES_DB={db_name}",
                            f"POSTGRES_USER={self.name}-user",
                            "POSTGRES_PASSWORD=o4$DR40Hou@YF30o1S!vP",
                            f"POSTGRES_HOST={db_name}",
                            "POSTGRES_ROOT_PASSWORD=LK4SI2O9@clmsDB4$DR40H",
                        ],
                        "volumes": [],
                        "networks": [db_network]
                    })
                    db_list[db_name] = new_db
                    self.networks.append(db_network)
        return db_list
    
    def __set_requirements__(self):
        req = []
        if self.framework == "django":
            req = [
                "asgiref==3.8.1",
                "Django==5.1.3",
                "sqlparse==0.5.2",
            ]
        elif self.framework == "flask":
            req = [
                "blinker==1.9.0",
                "click==8.1.7",
                "Flask==3.1.0",
                "itsdangerous==2.2.0",
                "Jinja2==3.1.4",
                "MarkupSafe==3.0.2",
                "Werkzeug==3.1.3",
            ]
        elif self.framework == "fastapi":
            req = [
                "annotated-types==0.7.0",
                "anyio==4.6.2.post1",
                "certifi==2024.8.30",
                "click==8.1.7",
                "dnspython==2.7.0",
                "email_validator==2.2.0",
                "fastapi==0.115.5",
                "fastapi-cli==0.0.5",
                "h11==0.14.0",
                "httpcore==1.0.7",
                "httptools==0.6.4",
                "httpx==0.28.0",
                "idna==3.10",
                "Jinja2==3.1.4",
                "markdown-it-py==3.0.0",
                "MarkupSafe==3.0.2",
                "mdurl==0.1.2",
                "pydantic==2.10.2",
                "pydantic_core==2.27.1",
                "Pygments==2.18.0",
                "python-dotenv==1.0.1",
                "python-multipart==0.0.19",
                "PyYAML==6.0.2",
                "rich==13.9.4",
                "shellingham==1.5.4",
                "sniffio==1.3.1",
                "starlette==0.41.3",
                "typer==0.14.0",
                "typing_extensions==4.12.2",
                "uvicorn==0.32.1",
                "uvloop==0.21.0",
                "watchfiles==1.0.0",
                "websockets==14.1",
            ]
        return req

    def get(self, name:str):
        return self.services_list.get(name, None)
    
    def generate(self, path: str):
        path = os.path.join(path, self.name)
        os.makedirs(path, exist_ok=True)
    

        


class ConfigurationType(TypedDict):
    metadata: MetadataType
    services: Dict[str, ServiseType]
    environments: Dict[str, List[str]]
    databases: Dict[str, DatabaseType]
    networks: List[str]
    volumes: List[str]


class Configuration:
    data: 'Configuration' = None
    def __init__(self, config: ConfigurationType):        
        self.metadata = Metadata(config['metadata'])
        self.environments = Environments(config['environments'])
        self.networks = Networks(config.get('networks', []))
        self.volumes = Volumes(config.get('volumes', []))
        self.databases = {name: Database(name, database) for name, database in config.get("databases", {}).items()}
        self.services = {name: Service(name, service) for name, service in config.get("services", {}).items()}
        self.data = self

    def generate(self, path: str):
        for service in self.services.values():
            generator = GenerateService(service, path)
            generator.generate()

        GenerateDockerCompose(self, path)