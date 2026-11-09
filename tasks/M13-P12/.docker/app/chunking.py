"""Crea los chunks que falten antes de arrancar FastAPI."""

import os
from pathlib import Path
from uuid import uuid4

from app.infrastructure.database import get_connection

CHUNK_SIZE = 100
CHUNK_OVERLAP = 10
MODEL_NAME = os.getenv(
    "MODEL_EMBEDDING_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
BASE_DIR = Path(__file__).resolve().parent


def split_in_chunks(text: str) -> list[str]:
    words = text.split()
    step = CHUNK_SIZE - CHUNK_OVERLAP
    return [" ".join(words[i:i + CHUNK_SIZE]) for i in range(0, len(words), step)]


def prepare_chunks() -> None:
    documents = sorted((BASE_DIR / "documents").glob("*.txt"))
    if not documents:
        raise RuntimeError("No hay documentos .txt para generar los chunks")

    model = None
    with get_connection() as connection:
        # También prepara las tablas cuando el volumen de PostgreSQL ya existía.
        connection.execute((BASE_DIR / "schema.sql").read_text(encoding="utf-8"))

        for document in documents:
            path = "documents/" + document.name
            exists = connection.execute(
                """SELECT EXISTS (
                    SELECT 1 FROM document_chunks ch
                    JOIN documents doc ON doc.id = ch.document_id
                    WHERE doc.path = %s
                ) AS found""",
                (path,),
            ).fetchone()["found"]
            if exists:
                print(f"Chunks ya existentes: {document.name}", flush=True)
                continue

            chunks = split_in_chunks(document.read_text(encoding="utf-8"))
            if not chunks:
                raise ValueError(f"El documento está vacío: {document.name}")

            if model is None:
                from sentence_transformers import SentenceTransformer

                print(f"Cargando modelo de embeddings: {MODEL_NAME}", flush=True)
                model = SentenceTransformer(MODEL_NAME, device="cpu")
                if model.get_sentence_embedding_dimension() != 384:
                    raise ValueError("El modelo debe generar embeddings de 384 dimensiones")

            embeddings = model.encode(chunks, normalize_embeddings=True)
            row = connection.execute(
                """INSERT INTO documents (id, path) VALUES (%s, %s)
                ON CONFLICT (path) DO UPDATE SET path = EXCLUDED.path RETURNING id""",
                (uuid4(), path),
            ).fetchone()
            with connection.cursor() as cursor:
                cursor.executemany(
                    """INSERT INTO document_chunks
                    (id, document_id, position, content, embedding)
                    VALUES (%s, %s, %s, %s, %s::vector)""",
                    [
                        (uuid4(), row["id"], position, chunk, str(embedding.tolist()))
                        for position, (chunk, embedding) in enumerate(zip(chunks, embeddings))
                    ],
                )
            print(f"Creados {len(chunks)} chunks: {document.name}", flush=True)

    print("Documentos preparados. Arrancando FastAPI.", flush=True)


if __name__ == "__main__":
    prepare_chunks()
