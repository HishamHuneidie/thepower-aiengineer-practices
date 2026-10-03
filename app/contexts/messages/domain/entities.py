from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class Message:
    id: int
    question: str
    answer: str
    sender_id: int
    sent_at: datetime
