from dataclasses import dataclass, field
from io import BytesIO
from typing import Literal
from uuid import UUID, uuid4
import json


class Audio(BytesIO):
    file_type = 'audio'
    mime_type = 'audio/wav'


class Image(BytesIO):
    file_type = 'image'
    mime_type = 'image/png'


@dataclass
class Message:
    role: Literal["user", "assistant"]
    thread_id: str = "default"
    id: UUID = field(default_factory=uuid4)
    text: str | None = None
    audio_path: str | None = None
    image_path: str | None = None
    audio_transcript: str | None = None
    image_transcript: str | None = None
    response_in_audio_path: str | None = None


class ParentChunk:
    pass


@dataclass
class Chunk(ParentChunk):
    content: str
    embedding: list[float]
    document_id: UUID|None
    id: UUID = field(default_factory=uuid4)


    def __str__(self):
        return self.__class__.__name__ +': '+ json.dumps({
            'id': str(self.id),
            'content': self.content,
            'embedding': f'[{self.embedding[0]}, {self.embedding[1]}, ...]',
            'document_id': str(self.document_id),
        }, ensure_ascii=False, indent=2)


@dataclass
class InternetChunk(ParentChunk):
    content: str


    def __str__(self):
        return self.__class__.__name__ +': '+ json.dumps({
            'content': self.content,
        }, ensure_ascii=False, indent=2)


@dataclass
class ChunkSimilarity:
    chunk: Chunk|InternetChunk
    question: str
    distance: float|None
    score: float|None = None


    def __str__(self):
        return self.__class__.__name__ +': '+ json.dumps({
            'question': self.question,
            'distance': self.distance,
            'score': self.score,
            'chunk': {
                'content': self.chunk.content,
            },
        }, ensure_ascii=False, indent=2)

@dataclass
class ResearchJob:
    """Trabajo de Gemini Deep Research. interaction_id es el id que devuelve Google."""
    interaction_id: str
    thread_id: str
    question: str
    agent: str
    remote_status: str
    simulated: bool = False
    report: str | None = None
    sources: list[dict] = field(default_factory=list)
    usage: dict | None = None
    error: str | None = None
    poll_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None
    completed_at: str | None = None
    # Campos locales (no se guardan en la tabla)
    reused: bool = False
    local_status: str | None = None
