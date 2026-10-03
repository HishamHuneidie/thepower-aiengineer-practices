from typing import Dict

from app.contexts.cars.domain.repositories import CarRepository


class ListCars:
    def __init__(self, repository: CarRepository):
        self.repository = repository

    def execute(self):
        return self.repository.list()


class GetCar:
    def __init__(self, repository: CarRepository):
        self.repository = repository

    def execute(self, car_id: int):
        return self.repository.get(car_id)


class CreateCar:
    def __init__(self, repository: CarRepository):
        self.repository = repository

    def execute(self, data: Dict):
        return self.repository.create(data)


class UpdateCar:
    def __init__(self, repository: CarRepository):
        self.repository = repository

    def execute(self, car_id: int, data: Dict):
        return self.repository.update(car_id, data)


class DeleteCar:
    def __init__(self, repository: CarRepository):
        self.repository = repository

    def execute(self, car_id: int):
        return self.repository.delete(car_id)
