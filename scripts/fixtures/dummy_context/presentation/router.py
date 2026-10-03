from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status


from app.contexts.{entity_plural_name}.application.dtos import {EntityName}Create, {EntityName}Read, {EntityName}Update
from app.contexts.{entity_plural_name}.application.use_cases import (
    Create{EntityName},
    Delete{EntityName},
    Get{EntityName},
    List{EntityPluralName},
    Update{EntityName},
)
from app.contexts.{entity_plural_name}.infrastructure.repository import (
    SqlRelationError,
    {EntityName}Repository,
)

router = APIRouter(prefix="/{entity_plural_name}", tags=["{entity_plural_name}"])


def get_{entity_name}_repository():
    return {EntityName}Repository()


@router.get("", response_model=List[{EntityName}Read])
def list_{entity_plural_name}(repository=Depends(get_{entity_name}_repository)):
    return List{EntityPluralName}(repository).execute()


@router.post("", response_model={EntityName}Read, status_code=status.HTTP_201_CREATED)
def create_{EntityName}(payload: {EntityName}Create, repository=Depends(get_{entity_name}_repository)):
    try:
        return Create{EntityName}(repository).execute(payload.model_dump())
    except SqlRelationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{{entity_name}_id}", response_model={EntityName}Read)
def get_{entity_name}({entity_name}_id: int, repository=Depends(get_{entity_name}_repository)):
    {entity_name} = Get{EntityName}(repository).execute({entity_name}_id)
    if {entity_name} is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{EntityName} not found")
    return {entity_name}


@router.put("/{{entity_name}_id}", response_model={EntityName}Read)
def update_{entity_name}({entity_name}_id: int, payload: {EntityName}Update, repository=Depends(get_{entity_name}_repository)):
    try:
        {entity_name} = Update{EntityName}(repository).execute({entity_name}_id, payload.model_dump())
    except SqlRelationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if {entity_name} is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{EntityName} not found")
    return {entity_name}


@router.delete("/{{entity_name}_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_{entity_name}({entity_name}_id: int, repository=Depends(get_{entity_name}_repository)):
    deleted = Delete{EntityName}(repository).execute({entity_name}_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{EntityName} not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
