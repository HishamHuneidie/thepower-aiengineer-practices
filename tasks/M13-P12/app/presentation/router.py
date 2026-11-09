from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, PlainTextResponse, Response
from minio.error import S3Error

from app.application.use_cases import get_messages, send_message
from app.domain.entities import Message
from app.infrastructure.postgres_repository import PostgresMessageRepository
from app.infrastructure.files import save_file, delete_file, get_file

router = APIRouter()
repository = PostgresMessageRepository()


@router.get("/", include_in_schema=False)
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@router.post("/chat", response_class=PlainTextResponse)
def chat(
    message: str = Form(""),
    audio: UploadFile | None = File(None),
    image: UploadFile | None = File(None),
):
    if not message.strip() and audio is None and image is None:
        raise HTTPException(400, "Escribe un mensaje o adjunta un audio o una imagen")
    paths = {}
    try:
        for kind, upload in (("audio", audio), ("image", image)):
            if upload is not None:
                content = upload.file.read(10 * 1024 * 1024 + 1)
                paths[kind + "_path"] = save_file(content, upload.content_type or "", kind)
        response = send_message(Message(text=message.strip(), role="user", **paths), repository)
        return response.text
    except Exception as error:
        for path in paths.values():
            delete_file(path)
        if isinstance(error, ValueError):
            raise HTTPException(400, str(error)) from error
        raise


@router.get("/chat")
def history() -> list[Message]:
    return get_messages(repository)


@router.get("/uploads/{name}")
def attachment(name: str):
    try:
        content, mime = get_file(name)
    except S3Error as error:
        if error.code == "NoSuchKey":
            raise HTTPException(404, "Archivo no encontrado") from error
        raise
    return Response(content=content, media_type=mime)
