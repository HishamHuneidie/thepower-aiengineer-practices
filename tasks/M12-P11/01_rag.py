"""
CRAG
"""

# imports


import sys
from pathlib import Path

from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from tabulate import tabulate

from chunking import prepare_chunks
from colorize import colorize
from database import connect, search, ChunkSimilarity, clean_db
from reranking import reranking, assess, decompose, CHUNKS_ENOUGH, CHUNKS_NON_ENOUGH
from utils import update_progress, print_line_splitter, add_logs, reset_progress

# general configs


BASE = Path(__file__).resolve().parent
GEN_MODEL_ID = 'llama3.2:3b'
EMBEDDING_MODEL_ID = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
REJECTION = 'No tengo información suficiente en los documentos para responder.'
PROMPT_INPUT = colorize("""
Pregunta algo como:
- ¿En qué plataforma puedo ver las clases?
- ¿Cómo recupero mi contraseña?
- ¿como pago el curso? cuanto cuesta el curso? y cuanto dura?

> """, 'gray')


llm = ChatOllama(model=GEN_MODEL_ID, temperature=0)
system_message = ('system', 'Answer always in Spanish and USE ALWAYS the context to respond')
human_message_template = """
Context:
- {context}

Question: {question}
"""
missing_instruction_template = """
Answer ONLY the part of the question that the context covers. DO NOT invent anything about: {missing}
"""


# database connection


conn = connect()


# chunking


prepare_chunks(True)


def respond(rows: list[ChunkSimilarity], question: str, missing: str = '') -> str | None:
    """Generate an answer from similar chunks"""
    
    global llm, system_message, human_message_template

    if not rows:
        return None

    # Call LLM
    
    context = "\n- ".join([row.chunk.content for row in rows])
    human_message = human_message_template.format(context=context, question=question)

    if missing:
        human_message += missing_instruction_template.format(missing=missing)

    response: AIMessage = llm.invoke([
        system_message,
        ('human', human_message),
    ])

    if missing:
        return f'{response.content}\n\nNo tengo información sobre: {missing}'

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
    print(tabulate(
        rows_to_show,
        headers=['Threshold', 'Chunk ID', 'Chunk content', 'Document', 'Score'],
        tablefmt='rounded_grid'
    ))
    print()
    print(colorize('Response: ', 'green'))
    print(wrap_response(response))
    print()


def reformulate(sub_question: str) -> str:
    """Rephrase a sub-question that found no chunks, to retry the retrieval."""

    global llm

    prompt = f"""
        Question: {sub_question}

        Rewrite the question in Spanish with different words or synonyms,
        so it can be searched again in a document base.
        Return just the new question.
    """

    return llm.invoke(prompt).content.strip().strip('"\'')


def crag(question: str) -> tuple[str, list[ChunkSimilarity], list[ChunkSimilarity]]:
    """Retrieve, rerank and assess up to 3 times. Return tuple[response_str, used_rows, all_rows]"""

    sub_questions = decompose(question)
    add_logs(colorize(f'sub-questions={sub_questions}', 'gray'))

    candidates: dict[str, ChunkSimilarity] = {}
    tried: set[str] = set()
    pending = list(sub_questions)
    state, useful, missing = CHUNKS_NON_ENOUGH, [], list(sub_questions)

    for attempt in range(1, 4):
        queries = pending if attempt == 1 else [reformulate(q) for q in pending]
        queries = [q for q in queries if q not in tried]
        if not queries:
            break
        tried.update(queries)

        # retrieve + rerank per query, so each part of the question gets its own chunks
        for query in queries:
            update_progress('retrieve')
            rows = search(conn, query, True)

            update_progress('rerank')
            for row in reranking(rows, True):
                candidates.setdefault(row.chunk.id, row)

        update_progress('assess')
        state, useful, missing = assess(conn, sub_questions, list(candidates.values()))

        add_logs(colorize(
            f'[{attempt}] [{state}] · queries={queries} · missing={missing} · kept={len(useful)}',
            'gray',
        ))

        if state == CHUNKS_ENOUGH:
            break

        pending = missing

    all_rows = sorted(candidates.values(), key=lambda row: row.score, reverse=True)[:10]

    if state == CHUNKS_NON_ENOUGH:
        return REJECTION, [], all_rows

    update_progress('response')
    response = respond(useful, question, ', '.join(missing))
    update_progress('end')

    return response, useful, all_rows


# Question and answer


if __name__ == '__main__':
    while True:
        try:
            # Ask for a new question
            question = str(input(PROMPT_INPUT)).strip()
            
            if not question:
                continue

            # retrieve -> rerank -> (-> reformulate) -> answer|refuse
            print()
            reset_progress()
            response, accepted_rows, sorted_rows = crag(question)
            
            show_response(response, accepted_rows, sorted_rows)
            
            print_line_splitter()
        except Exception as e:
            print()
            print(colorize(str(e), 'red'))
            print(colorize('Bye bye', 'purple'))
            sys.exit(0)

    clean_db(conn)
