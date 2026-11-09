from typing import Protocol

from app.domain.entities import Message


class MessageRepository(Protocol):
    def save(self, messages: list[Message]) -> None: ...

    def list_all(self) -> list[Message]: ...
