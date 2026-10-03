from typing import Dict, Optional

from psycopg.errors import ForeignKeyViolation

from app.components.database import get_connection
from app.contexts.{entity_plural_name}.domain.repositories import {EntityName}RepositoryInterface



class SqlRelationError(Exception):
    pass


class {EntityName}Repository({EntityName}RepositoryInterface):
    def list(self):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, brand, model, year, owner_id FROM {entity_plural_name} ORDER BY id")
                return cursor.fetchall()

    def get(self, {entity_name}_id: int) -> Optional[Dict]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, brand, model, year, owner_id FROM {entity_plural_name} WHERE id = %s",
                    ({entity_name}_id,),
                )
                return cursor.fetchone()

    def create(self, data: Dict) -> Dict:
        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO {entity_plural_name} (brand, model, year, owner_id)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id, brand, model, year, owner_id
                        """,
                        (data["brand"], data["model"], data["year"], data.get("owner_id")),
                    )
                    return cursor.fetchone()
        except ForeignKeyViolation as exc:
            raise SqlRelationError("Error in the relation between tables") from exc

    def update(self, {entity_name}_id: int, data: Dict) -> Optional[Dict]:
        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE {entity_plural_name}
                        SET brand = %s, model = %s, year = %s, owner_id = %s
                        WHERE id = %s
                        RETURNING id, brand, model, year, owner_id
                        """,
                        (
                            data["brand"],
                            data["model"],
                            data["year"],
                            data.get("owner_id"),
                            {entity_name}_id,
                        ),
                    )
                    return cursor.fetchone()
        except ForeignKeyViolation as exc:
            raise SqlRelationError("Error in the relation between tables") from exc

    def delete(self, {entity_name}_id: int) -> bool:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM {entity_plural_name} WHERE id = %s", ({entity_name}_id,))
                return cursor.rowcount > 0
