from dataclasses import asdict, fields

from psycopg.types.json import Jsonb

from app.domain.entities import Message, ResearchJob
from app.infrastructure.database import (
    get_connection,
    embed,
    TABLE_NAME_CHUNKS,
    TABLE_NAME_DOCUMENTS,
)
from psycopg import sql
from app.domain.entities import Chunk, ChunkSimilarity
from psycopg.rows import tuple_row


class PostgresSettingsRepository:
    def get(self, key: str) -> str | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT value FROM settings WHERE key = %s", (key,)
            ).fetchone()
        return row["value"] if row else None

    def set(self, key: str, value: str) -> None:
        with get_connection() as connection:
            connection.execute(
                """INSERT INTO settings (key, value) VALUES (%s, %s)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value""",
                (key, value),
            )


class PostgresMessageRepository:
    def save(self, messages: list[Message]) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """INSERT INTO messages (id, thread_id, text, role, audio_path, image_path, audio_transcript, image_transcript, response_in_audio_path)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    [(message.id, message.thread_id, message.text, message.role, message.audio_path, message.image_path, message.audio_transcript, message.image_transcript, message.response_in_audio_path)
                     for message in messages],
                )

    def list_all(self, thread_id: str) -> list[Message]:
        """Solo los mensajes de una conversación."""
        with get_connection() as connection:
            rows = connection.execute(
                """SELECT id, thread_id, text, role, audio_path, image_path, audio_transcript, image_transcript, response_in_audio_path
                FROM messages WHERE thread_id = %s ORDER BY position""",
                (thread_id,),
            ).fetchall()
        return [Message(**row) for row in rows]


RESEARCH_COLUMNS = [f.name for f in fields(ResearchJob) if f.name not in ("reused", "local_status")]


def _research_from_row(row: dict) -> ResearchJob:
    values = dict(row)
    for key in ("created_at", "updated_at", "completed_at"):
        if values.get(key) is not None:
            values[key] = values[key].isoformat()
    return ResearchJob(**values)


class PostgresResearchRepository:
    def get(self, interaction_id: str) -> ResearchJob | None:
        with get_connection() as connection:
            row = connection.execute(
                f"SELECT {', '.join(RESEARCH_COLUMNS)} FROM research_jobs WHERE interaction_id = %s",
                (interaction_id,),
            ).fetchone()
        return _research_from_row(row) if row else None

    def latest_real(self) -> ResearchJob | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""SELECT {', '.join(RESEARCH_COLUMNS)} FROM research_jobs
                WHERE simulated = FALSE ORDER BY created_at DESC LIMIT 1"""
            ).fetchone()
        return _research_from_row(row) if row else None

    def count_real(self) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT count(*) AS total FROM research_jobs WHERE simulated = FALSE").fetchone()
        return int(row["total"])

    def save(self, job: ResearchJob) -> None:
        """Inserta o actualiza (por interaction_id)."""
        data = asdict(job)
        values = {column: data[column] for column in RESEARCH_COLUMNS}
        values["sources"] = Jsonb(values["sources"] or [])
        values["usage"] = Jsonb(values["usage"]) if values["usage"] is not None else None
        columns = [c for c in RESEARCH_COLUMNS if c != "updated_at"]
        placeholders = {c: f"%({c})s" for c in columns}
        placeholders["created_at"] = "COALESCE(%(created_at)s::timestamptz, now())"
        placeholders["completed_at"] = "%(completed_at)s::timestamptz"
        updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in columns if c not in ("interaction_id", "created_at"))
        with get_connection() as connection:
            connection.execute(
                f"""INSERT INTO research_jobs ({', '.join(columns)}, updated_at)
                VALUES ({', '.join(placeholders[c] for c in columns)}, now())
                ON CONFLICT (interaction_id) DO UPDATE SET {updates}, updated_at = now()""",
                values,
            )


class PostgresChunkRepository:
    def find(self, questions: list[str]) -> list[ChunkSimilarity]:
        with get_connection() as connection:
            with connection.cursor(row_factory=tuple_row) as cur:

                embedded_questions = [str(e.tolist()) for e in embed(questions)]

                query = sql.SQL("""
                    SELECT
                        q.idx AS question_id,
                        q.question AS question,
                        ch.id,
                        ch.document_id,
                        ch.content,
                        ch.distance,
                        ch.embedding::real[] as embedding,
                        docs.path
                    FROM unnest(%s::text[], %s::text[]) WITH ORDINALITY AS q(question, emb, idx)
                    CROSS JOIN LATERAL (
                        SELECT c.*, c.embedding <=> q.emb::VECTOR AS distance
                        FROM {} c
                        ORDER BY distance ASC
                        LIMIT %s
                    ) ch
                    LEFT JOIN {} docs ON ch.document_id = docs.id
                    ORDER BY q.idx, ch.distance
                """).format(
                    sql.Identifier(TABLE_NAME_CHUNKS),
                    sql.Identifier(TABLE_NAME_DOCUMENTS),
                )

                records = cur.execute(query, (questions, embedded_questions, 5)).fetchall()

                results: list[ChunkSimilarity] = []
                for question_id, question, id, document_id, content, distance, embedding, path in records:

                    chunk: Chunk = Chunk(
                        content=content,
                        embedding=embedding,
                        document_id=document_id,
                        id=id,
                    )

                    chunk_similarity: ChunkSimilarity = ChunkSimilarity(
                        chunk=chunk,
                        question=question,
                        distance=distance,
                        score=None,
                    )

                    results.append(chunk_similarity)

                return results