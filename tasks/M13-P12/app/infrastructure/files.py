import os
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from minio import Minio
from minio.error import S3Error

client = Minio(
    os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=os.environ["MINIO_ACCESS_KEY"],
    secret_key=os.environ["MINIO_SECRET_KEY"],
    secure=False,
)
BUCKET = os.getenv("MINIO_BUCKET", "chat-files")
FILE_TYPES = {
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/mp4": ".m4a",
    "audio/wav": ".wav",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}


def initialize_storage() -> None:
    if not client.bucket_exists(BUCKET):
        client.make_bucket(BUCKET)
    # Conserva los adjuntos locales anteriores sin cambiar sus referencias.
    for path in Path("legacy_uploads").glob("*"):
        if not path.is_file():
            continue
        try:
            client.stat_object(BUCKET, path.name)
        except S3Error as error:
            if error.code != "NoSuchKey":
                raise
            mime = next((mime for mime, suffix in FILE_TYPES.items() if suffix == path.suffix), "application/octet-stream")
            client.fput_object(BUCKET, path.name, str(path), content_type=mime)
            print(f"Adjunto anterior copiado a MinIO: {path.name}", flush=True)


def save_file(content: bytes, content_type: str, kind: str) -> str:
    mime = content_type.split(";")[0].strip()
    if mime not in FILE_TYPES or not mime.startswith(kind + "/"):
        raise ValueError(f"Formato de {kind} no admitido")
    limit = 5 * 1024 * 1024 if kind == "image" else 10 * 1024 * 1024
    if not content or len(content) > limit:
        raise ValueError(f"El archivo de {kind} está vacío o supera {limit // 1024 // 1024} MB")
    name = str(uuid4()) + FILE_TYPES[mime]
    client.put_object(BUCKET, name, BytesIO(content), len(content), content_type=mime)
    return "/uploads/" + name


def delete_file(path: str) -> None:
    client.remove_object(BUCKET, Path(path).name)


def get_file(name: str) -> tuple[bytes, str]:
    response = client.get_object(BUCKET, name)
    try:
        return response.read(), response.headers.get("Content-Type", "application/octet-stream")
    finally:
        response.close()
        response.release_conn()
