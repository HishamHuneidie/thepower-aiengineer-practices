"""
Methods to work with database and its entities
"""


# imports


from psycopg import Connection, sql
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid
import json
from typing_extensions import Self
from transformers.utils import logging as hf_logging


load_dotenv()
hf_logging.disable_progress_bar()


# general configs


TABLE_NAME_DOCUMENTS = os.environ.get('TABLE_NAME_DOCUMENTS', None)
TABLE_NAME_CHUNKS = os.environ.get('TABLE_NAME_CHUNKS', None)
TABLES = [TABLE_NAME_DOCUMENTS, TABLE_NAME_CHUNKS]
DATABASE_URL = os.environ.get('DATABASE_URL', None)
MODEL_EMBEDDING_NAME = os.environ.get('MODEL_EMBEDDING_NAME', None)
EMBEDDING_DIMENSIONS = os.environ.get('EMBEDDING_DIMENSIONS', None)


model = {
    'name': MODEL_EMBEDDING_NAME,
    'dimensions': EMBEDDING_DIMENSIONS,
    'transformer': None,
}


class Document:
    def __init__(self, id: str, path: str):
        self.id = id
        self.path = path
    
    
    def __str__(self) -> str:
        return '{{"path":"{}"}}'.format(self.path)


class Chunk:
    def __init__(self, content: str, embedding: list[float], reference: Document, id: str|None):
        self.content = content
        self.embedding = embedding
        self.reference = reference
        self.id = id


    def set_id(self, id: str) -> Self:
        self.id = id
        return self


    def __str__(self) -> str:
        global model

        mini_chunk = {
            'id': self.id,
            'content': f'{self.content[:35]}...',
            'embedding': f'list({model["dimensions"]}) -> [{str(self.embedding[0])}, {str(self.embedding[1])}, ...]',
            'reference': str(self.reference),
        }

        return 'Chunk: '+ json.dumps(mini_chunk, ensure_ascii=False, indent=2)


class ChunkSimilarity:
    def __init__(self, question: str, distance: float, chunk: Chunk, score: float|None=None):
        self.question = question
        self.distance = distance
        self.chunk = chunk
        self.score = score


    def set_score(self, score: float) -> Self:
        self.score = score
    
    
    def __str__(self) -> str:
        
        mini_chunk = {
            'id': self.chunk.id,
            'content': f'{self.chunk.content[:35]}...',
            'embedding': f'list({model["dimensions"]}) -> [{str(self.chunk.embedding[0])}, {str(self.chunk.embedding[1])}, ...]',
            'reference': str(self.chunk.reference),
        }

        mini_chunk_similarity = {
            'question': self.question,
            'distance': self.distance,
            'chunk': mini_chunk,
            'score': self.score,
        }

        return 'ChunkSimilarity: '+ json.dumps(mini_chunk_similarity, ensure_ascii=False, indent=2)
        


# connection


def connect() -> Connection:
    import psycopg
    from pgvector.psycopg import register_vector
    
    conn = psycopg.connect(DATABASE_URL, autocommit=True)
    conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
    register_vector(conn)
    
    if not has_tables(conn):
        create_tables(conn)
        
        conn.execute(
            sql
                .SQL("""
                CREATE INDEX IF NOT EXISTS {} ON {}
                USING hnsw (embedding vector_cosine_ops)
                """)
                .format(
                    sql.Identifier(TABLE_NAME_CHUNKS+'_hnsw'), 
                    sql.Identifier(TABLE_NAME_CHUNKS),
                )
        )
    
    return conn


def create_tables(conn: Connection) -> None:
    clean_db(conn)

    conn.execute(
        sql.SQL("""
        CREATE TABLE IF NOT EXISTS {} (
            id UUID PRIMARY KEY,
            path TEXT
        )
        """).format(sql.Identifier(TABLE_NAME_DOCUMENTS))
    )

    conn.execute(
        sql.SQL("""
        CREATE TABLE IF NOT EXISTS {} (
            id UUID PRIMARY KEY,
            document_id UUID NOT NULL REFERENCES {}(id) ON DELETE CASCADE,
            content TEXT,
            embedding VECTOR({})
        )
        """).format(
            sql.Identifier(TABLE_NAME_CHUNKS), 
            sql.Identifier(TABLE_NAME_DOCUMENTS), 
            EMBEDDING_DIMENSIONS,
        )
    )
    
    return


def has_tables(conn: Connection) -> bool:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM unnest(%s::text[]) AS t(name) WHERE to_regclass(name) IS NOT NULL",
            (TABLES,)
        )

        result = cursor.fetchone()
        return result is not None and result[0] == len(TABLES)


def embed(text: list[str]|str) -> list[float]|list[list[float]]:
    """Convert text to embedding"""
    
    global model

    from sentence_transformers import SentenceTransformer
    
    if model['transformer'] is None:
        model['transformer'] = SentenceTransformer(model['name'])

    return list(model['transformer'].encode(text, normalize_embeddings=True))


def insert_document(conn: Connection, document: Path) -> Document:
    document_id: str = str(uuid.uuid4())
    path = 'documents/'+ str(document.name)

    conn.execute(
        sql.SQL("""
        INSERT INTO {} (id, path)
        VALUES ({}, {})
        """).format(
            sql.Identifier(TABLE_NAME_DOCUMENTS),
            document_id,
            path,
        )
    )

    return Document(document_id, path)


def insert_chunk(conn: Connection, chunk: Chunk) -> Chunk:
    chunk_id: str = str(uuid.uuid4())
    chunk.set_id(chunk_id)

    conn.execute(
        sql.SQL("""
        INSERT INTO {} (id, document_id, content, embedding)
        VALUES ({}, {}, {}, {})
        """).format(
            sql.Identifier(TABLE_NAME_CHUNKS),
            chunk.id,
            chunk.reference.id,
            chunk.content,
            chunk.embedding,
        )
    )

    return chunk


def clean_db(conn: Connection) -> None:
    conn.execute(
        sql.SQL('DROP TABLE IF EXISTS {}').format(sql.Identifier(TABLE_NAME_CHUNKS))
    )
    conn.execute(
        sql.SQL('DROP TABLE IF EXISTS {}').format(sql.Identifier(TABLE_NAME_DOCUMENTS))
    )


def search(conn: Connection, question: str, is_extended: bool=False) -> list[ChunkSimilarity]:
    """Retrieve rows from database"""
    
    limit = 10 if is_extended else 3
    
    embedded_question = embed(question)
    
    query = sql.SQL("""
        SELECT
            ch.id, ch.document_id, ch.content, ch.embedding <=> %s::VECTOR AS distance, ch.embedding, docs.path
        FROM {} ch
        LEFT JOIN {} docs
            ON ch.document_id = docs.id
        ORDER BY 4 ASC
        LIMIT %s
        """).format(
            sql.Identifier(TABLE_NAME_CHUNKS),
            sql.Identifier(TABLE_NAME_DOCUMENTS),
        )
    
    records = conn.execute(query, (embedded_question, limit))

    result: ChunkSimilarity = []
    for id, document_id, content, distance, embedding, document_path in records:
        result.append(ChunkSimilarity(
            question,
            distance,
            Chunk(content, embedding.to_list(), Document(document_id, document_path), str(id)),
        ))

    return list(result)


# end