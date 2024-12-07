from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, RootModel, model_validator


class Metadata(BaseModel):
    version: str | float | int | None
    project: str
    description: Optional[str] = None
    path: Optional[str] = None


class Service(BaseModel):
    name: Optional[str] = None
    framework: Literal['django', 'flask', 'fastapi']
    port: int
    databases: Optional[List[str]] = []
    database_list: Dict[str, 'Database'] = {}
    networks: Optional[List[str]] = []
    environments: Optional[List[str]] = []
    environment: Optional[List[str]] = []
    repository: Dict[str, 'Repository'] = {}

    # update service data
    def update(self, service_data:Dict):
        for key, value in service_data.items():
            setattr(self, key, value)


class Database(BaseModel):
    name: Optional[str] = None
    type: Literal['mysql', 'postgresql']
    image: Optional[str] = None
    ports: List[str]
    volumes: Optional[List[str]] = []
    networks: Optional[List[str]] = []
    environments: Optional[List[str]] = []
    environment: Optional[List[str]] = []

    # set default image if not available
    @model_validator(mode="after")
    def set_default_image(self) -> 'Database':
        """
        Set default image for database if not available.
        """

        if self.image is None:
            if self.type == 'mysql':
                self.image = 'mysql:8.4'
            elif self.type == 'postgresql':
                self.image = 'postgres:17'

        return self


class Repository(BaseModel):
    remoteurl: str
    mainbranch: Optional[str] = 'main'
    initbranches: Optional[List[str]] = None


class Git(BaseModel):
    repositories: Optional[Dict[str, Repository]] = {}
    fullproject: Optional[Repository] = {}


class Configuration(BaseModel):
    metadata: Metadata
    environments: Optional[Dict[str, List[str]]] = None
    services: Dict[str, Service]
    databases: Dict[str, Database]
    networks: Optional[List[str]] = []
    volumes: Optional[List[str]] = []
    git: Optional[Git] = None

    @model_validator(mode="after")
    def merge_envs(self) -> 'Configuration':
        """
        Merge all environments from services, databases, and the global environments.
        """

        # Merge environments from services
        for service in self.services.values():
            service_env = service.environment if service.environment else []
            for key, env_list in self.environments.items():
                if service.environments and key in service.environments:
                    service_env += env_list
            
            service_env = list(set(service_env))
            service_env.sort()
            service.environments = service_env

        # Merge environments from databases
        for database in self.databases.values():
            db_env = database.environment if database.environment else []
            for key, env_list in self.environments.items():
                if database.environments and key in database.environments:
                    db_env += env_list
            
            db_env = list(set(db_env))
            db_env.sort()
            database.environments = db_env

        return self
    
    # merge if git available and fullproject is not available
    @model_validator(mode="after")
    def merge_git(self) -> 'Configuration':
        """
        Merge all repositories from git to services and databases.
        """

        if self.git is not None and self.git.fullproject is not None:
            for name, service in self.services.items():
                if self.git.repositories and name in self.git.repositories:
                    service.repository = self.git.repositories[name]

        return self
    
    # merge if databases available in services
    @model_validator(mode="after")
    def merge_databases(self) -> 'Configuration':
        """
        Merge all databases from services to databases.
        """

        for service_name, service in self.services.items():
            database_list:Dict[str, Database] = {}
            for db_name, database in self.databases.items():
                if service.databases and db_name in service.databases:
                    database_list[db_name] = database

            for db_name in service.databases if service.databases else []:
                if db_name not in database_list:
                    new_db_name = f"{service_name}-{db_name}"
                    if db_name == "mysql":
                        new_database = Database(name=new_db_name, type='mysql', ports=[f'3306:3306'])
                        database_list[new_db_name] = new_database
                        self.databases[new_db_name] = new_database

                    elif db_name == "postgresql":
                        new_database = Database(name=new_db_name, type='postgresql', ports=[f'5432:5432'])
                        database_list[new_db_name] = new_database
                        self.databases[new_db_name] = new_database

            service.database_list = database_list

        return self

    # Add new service if given service name not available. and validate is port available or not.
    def add_service(self, name:str, service_data:Dict):
        if name not in self.services:
            new_service = Service(**service_data)
            is_port_available = False
            
            for service in self.services.values():
                if new_service.port == service.port:
                    is_port_available = True
                    break
            
            new_service.port += 10 if is_port_available else 0
            self.services[name] = new_service


    # Add new database if given database name not available.
    def add_database(self, name:str, database_data:Dict):
        if name not in self.databases:
            self.databases[name] = Database(**database_data)

    # Add environment to global environments.
    def add_environment(self, name:str, env_list:List[str], service:str=None, database:str=None):
        if name not in self.environments:
            self.environments[name] = env_list

        if service:
            if service not in self.services:
                raise ValueError(f"Service {service} not found in services list")

            if name not in self.services[service].environments:
                self.services[service].environments.append(name)
        
        if database:
            if database not in self.databases:
                raise ValueError(f"Database {database} not found in databases list")
            
            if name not in self.databases[database].environments:
                self.databases[database].environments.append(name)

    # add volume to global volumes
    def add_volume(self, name:str):
        if name not in self.volumes:
            self.volumes.append(name)