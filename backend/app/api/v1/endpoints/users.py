"""Эндпойнты профиля пользователя.

Содержит:
- обновление языков
- экспорт данных
- сброс прогресса
- частичное обновление профиля
"""

from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
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
