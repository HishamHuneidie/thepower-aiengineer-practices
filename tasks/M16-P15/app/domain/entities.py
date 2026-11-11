from dataclasses import dataclass
from typing import Literal


@dataclass
class Order:
    id: int
    title: str
    status: Literal["created", "updated", "deleted"]
    price: float
    currency: Literal["EUR", "USD"]