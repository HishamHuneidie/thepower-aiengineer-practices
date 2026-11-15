from app.domain.entities import Message
from app.infrastructure.database import get_connection


class PostgresMessageRepository:
    def save(self, messages: list[Message]) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """INSERT INTO messages (id, text, role, audio_path, image_path, audio_transcript, image_transcript, response_in_audio_path)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    [(message.id, message.text, message.role, message.audio_path, message.image_path, message.audio_transcript, message.image_transcript, message.response_in_audio_path)
                     for message in messages],
                )

    def list_all(self) -> list[Message]:
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT id, text, role, audio_path, image_path FROM messages ORDER BY position"
            ).fetchall()
        return [Message(**row) for row in rows]
