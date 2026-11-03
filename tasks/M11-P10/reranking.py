"""
Reranking of records
"""

# imports


from database import ChunkSimilarity, search
from dotenv import load_dotenv
import os
import json
from psycopg import Connection
from utils import update_progress


# configs

load_dotenv()
threshold = None
MODEL_RERANKER_NAME = os.environ.get('MODEL_RERANKER_NAME', None)


# reranking


def reranking(rows: list[ChunkSimilarity], is_extended: bool=False) -> list[ChunkSimilarity]:
    from sentence_transformers import CrossEncoder

    pairs = [(row.question, row.chunk.content) for row in rows]
    
    reranker = CrossEncoder(MODEL_RERANKER_NAME)
    scores = reranker.predict(pairs)
    
    for row, score in zip(rows, scores):
        row.set_score(float(score))
    
    limit = 10 if is_extended else 3
    
    return sorted(rows, key=lambda row: row.score, reverse=True)[:limit]


def calculate_threshold(conn: Connection) -> float:
    validation_questions = []
    with open('./assess/validation_questions.json') as questions_file:
        validation_questions = json.load(questions_file)['validation']

    samples: list[tuple[float,bool]] = []

    # Get validation questions

    for question in validation_questions:
        rows = search(conn, question['question'], True)
        ranked = reranking(rows)

        if not ranked:
            continue

        samples.append((ranked[0].score, question['has_answer']))
        
    # Calculate threshold

    scores = [score for score, _ in samples]
    candidates = scores + [max(scores) + 1]

    return max(candidates, key=lambda threshold: (
        sum((score >= threshold) == has_answer
            for score, has_answer in samples),
        threshold,
    ))


def assess(conn: Connection, rows: list[ChunkSimilarity]) -> list[ChunkSimilarity]:
    global threshold
    
    if not threshold:
        update_progress('threshold')
        threshold = calculate_threshold(conn)

    return [row for row in rows if row.score >= threshold]