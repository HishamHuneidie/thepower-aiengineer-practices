from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from app.application.use_cases import get_messages, send_message
from app.domain.entities import Message
from app.infrastructure.postgres_repository import PostgresMessageRepository

router = APIRouter()
repository = PostgresMessageRepository()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


@router.get("/", include_in_schema=False)
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@router.post("/chat", response_class=PlainTextResponse)
def chat(request: ChatRequest):
    message = Message(text=request.message, role="user")
    response = send_message(message, repository)
    return response.text


@router.get("/chat")
def history() -> list[Message]:
    return get_messages(repository)
