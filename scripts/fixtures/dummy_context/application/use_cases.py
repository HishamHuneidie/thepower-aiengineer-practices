from typing import Dict

from app.contexts.{entity_plural_name}.domain.repositories import {EntityName}RepositoryInterface


class List{EntityPluralName}:
    def __init__(self, repository: {EntityName}RepositoryInterface):
        self.repository = repository

    def execute(self):
        return self.repository.list()


class Get{EntityName}:
    def __init__(self, repository: {EntityName}RepositoryInterface):
        self.repository = repository

    def execute(self, {entity_name}_id: int):
        return self.repository.get({entity_name}_id)


class Create{EntityName}:
    def __init__(self, repository: {EntityName}RepositoryInterface):
        self.repository = repository

    def execute(self, data: Dict):
        return self.repository.create(data)


class Update{EntityName}:
    def __init__(self, repository: {EntityName}RepositoryInterface):
        self.repository = repository

    def execute(self, {entity_name}_id: int, data: Dict):
        return self.repository.update({entity_name}_id, data)


class Delete{EntityName}:
    def __init__(self, repository: {EntityName}RepositoryInterface):
        self.repository = repository

    def execute(self, {entity_name}_id: int):
        return self.repository.delete({entity_name}_id)
