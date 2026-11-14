from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.application.use_cases import reply

from random import choice
import secrets

router = APIRouter()


@router.get("/health")
def index():
    return JSONResponse(status_code=200, content={"message": "OK"})


@router.post("/chat")
def chat():
    optional_messages: list[str] = [
        'Artificial Intelligence and Society',
        'Future of Technology',
        'Personal Growth and Development',
        'Science and Space Exploration',
        'Health and Healthy Habits',
        'Travel and Cultural Experiences',
        'Business and Entrepreneurship',
    ]

    code = secrets.token_hex(3)
    selected = f'[{code}] ' + choice(optional_messages)

    response = reply(selected)

    return JSONResponse(status_code=200, content={"message": f"LLM replies -> '{response}'"})
