from fastapi import FastAPI

from app.contexts.cars.presentation.router import router as cars_router
from app.contexts.users.presentation.router import router as users_router
from app.contexts.messages.presentation.router import router as messages_router

app = FastAPI(title="ThePower Course API")


@app.get("/")
def root():
    return {
        "users": {
            "list": "GET /users",
            "create": "POST /users",
            "retrieve": "GET /users/{user_id}",
            "update": "PUT /users/{user_id}",
            "delete": "DELETE /users/{user_id}",
        },
        "cars": {
            "list": "GET /cars",
            "create": "POST /cars",
            "retrieve": "GET /cars/{car_id}",
            "update": "PUT /cars/{car_id}",
            "delete": "DELETE /cars/{car_id}",
        },
    }


app.include_router(users_router)
app.include_router(cars_router)
app.include_router(messages_router)
