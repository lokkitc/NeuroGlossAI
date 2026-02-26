from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api import deps
from app.core.exceptions import EntityNotFoundException, NeuroGlossException
from app.features.users.models import User
from app.features.characters.repository import CharacterRepository
from app.features.themes.repository import ThemeRepository
from app.features.themes.models import Theme
from app.features.themes.schemas import ThemeCreate, ThemeOut, SelectThemeRequest


router = APIRouter()


@router.get("/available", response_model=list[ThemeOut])
async def list_available_themes(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
    theme_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    return await ThemeRepository(db).list_available(user_id=current_user.id, theme_type=theme_type, skip=skip, limit=limit)


@router.post("/me", response_model=ThemeOut)
async def create_my_theme(
    body: ThemeCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    repo = ThemeRepository(db)
    existing = await repo.get_by_owner_and_slug(owner_user_id=current_user.id, slug=body.slug)
    if existing is not None:
        raise NeuroGlossException(status_code=409, code="conflict", detail="Theme slug already exists")

    row = Theme(
        theme_type=body.theme_type.value,
        slug=body.slug,
        display_name=body.display_name,
        description=body.description or "",
        is_public=bool(body.is_public),
        owner_user_id=current_user.id,
        light_tokens=body.light_tokens.model_dump() if body.light_tokens is not None else None,
        dark_tokens=body.dark_tokens.model_dump() if body.dark_tokens is not None else None,
    )
    return await repo.create(row, commit=True)


@router.post("/me/select", response_model=dict)
async def select_my_ui_theme(
    body: SelectThemeRequest,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    theme = await ThemeRepository(db).get_available(theme_id=body.theme_id, user_id=current_user.id)
    if theme is None:
        raise EntityNotFoundException("Theme", body.theme_id)

    current_user.selected_theme_id = theme.id
    await db.commit()
    await db.refresh(current_user)
    return {"status": "ok", "selected_theme_id": str(current_user.selected_theme_id)}


@router.post("/characters/{character_id}/select-chat", response_model=dict)
async def select_character_chat_theme(
    character_id: UUID,
    body: SelectThemeRequest,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    ch_repo = CharacterRepository(db)
    ch = await ch_repo.get(character_id)
    if not ch or ch.owner_user_id != current_user.id:
        raise EntityNotFoundException("Character", character_id)

    theme = await ThemeRepository(db).get_available(theme_id=body.theme_id, user_id=current_user.id)
    if theme is None:
        raise EntityNotFoundException("Theme", body.theme_id)

    ch.chat_theme_id = theme.id
    await db.commit()
    await db.refresh(ch)

    return {"status": "ok", "character_id": str(ch.id), "chat_theme_id": str(ch.chat_theme_id)}
