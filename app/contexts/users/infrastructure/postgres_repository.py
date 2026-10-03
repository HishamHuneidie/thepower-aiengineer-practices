from typing import Dict, Optional

from app.components.database import get_connection
from app.contexts.users.domain.repositories import UserRepository


class PostgresUserRepository(UserRepository):
    def list(self):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, name, email FROM users ORDER BY id")
                return cursor.fetchall()

    def get(self, user_id: int) -> Optional[Dict]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, email FROM users WHERE id = %s",
                    (user_id,),
                )
                return cursor.fetchone()

    def create(self, data: Dict) -> Dict:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (name, email)
                    VALUES (%s, %s)
                    RETURNING id, name, email
                    """,
                    (data["name"], data["email"]),
                )
                return cursor.fetchone()

    def update(self, user_id: int, data: Dict) -> Optional[Dict]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE users
                    SET name = %s, email = %s
                    WHERE id = %s
                    RETURNING id, name, email
                    """,
                    (data["name"], data["email"], user_id),
                )
                return cursor.fetchone()

    def delete(self, user_id: int) -> bool:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                return cursor.rowcount > 0
