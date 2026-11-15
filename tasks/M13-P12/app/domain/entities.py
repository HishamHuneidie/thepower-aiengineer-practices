from dataclasses import dataclass, field
from io import BytesIO
from typing import Literal
from uuid import UUID, uuid4


class Audio(BytesIO):
    file_type = 'audio'


class Image(BytesIO):
    file_type = 'image'


@dataclass
class Message:
    role: Literal["user", "assistant"]
    id: UUID = field(default_factory=uuid4)
    text: str | None = None
    audio_path: str | None = None
    image_path: str | None = None
    audio_transcript: str | None = None
    image_transcript: str | None = None
    response_in_audio_path: str | None = None