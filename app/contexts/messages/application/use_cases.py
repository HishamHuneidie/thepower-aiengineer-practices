from typing import Dict

from app.contexts.messages.domain.repositories import MessageRepositoryInterface


class ListMessages:
    def __init__(self, repository: MessageRepositoryInterface):
        self.repository = repository

    def execute(self):
        return self.repository.list()


class GetMessage:
    def __init__(self, repository: MessageRepositoryInterface):
        self.repository = repository

    def execute(self, message_id: int):
        return self.repository.get(message_id)


class CreateMessage:
    def __init__(self, repository: MessageRepositoryInterface):
        self.repository = repository

    def execute(self, data: Dict):
        return self.repository.create(data)


class UpdateMessage:
    def __init__(self, repository: MessageRepositoryInterface):
        self.repository = repository

    def execute(self, message_id: int, data: Dict):
        return self.repository.update(message_id, data)


class DeleteMessage:
    def __init__(self, repository: MessageRepositoryInterface):
        self.repository = repository

    def execute(self, message_id: int):
        return self.repository.delete(message_id)
