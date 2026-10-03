from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Car:
    id: int
    brand: str
    model: str
    year: int
    owner_id: Optional[int]
