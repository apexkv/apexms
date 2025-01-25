from pydantic import BaseModel
import yaml


class Metadata(BaseModel):
    version: str
    project: str
    description: str
    path: str


class Config(BaseModel):
    metadata: Metadata


file = open("apexms.config.yaml", "r")
data = yaml.safe_load(file)

print(data["metadata"])

config = Config(**data)
print(config.metadata.version)
