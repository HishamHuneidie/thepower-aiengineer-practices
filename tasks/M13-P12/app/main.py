from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.presentation.router import router
from app.infrastructure.files import initialize_storage

STATIC_DIR = Path(__file__).parent / "presentation" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_storage()
    yield


app = FastAPI(title="M13-P12 · Chat", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(router)
