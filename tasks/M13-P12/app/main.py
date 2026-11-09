from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.presentation.router import router

STATIC_DIR = Path(__file__).parent / "presentation" / "static"

app = FastAPI(title="M13-P12 · Chat")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(router)
