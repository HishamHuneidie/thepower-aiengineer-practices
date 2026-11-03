"""
CRAG
"""

# imports


from pathlib import Path
from database import connect, search, ChunkSimilarity, clean_db
from chunking import prepare_chunks
from reranking import reranking, assess
from colorize import colorize
from utils import update_progress, print_line_splitter
import sys
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
from tabulate import tabulate


# general configs


BASE = Path(__file__).resolve().parent
GEN_MODEL_ID = 'llama3.2:3b'
EMBEDDING_MODEL_ID = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
REJECTION = 'No tengo información suficiente en los documentos para responder.'
PROMPT_INPUT = colorize("""
Pregunta algo como:
- ¿En qué plataforma puedo ver las clases?
- ¿Cómo recupero mi contraseña?
- ¿Cuándo está abierta la academia entre semana?

> """, 'gray')


llm = ChatOllama(model=GEN_MODEL_ID, temperature=0)
system_message = ('system', 'Answer always in Spanish and USE ALWAYS the context to respond')
human_message_template = """
Context:
- {context}

Question: {question}
"""


# database connection


conn = connect()


# chunking


prepare_chunks()


def respond(rows: list[ChunkSimilarity], question: str) -> str|None:
    """Generate an answer from similar chunks"""
    
    global llm, system_message, human_message_template

    if not rows:
        return None

    # Call LLM
    
    context = "\n- ".join([row.chunk.content for row in rows])
    human_message = human_message_template.format(context=context, question=question)

    response: AIMessage = llm.invoke([
        system_message,
        ('human', human_message),
    ])
    
    return response.content


def wrap_response(response: str) -> str:
    delimiter = colorize('| ', 'green')

    return delimiter + f'\n{delimiter}'.join(response.splitlines())


def wrap_cell_content(cell_content: str, color: str|None) -> str:
    words = cell_content.split()
    
    words_count = 12
    
    if not color:
        return "\n".join(
            " ".join(words[i:i + words_count])
            for i in range(0, len(words), words_count)
        )

    return "\n".join(
        colorize(" ".join(words[i:i + words_count]), color)
        for i in range(0, len(words), words_count)
    )


def show_response(response: str, accepted_rows: list[ChunkSimilarity], rows: list[ChunkSimilarity]) -> str:
    from reranking import threshold
    
    if not response:
        print()
        print(colorize('There is no answer for you', 'red'))
        print()
        return
    
    rows_to_show = [
            [
                threshold,
                row.chunk.id,
                wrap_cell_content(row.chunk.content, 'green'),
                row.chunk.reference.path,
                colorize(row.score, 'green'),
            ]
            for row in accepted_rows
        ] + [
            [
                threshold,
                row.chunk.id,
                wrap_cell_content(row.chunk.content, 'red'),
                row.chunk.reference.path,
                colorize(row.score, 'red'),
            ]
            for row in rows if row not in accepted_rows
        ]
    
    print()
    # TODO: Falta chunk_id, document_path, threshold, chunks malos
    print(tabulate(
        rows_to_show,
        headers=['Threshold', 'Chunk ID', 'Chunk content', 'Document', 'Score'],
        tablefmt='rounded_grid'
    ))
    print()
    print(colorize('Response: ', 'green'))
    print(wrap_response(response))
    print()


# Question and answer


if __name__ == '__main__':
    while True:
        try:
            # Ask for a new question
            question = str(input(PROMPT_INPUT)).strip()
            
            if not question:
                continue
            
            # retrieve chunks with possible answers
            print()
            update_progress('retrieve')
            rows = search(conn, question, True)

            # reranking
            update_progress('reranking')
            sorted_rows = reranking(rows)

            # assess
            update_progress('assess')
            accepted_rows = assess(conn, sorted_rows)

            update_progress('response')
            response = respond(accepted_rows, question)
            update_progress('end')
            
            show_response(response, accepted_rows, sorted_rows)
            
            print_line_splitter()
        except Exception as e:
            print()
            clean_db(conn)
            print(colorize(str(e), 'red'))
            print(colorize('Bye bye', 'purple'))
            sys.exit(0)