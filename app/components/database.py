import os

import psycopg
from psycopg.rows import dict_row


def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "thepower"),
        user=os.getenv("POSTGRES_USER", "thepower"),
        password=os.getenv("POSTGRES_PASSWORD", "thepower"),
        row_factory=dict_row,
    )
