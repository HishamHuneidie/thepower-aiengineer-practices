import re
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse, Response
from minio.error import S3Error

from app.application.use_cases import get_messages, get_state, send_message
from app.domain.entities import Message
from app.infrastructure.postgres_repository import PostgresMessageRepository
from app.infrastructure.files import save_file, delete_file, get_file

router = APIRouter()
repository = PostgresMessageRepository()
THREAD_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def validate_thread_id(thread_id: str) -> str:
    if not THREAD_ID_PATTERN.fullmatch(thread_id):
        raise HTTPException(400, "thread_id no válido: usa letras, números, - o _ (máximo 64)")
    return thread_id


@router.get("/", include_in_schema=False)
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@router.post("/chat")
def chat(
    message: str = Form(""),
    thread_id: str = Form("default"),
    speak: bool = Form(False),
    audio: UploadFile | None = File(None),
    image: UploadFile | None = File(None),
):
    thread_id = validate_thread_id(thread_id)
    if not message.strip() and audio is None and image is None:
        raise HTTPException(400, "Escribe un mensaje o adjunta un audio o una imagen")
    paths = {}
    try:
        for kind, upload in (("audio", audio), ("image", image)):
            if upload is not None:
                content = upload.file.read(10 * 1024 * 1024 + 1)
                paths[kind + "_path"] = save_file(content, upload.content_type or "", kind)

        response = send_message(
            Message(text=message.strip(), role="user", thread_id=thread_id, **paths),
            repository,
            want_speech=speak,
        )

        return response
    except Exception as error:
        for path in paths.values():
            delete_file(path)
        if isinstance(error, ValueError):
            raise HTTPException(400, str(error)) from error
        raise


@router.get("/chat")
def history(thread_id: str = Query("default")) -> list[Message]:
    return get_messages(repository, validate_thread_id(thread_id))


@router.get("/threads/{thread_id}/state")
def thread_state(thread_id: str) -> dict:
    """Estado del checkpointer para un hilo: sirve como evidencia de memoria separada."""
    return get_state(validate_thread_id(thread_id))


@router.get("/uploads/{name}")
def attachment(name: str):
    try:
        content, mime = get_file(name)
    except S3Error as error:
        if error.code == "NoSuchKey":
            raise HTTPException(404, "Archivo no encontrado") from error
        raise
    return Response(content=content, media_type=mime)
