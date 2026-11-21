import os

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row


TABLE_NAME_DOCUMENTS = os.environ.get('TABLE_NAME_DOCUMENTS', None)
TABLE_NAME_CHUNKS = os.environ.get('TABLE_NAME_CHUNKS', None)
MODEL_EMBEDDING_NAME = os.environ.get('MODEL_EMBEDDING_NAME', None)
MODEL_EMBEDDING_DIMENSIONS = os.environ.get('MODEL_EMBEDDING_DIMENSIONS', None)


model = {
    'name': MODEL_EMBEDDING_NAME,
    'dimensions': MODEL_EMBEDDING_DIMENSIONS,
    'transformer': None,
}


def get_connection():
    connection = psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "thepower"),
        user=os.getenv("POSTGRES_USER", "thepower"),
        password=os.getenv("POSTGRES_PASSWORD", "thepower"),
        row_factory=dict_row,
    )

    register_vector(connection)

    return connection


def embed(text: list[str] | str) -> list[float] | list[list[float]]:
    """Convert text to embedding"""

    global model

    from sentence_transformers import SentenceTransformer

    if model['transformer'] is None:
        model['transformer'] = SentenceTransformer(model['name'])

    return list(model['transformer'].encode(text, normalize_embeddings=True))