from typing import Optional

from pydantic import BaseModel, Field


class CarCreate(BaseModel):
    brand: str
    model: str
    year: int = Field(ge=1886)
    owner_id: Optional[int] = None


class CarUpdate(BaseModel):
    brand: str
    model: str
    year: int = Field(ge=1886)
    owner_id: Optional[int] = None


class CarRead(BaseModel):
    id: int
    brand: str
    model: str
    year: int
    owner_id: Optional[int] = None
