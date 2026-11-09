from dataclasses import dataclass, field
from typing import Literal
from uuid import UUID, uuid4


@dataclass
class Message:
    text: str
    role: Literal["user", "assistant"]
    id: UUID = field(default_factory=uuid4)
