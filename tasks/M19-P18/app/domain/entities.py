from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class Message:
    id: UUID = field(default_factory=uuid4)
    text: str | None = None
