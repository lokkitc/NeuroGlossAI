from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api import deps
from app.features.users.models import User
from app.features.characters.models import Character
from app.features.characters.repository import CharacterRepository
from app.features.characters.schemas import CharacterCreate, CharacterOut, CharacterUpdate
from app.core.exceptions import EntityNotFoundException


router = APIRouter()


@router.get("/me", response_model=list[CharacterOut])
async def list_my_characters(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    repo = CharacterRepository(db)
    return await repo.list_for_owner(current_user.id, skip=skip, limit=limit)


@router.get("/public", response_model=list[CharacterOut])
async def list_public_characters(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    nsfw: bool | None = Query(None),
) -> Any:
    repo = CharacterRepository(db)
    return await repo.list_public(skip=skip, limit=limit, nsfw=nsfw)


@router.post("/me", response_model=CharacterOut)
async def create_character(
    body: CharacterCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    repo = CharacterRepository(db)
    row = Character(
        owner_user_id=current_user.id,
        slug=body.slug,
        display_name=body.display_name,
        description=body.description or "",
        system_prompt=body.system_prompt,
        style_prompt=body.style_prompt,

        avatar_url=body.avatar_url,
        thumbnail_url=body.thumbnail_url,
        banner_url=body.banner_url,
        greeting=body.greeting,
        tags=body.tags,
        voice_provider=body.voice_provider,
        voice_id=body.voice_id,
        voice_settings=body.voice_settings,
        chat_settings=body.chat_settings,

        chat_theme_id=body.chat_theme_id,

        is_public=bool(body.is_public),
        is_nsfw=bool(body.is_nsfw),
        settings=body.settings,
    )
    return await repo.create(row, commit=True)


@router.patch("/me/{character_id}", response_model=CharacterOut)
async def update_character(
    character_id: UUID,
    body: CharacterUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    repo = CharacterRepository(db)
    ch = await repo.get(character_id)
    if not ch or ch.owner_user_id != current_user.id:
        raise EntityNotFoundException("Character", character_id)
    return await repo.update(ch, body, commit=True)


@router.delete("/me/{character_id}")
async def delete_character(
    character_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    repo = CharacterRepository(db)
    ch = await repo.get(character_id)
    if not ch or ch.owner_user_id != current_user.id:
        raise EntityNotFoundException("Character", character_id)
    await repo.delete(character_id, commit=True)
    return {"status": "ok"}
