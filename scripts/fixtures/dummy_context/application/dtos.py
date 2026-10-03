from typing import Optional

from pydantic import BaseModel, Field


class {EntityName}Create(BaseModel):
    property_name: str


class {EntityName}Update(BaseModel):
    property_name: str


class {EntityName}Read(BaseModel):
    id: int
    property_name: str
