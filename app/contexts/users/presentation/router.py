from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.contexts.users.application.dtos import UserCreate, UserRead, UserUpdate
from app.contexts.users.application.use_cases import (
    CreateUser,
    DeleteUser,
    GetUser,
    ListUsers,
    UpdateUser,
)
from app.contexts.users.infrastructure.postgres_repository import PostgresUserRepository

router = APIRouter(prefix="/users", tags=["users"])


def get_user_repository():
    return PostgresUserRepository()


@router.get("", response_model=List[UserRead])
def list_users(repository=Depends(get_user_repository)):
    return ListUsers(repository).execute()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, repository=Depends(get_user_repository)):
    return CreateUser(repository).execute(payload.model_dump())


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, repository=Depends(get_user_repository)):
    user = GetUser(repository).execute(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, repository=Depends(get_user_repository)):
    user = UpdateUser(repository).execute(user_id, payload.model_dump())
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, repository=Depends(get_user_repository)):
    deleted = DeleteUser(repository).execute(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
