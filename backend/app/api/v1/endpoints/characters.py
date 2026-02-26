from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api import deps
from app.features.users.models import User
from app.features.characters.service import CharacterService
from app.features.characters.schemas import CharacterCreate, CharacterOut, CharacterUpdate


router = APIRouter()


@router.get("/me", response_model=list[CharacterOut])
async def list_my_characters(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    return await CharacterService(db).list_for_owner(owner_user_id=current_user.id, skip=skip, limit=limit)


@router.get("/public", response_model=list[CharacterOut])
async def list_public_characters(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    nsfw: bool | None = Query(None),
) -> Any:
    return await CharacterService(db).list_public(skip=skip, limit=limit, nsfw=nsfw)


@router.post("/me", response_model=CharacterOut)
async def create_character(
    body: CharacterCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await CharacterService(db).create_character(owner_user_id=current_user.id, body=body)


@router.patch("/me/{character_id}", response_model=CharacterOut)
async def update_character(
    character_id: UUID,
    body: CharacterUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await CharacterService(db).update_character(character_id=character_id, owner_user_id=current_user.id, body=body)


@router.delete("/me/{character_id}")
async def delete_character(
    character_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await CharacterService(db).delete_character(character_id=character_id, owner_user_id=current_user.id)
