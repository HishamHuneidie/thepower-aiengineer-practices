from app.domain.entities import ChunkSimilarity
from app.infrastructure.postgres_repository import PostgresChunkRepository, PostgresSettingsRepository
import os


MODEL_RERANKER_NAME = os.getenv('MODEL_RERANKER_NAME', '')


chunk_repository = PostgresChunkRepository()
settings_repository = PostgresSettingsRepository()
_reranker = None
_threshold: float | None = None


def get_threshold() -> float:
    """Threshold calculado por threshold.py al arrancar el contenedor (se lee una sola vez)."""
    global _threshold

    if _threshold is None:
        value = settings_repository.get('threshold')
        if value is None:
            raise RuntimeError('No hay threshold guardado. Revisa que threshold.py se ejecutó al arrancar.')
        _threshold = float(value)

    return _threshold


class RAGService:


    def get_reranker(self):
        """Retrieve the reranker"""
        global _reranker

        if not _reranker:
            from sentence_transformers import CrossEncoder
            _reranker = CrossEncoder(MODEL_RERANKER_NAME, device='cpu')

        return _reranker


    def retrieve(self, questions: list[str]) -> list[ChunkSimilarity]:
        """Retrieve rows from database"""

        try:
            results = chunk_repository.find(questions)

            return self.assess(self.rerank(results))
        except Exception as e:
            print(e)
            return []


    def rerank(self, chunks: list[ChunkSimilarity]) -> list[ChunkSimilarity]:
        """Rerank chunks"""

        if not chunks:
            return []

        pairs = [(chunk.question, chunk.chunk.content) for chunk in chunks]

        ranker = self.get_reranker()
        scores = ranker.predict(pairs)

        for chunk, score in zip(chunks, scores):
            chunk.score = float(score)

        return sorted(chunks, key=lambda c: c.score, reverse=True)


    def assess(self, chunks: list[ChunkSimilarity]) -> list[ChunkSimilarity]:
        """Devuelve solo los chunks (ya rerankeados) cuyo score supera el threshold"""

        threshold = get_threshold()

        return [
            chunk for chunk in chunks
            if chunk.score is not None and chunk.score >= threshold
        ]
