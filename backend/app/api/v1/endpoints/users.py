"""Эндпойнты профиля пользователя.

Содержит:
- обновление языков
- экспорт данных
- сброс прогресса
- частичное обновление профиля
"""

from typing import Any
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.core.config import settings
from app.core.exceptions import NeuroGlossException
from app.features.users.schemas import UserResponse, UserUpdateLanguages, UserUpdate
from app.features.users.models import User
from app.features.users.service import UserService

router = APIRouter()


@router.get("/me/export")
async def export_me(
    current_user: User = Depends(deps.require_subscription_feature("exports")),
) -> Any:
    if not bool(getattr(settings, "ENABLE_USER_EXPORT", False)):
        raise NeuroGlossException(status_code=403, code="feature_disabled", detail="Export is disabled")
    return jsonable_encoder(current_user)

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
