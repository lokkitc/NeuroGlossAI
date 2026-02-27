"""Эндпойнты профиля пользователя.

Содержит:
- обновление языков
- экспорт данных
- сброс прогресса
- частичное обновление профиля
"""

from typing import Any
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.core.rate_limit import limiter
from app.features.users.schemas import UserResponse, UserUpdateLanguages, UserUpdate
from app.features.users.models import User
from app.features.users.service import UserService

router = APIRouter()

@router.put("/me/languages", response_model=UserResponse)
async def update_languages(
    languages: UserUpdateLanguages,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Обновление родного и целевого языков пользователя (Текущий курс).
    """
    return await UserService(db).update_languages(current_user=current_user, languages=languages)


@router.get("/me/export")
@limiter.limit("2/minute")
async def export_user_data(
    request: Request,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """Полный экспорт данных пользователя одним объектом (для отладки и бэкапа)."""
    return await UserService(db).export_user_data(current_user=current_user)

@router.post("/me/reset", response_model=UserResponse)
async def reset_progress(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Сброс контента пользователя: удаляет активные записи курса пользователя, прогресс, сгенерированные уроки и словарь.
    Не сбрасывает опыт или общую статистику геймификации (как запрошено).
    """
    return await UserService(db).reset_progress(current_user=current_user)

@router.patch("/me", response_model=UserResponse)
async def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Частичное обновление собственного профиля пользователя.
    Используйте это для настроек, информации о профиле и т.д.
    """
    user = await UserService(db).update_me(current_user=current_user, body=user_in)
    resp = UserResponse.model_validate(user)
    resp.avatar_url = UserResponse._normalize_storageapi_urls(resp.avatar_url)
    resp.thumbnail_url = UserResponse._normalize_storageapi_urls(resp.thumbnail_url)
    resp.banner_url = UserResponse._normalize_storageapi_urls(resp.banner_url)
    return resp
