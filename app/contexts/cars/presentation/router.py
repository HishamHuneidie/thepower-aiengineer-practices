from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.contexts.cars.application.dtos import CarCreate, CarRead, CarUpdate
from app.contexts.cars.application.use_cases import (
    CreateCar,
    DeleteCar,
    GetCar,
    ListCars,
    UpdateCar,
)
from app.contexts.cars.infrastructure.postgres_repository import (
    InvalidOwnerError,
    PostgresCarRepository,
)

router = APIRouter(prefix="/cars", tags=["cars"])


def get_car_repository():
    return PostgresCarRepository()


@router.get("", response_model=List[CarRead])
def list_cars(repository=Depends(get_car_repository)):
    return ListCars(repository).execute()


@router.post("", response_model=CarRead, status_code=status.HTTP_201_CREATED)
def create_car(payload: CarCreate, repository=Depends(get_car_repository)):
    try:
        return CreateCar(repository).execute(payload.model_dump())
    except InvalidOwnerError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{car_id}", response_model=CarRead)
def get_car(car_id: int, repository=Depends(get_car_repository)):
    car = GetCar(repository).execute(car_id)
    if car is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
    return car


@router.put("/{car_id}", response_model=CarRead)
def update_car(car_id: int, payload: CarUpdate, repository=Depends(get_car_repository)):
    try:
        car = UpdateCar(repository).execute(car_id, payload.model_dump())
    except InvalidOwnerError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if car is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
    return car


@router.delete("/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_car(car_id: int, repository=Depends(get_car_repository)):
    deleted = DeleteCar(repository).execute(car_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
