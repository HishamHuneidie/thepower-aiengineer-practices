from typing import Dict

from app.contexts.users.domain.repositories import UserRepository


class ListUsers:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self):
        return self.repository.list()


class GetUser:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, user_id: int):
        return self.repository.get(user_id)


class CreateUser:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, data: Dict):
        return self.repository.create(data)


class UpdateUser:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, user_id: int, data: Dict):
        return self.repository.update(user_id, data)


class DeleteUser:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, user_id: int):
        return self.repository.delete(user_id)
