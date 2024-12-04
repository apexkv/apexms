from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, RootModel


class Metadata(BaseModel):
    version: str | float | int | None
    project: str
    description: Optional[str] = None


class Environments(RootModel):
    root: Dict[str, List[str]]


class Service(BaseModel):
    name: Optional[str] = None
    framework: Literal['django', 'flask', 'fastapi']
    port: int
    environments: Optional[List[str]] = []
    environment: Optional[List[str]] = []
    databases: Optional[List[str]] = []
    networks: Optional[List[str]] = []


class Database(BaseModel):
    name: Optional[str] = None
    type: Literal['mysql', 'postgresql']
    ports: List[str]
    environments: Optional[List[str]] = []
    environment: Optional[List[str]] = []
    volumes: Optional[List[str]] = []
    networks: Optional[List[str]] = []


class Configuration(BaseModel):
    metadata: Metadata
    environments: Optional[Environments] = None
    services: Dict[str, Service]
    databases: Dict[str, Database]
    networks: Optional[List[str]] = []
    volumes: Optional[List[str]] = []