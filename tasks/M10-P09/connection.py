# imports

import os
import psycopg
from typing import Any
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from transformer import model

load_dotenv()

# get connection

def connect(has_vector: bool=False) -> psycopg.Connection:
    """Opens a pg connection. Database URL must be set in .env"""
    conn = psycopg.connect(os.environ['DATABASE_URL'], autocommit=True)

    if has_vector:
        register_vector(conn)

    return conn

# create/register vector

def enable_vectors(conn: psycopg.Connection) -> None:
    """Set up vector in connection"""
    conn.execute('CREATE EXTENSION IF NOT EXISTS vector')

# create tables

def create_table_phrases(conn: psycopg.Connection) -> None:
    """Create a table"""
    conn.execute('DROP TABLE IF EXISTS phrases')
    conn.execute(f'CREATE TABLE phrases (id SERIAL PRIMARY KEY, content TEXT, embedding VECTOR({model["dimensions"]}))')

def create_table_phrases_tenant(conn: psycopg.Connection) -> None:
    """Create a table"""
    conn.execute('DROP TABLE IF EXISTS phrases_tenant')
    conn.execute(f'CREATE TABLE phrases_tenant (id SERIAL PRIMARY KEY, tenant_id TEXT NOT NULL, content TEXT, embedding VECTOR({model["dimensions"]}))')

# Clear all new data

def delete_tables(conn: psycopg.Connection) -> None:
    conn.execute('DROP TABLE IF EXISTS phrases')
    conn.execute('DROP TABLE IF EXISTS phrases_tenant')