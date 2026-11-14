from fastapi import FastAPI

from app.presentation.router import router

app = FastAPI(title="M17-P16 · Chat")
app.include_router(router)
