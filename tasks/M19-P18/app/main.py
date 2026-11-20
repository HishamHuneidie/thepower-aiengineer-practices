from fastapi import FastAPI

from app.presentation.router import router

app = FastAPI(title="M19-P18 · Github actions and testing")
app.include_router(router)
