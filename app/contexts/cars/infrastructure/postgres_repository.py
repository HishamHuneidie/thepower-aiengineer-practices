from typing import Dict, Optional

from psycopg.errors import ForeignKeyViolation

from app.components.database import get_connection
from app.contexts.cars.domain.repositories import CarRepository


class InvalidOwnerError(Exception):
    pass


class PostgresCarRepository(CarRepository):
    def list(self):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, brand, model, year, owner_id FROM cars ORDER BY id")
                return cursor.fetchall()

    def get(self, car_id: int) -> Optional[Dict]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, brand, model, year, owner_id FROM cars WHERE id = %s",
                    (car_id,),
                )
                return cursor.fetchone()

    def create(self, data: Dict) -> Dict:
        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO cars (brand, model, year, owner_id)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id, brand, model, year, owner_id
                        """,
                        (data["brand"], data["model"], data["year"], data.get("owner_id")),
                    )
                    return cursor.fetchone()
        except ForeignKeyViolation as exc:
            raise InvalidOwnerError("Owner does not exist") from exc

    def update(self, car_id: int, data: Dict) -> Optional[Dict]:
        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE cars
                        SET brand = %s, model = %s, year = %s, owner_id = %s
                        WHERE id = %s
                        RETURNING id, brand, model, year, owner_id
                        """,
                        (
                            data["brand"],
                            data["model"],
                            data["year"],
                            data.get("owner_id"),
                            car_id,
                        ),
                    )
                    return cursor.fetchone()
        except ForeignKeyViolation as exc:
            raise InvalidOwnerError("Owner does not exist") from exc

    def delete(self, car_id: int) -> bool:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM cars WHERE id = %s", (car_id,))
                return cursor.rowcount > 0
