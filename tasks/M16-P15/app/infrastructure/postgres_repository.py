from app.domain.entities import Order
from app.infrastructure.database import get_connection


class PostgresOrderRepository:
    def get_by_id(self, id: int) -> Order|None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                result = cursor.execute("SELECT * FROM orders WHERE id = %s", (id,)).fetchone()

                if not result:
                    return None

                return Order(**result)


    def get(self) -> list[Order]:
        with get_connection() as connection:
            rows = connection.execute("SELECT * FROM orders ORDER BY id ASC").fetchall()

        return [Order(**row) for row in rows]


    def create(self, order: dict) -> None:
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO orders (id, title, status, price, currency) VALUES (%s, %s, %s, %s, %s)",
                (order['id'], order['title'], 'created', order['price'], order['currency']),
            )
