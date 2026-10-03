from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    question: str
    sender_id: int
    sent_at: datetime


class MessageRead(BaseModel):
    id: int
    question: str
    answer: str
    sender_id: int
    sent_at: datetime
