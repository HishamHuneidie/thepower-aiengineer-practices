from app.domain.entities import Order
from app.infrastructure.postgres_repository import PostgresOrderRepository


repository = PostgresOrderRepository()


def get_order(id: int) -> Order|None:
    return repository.get_by_id(id)


def get_orders() -> list[Order]:
    return repository.get()


def create_order(order: dict) -> None:
    return repository.create(order)
