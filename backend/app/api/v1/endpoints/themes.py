from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api import deps
from app.features.users.models import User
from app.features.themes.service import ThemeService
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
    return await ThemeService(db).list_available(user_id=current_user.id, theme_type=theme_type, skip=skip, limit=limit)


@router.post("/me", response_model=ThemeOut)
async def create_my_theme(
    body: ThemeCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await ThemeService(db).create_my_theme(user_id=current_user.id, body=body)


@router.post("/me/select", response_model=dict)
async def select_my_ui_theme(
    body: SelectThemeRequest,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await ThemeService(db).select_my_ui_theme_for_user(current_user=current_user, theme_id=body.theme_id)


@router.post("/characters/{character_id}/select-chat", response_model=dict)
async def select_character_chat_theme(
    character_id: UUID,
    body: SelectThemeRequest,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await ThemeService(db).select_character_chat_theme(
        owner_user_id=current_user.id,
        character_id=character_id,
        theme_id=body.theme_id,
    )
