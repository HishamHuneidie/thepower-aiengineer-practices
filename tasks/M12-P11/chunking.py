"""
Generate and save chunks from documents
"""


# imports


from pathlib import Path
from colorize import colorize
from database import (
    connect,
    embed,
    Chunk,
    Document,
    insert_document,
    insert_chunk,
    has_tables,
    create_tables,
)
from utils import show_progress


# configs

CHUNK_SIZE = 100
CHUNK_OVERLAP = 10


# Search documents


folder: Path = Path('./documents')
conn = connect()


# Iterate documents, split their content, embed and save


def split_in_chunks(text: str) -> list[str]:
    words = text.split()
    
    word_frequency = CHUNK_SIZE - CHUNK_OVERLAP
    
    return [
        " ".join(words[i:i+CHUNK_SIZE])
        for i in range(0, len(words), word_frequency)
    ]


def chunking() -> None:
    """Embed and save files content"""
    
    print(colorize('Chunking...', 'green'))
    print()
    
    total_chunks: int = count_estimated_chunks()
    count = 0

    for document in folder.iterdir():
        
        if not document.is_file():
            continue
        
        content = document.read_text(encoding='utf-8')
        str_chunks = split_in_chunks(content)
        embedded_chunks: list[list[float]] = embed(str_chunks)
        doc: Document = insert_document(conn, document)
        
        for str_chunk, embedded_chunk in zip(str_chunks, embedded_chunks):
            chunk: Chunk = insert_chunk(conn, Chunk(str_chunk, embedded_chunk, doc, None))

            if chunk:
                count = count + 1

            show_progress(total_chunks, count)

    print()
    print(colorize('Finish chunking', 'green'))


def count_estimated_chunks() -> int:
    """Count how many chunks would be"""

    count = 0

    for document in folder.iterdir():
        
        if not document.is_file():
            continue

        content = document.read_text(encoding='utf-8')
        str_chunks = split_in_chunks(content)
        count = count + len(str_chunks)

    return count


def prepare_chunks(force_recreate: bool=False) -> None:
    """Chunk in case not exists chunks"""
    
    if has_tables(conn) and not force_recreate:
        print(colorize('Chunks already exist!!', 'yellow'))
        return
    
    if force_recreate:
        create_tables(conn)

    return chunking()


# end