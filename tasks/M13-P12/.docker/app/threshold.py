"""Calcula el threshold del reranker antes de arrancar FastAPI, solo si aún no está guardado.

Mismo criterio que M12-P11: se lanzan las preguntas de validación, se rerankean los chunks
y el threshold es el peor "mejor score" de las preguntas que sí tienen respuesta, menos un margen.
"""

import json
from pathlib import Path

from app.application.rag_service import RAGService
from app.infrastructure.postgres_repository import (
    PostgresChunkRepository,
    PostgresSettingsRepository,
)

THRESHOLD_KEY = "threshold"
THRESHOLD_MARGIN = 1.0
BASE_DIR = Path(__file__).resolve().parent


def calculate_threshold() -> float:
    validation = json.loads(
        (BASE_DIR / "assess" / "validation_questions.json").read_text(encoding="utf-8")
    )["validation"]
    has_answer = {item["question"]: item["has_answer"] for item in validation}

    # Se usa el repositorio directamente para que un error pare el arranque en vez de devolver [].
    rows = PostgresChunkRepository().find(list(has_answer))
    if not rows:
        raise RuntimeError("No se encontraron chunks para las preguntas de validación")

    # Mismo reranker que usa la app, para que los scores sean comparables.
    ranked = RAGService().rerank(rows)

    # Mejor score de cada pregunta.
    best: dict[str, float] = {}
    for row in ranked:
        best[row.question] = max(best.get(row.question, float("-inf")), float(row.score))

    answerable = [score for question, score in best.items() if has_answer[question]]
    if not answerable:
        raise ValueError("No hay preguntas de validación con has_answer=true")

    return min(answerable) - THRESHOLD_MARGIN


def prepare_threshold() -> None:
    settings = PostgresSettingsRepository()

    saved = settings.get(THRESHOLD_KEY)
    if saved is not None:
        print(f"Threshold ya existente: {saved}", flush=True)
        return

    threshold = calculate_threshold()
    settings.set(THRESHOLD_KEY, str(threshold))
    print(f"Threshold calculado y guardado: {threshold}", flush=True)


if __name__ == "__main__":
    prepare_threshold()
    print("Threshold preparado. Arrancando FastAPI.", flush=True)
