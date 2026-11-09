"""
Reranking of records
"""

# imports


import json
import os
import re

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from psycopg import Connection

from database import ChunkSimilarity, search
from utils import update_progress

# configs

load_dotenv()
threshold = None
MODEL_RERANKER_NAME = os.environ.get('MODEL_RERANKER_NAME', None)
CHUNKS_ENOUGH, CHUNKS_NON_ENOUGH, CHUNKS_PARTIALLY_ENOUGH = 'is_enough', 'is_not_enough', 'is_partially_enough'


# reranking


_reranker = None


def get_reranker():
    """Load the cross-encoder once"""
    global _reranker

    if _reranker is None:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder(MODEL_RERANKER_NAME)

    return _reranker


def reranking(rows: list[ChunkSimilarity], is_extended: bool = False) -> list[ChunkSimilarity]:
    if not rows:
        return []

    pairs = [(row.question, row.chunk.content) for row in rows]
    scores = get_reranker().predict(pairs)
    
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

    THRESHOLD_MARGIN = 1.0

    answerable_scores = [score for score, has_answer in samples if has_answer]

    if not answerable_scores:
        raise ValueError('No validation questions with has_answer=true')

    return min(answerable_scores) - THRESHOLD_MARGIN


judge = ChatOllama(model='llama3.2:3b', temperature=0, format='json')


def split_question(question: str) -> list[str]:
    """Split by question marks only. Never invents parts."""

    parts = [part.strip(' ¿?¡!.,;') for part in question.split('?')]
    parts = [re.sub(r'^(y|e|o)\s+', '', part, flags=re.IGNORECASE) for part in parts]
    return [f'¿{part}?' for part in parts if part]


def decompose(question: str) -> list[str]:
    """
    Split a compound question into self-contained sub-questions.
    The split is deterministic (by '?'); the LLM only resolves references
    ("y cuánto dura?" -> "¿Cuánto dura el curso?") and must keep the same number of parts.
    """

    parts = split_question(question)

    # a single question is never split
    if len(parts) <= 1:
        return [question.strip()]

    numbered = '\n'.join(f'{i}. {part}' for i, part in enumerate(parts, 1))
    prompt = f"""
        Original text: {question}

        Questions:
        {numbered}

        Rewrite each question so it is self-contained, in Spanish, replacing references
        (like "y cuánto dura?") with the subject mentioned in the other questions.
        Return exactly {len(parts)} questions, in the same order.
        Do not add, remove, merge or split questions. Do not add new topics.
        Respond just with a JSON like: {{"questions": ["...", "..."]}}
    """

    try:
        data = json.loads(judge.invoke(prompt).content)
        questions = [str(q).strip().strip('"\'') for q in data['questions'] if str(q).strip()]
        if len(questions) == len(parts):
            return questions
    except Exception:
        pass

    return parts


GREY_MARGIN = 2.0  # below threshold but within this margin -> ask the LLM


def judge_answers(question: str, rows: list[ChunkSimilarity]) -> bool:
    """Strict yes/no: does the context contain the data asked by a single question?"""

    context = "\n- ".join([row.chunk.content for row in rows])
    prompt = f"""
        Context:
        - {context}

        Question: {question}

        Does the context contain the exact information that answers the question?
        Be strict: related information is not enough, the specific data asked must appear explicitly.
        Respond just with a JSON like: {{"answers": true}} or {{"answers": false}}
    """

    try:
        answers = json.loads(judge.invoke(prompt).content)['answers']
        return answers is True or str(answers).strip().lower() == 'true'
    except Exception:
        return False


def assess(conn: Connection, sub_questions: list[str], rows: list[ChunkSimilarity]) -> tuple[
    str, list[ChunkSimilarity], list[str]]:
    """
    Score every chunk against every sub-question (not the whole compound question).
    A sub-question is covered if a chunk reaches the threshold, or if it is in the
    grey zone (threshold - GREY_MARGIN) and the LLM confirms it answers it.
    Returns tuple[state, useful_chunks, missing_sub_questions]
    """

    global threshold

    if threshold is None:
        update_progress('threshold')
        threshold = calculate_threshold(conn)

    if not rows:
        return CHUNKS_NON_ENOUGH, [], list(sub_questions)

    reranker = get_reranker()
    best_score = {row.chunk.id: float('-inf') for row in rows}
    useful_ids: set[str] = set()
    missing: list[str] = []

    for sub_question in sub_questions:
        scores = reranker.predict([(sub_question, row.chunk.content) for row in rows])
        scored = sorted(zip(rows, map(float, scores)), key=lambda pair: pair[1], reverse=True)

        for row, score in scored:
            best_score[row.chunk.id] = max(best_score[row.chunk.id], score)

        # keep the top 3 chunks over threshold for this sub-question
        top = scored[:3]
        passing = [row for row, score in top if score >= threshold]

        # grey zone: the reranker is unsure, let the LLM decide
        if not passing:
            grey = [row for row, score in top if score >= threshold - GREY_MARGIN]
            if grey and judge_answers(sub_question, grey):
                passing = grey

        useful_ids.update(row.chunk.id for row in passing)

        if not passing:
            missing.append(sub_question)

    for row in rows:
        row.set_score(best_score[row.chunk.id])

    useful = sorted(
        [row for row in rows if row.chunk.id in useful_ids],
        key=lambda row: row.score,
        reverse=True,
    )

    if not missing:
        return CHUNKS_ENOUGH, useful, []

    if len(missing) < len(sub_questions):
        return CHUNKS_PARTIALLY_ENOUGH, useful, missing

    return CHUNKS_NON_ENOUGH, [], missing