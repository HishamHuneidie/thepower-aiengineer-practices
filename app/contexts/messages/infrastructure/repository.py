from typing import Dict, Optional

from psycopg.errors import ForeignKeyViolation

from app.components.database import get_connection
from app.contexts.messages.domain.repositories import MessageRepositoryInterface



class SqlRelationError(Exception):
    pass


class MessageRepository(MessageRepositoryInterface):
    def list(self):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, question, answer, sender_id, sent_at FROM messages ORDER BY id")
                return cursor.fetchall()

    def get(self, message_id: int) -> Optional[Dict]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, question, answer, sender_id, sent_at FROM messages WHERE id = %s",
                    (message_id,),
                )
                return cursor.fetchone()

    def create(self, data: Dict) -> Dict:
        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO messages (question, answer, sender_id)
                        VALUES (%s, %s, %s)
                        RETURNING id, question, answer, sender_id, sent_at
                        """,
                        (data["question"], data["answer"], data.get("sender_id")),
                    )
                    return cursor.fetchone()
        except ForeignKeyViolation as exc:
            raise SqlRelationError("Error in the relation between tables") from exc
