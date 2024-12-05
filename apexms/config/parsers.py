from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, RootModel, model_validator


class Metadata(BaseModel):
    version: str | float | int | None
    project: str
    description: Optional[str] = None


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
    repositories: Dict[str, Repository] = {}
    fullproject: Repository = {}


class Configuration(BaseModel):
    metadata: Metadata
    environments: Optional[Dict[str, List[str]]] = None
    networks: Optional[List[str]] = []
    volumes: Optional[List[str]] = []
    databases: Dict[str, Database]
    services: Dict[str, Service]
    git: Optional[Git] = None

    @model_validator(mode="after")
    def merge_envs(self) -> 'Configuration':
        """
        Merge all environments from services, databases, and the global environments.
        """

        # Merge environments from services
        for service in self.services.values():
            service_env = service.environment
            for key, env_list in self.environments.items():
                if key in service.environments:
                    service_env += env_list
            
            service_env = list(set(service_env))
            service_env.sort()
            service.environments = service_env

        # Merge environments from databases
        for database in self.databases.values():
            db_env = database.environment
            for key, env_list in self.environments.items():
                if key in database.environments:
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
                if name in self.git.repositories:
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
                if db_name in service.databases:
                    database_list[db_name] = database

            for db_name in service.databases:
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
