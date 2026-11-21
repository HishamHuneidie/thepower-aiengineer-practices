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


@app.middleware("http")
async def no_cache_frontend(request, call_next):
    # Evita que el navegador mezcle un index.html nuevo con un chat.js antiguo (o al revés).
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(router)
