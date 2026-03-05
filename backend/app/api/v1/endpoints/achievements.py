from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.features.achievements.schemas import (
    AchievementResponse,
    UserAchievementResponse,
    AdminAwardAchievementRequest,
)
from app.features.achievements.service import AchievementService
from app.features.users.models import User


router = APIRouter()


@router.get("/", response_model=list[AchievementResponse])
async def list_achievements(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await AchievementService(db).list_achievements(skip=skip, limit=limit)


@router.get("/me", response_model=list[UserAchievementResponse])
async def my_achievements(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await AchievementService(db).list_my(user_id=current_user.id, skip=skip, limit=limit)


@router.post("/admin/award", response_model=UserAchievementResponse | None)
async def admin_award_achievement(
    body: AdminAwardAchievementRequest,
    current_user: User = Depends(deps.require_admin),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await AchievementService(db).award(user_id=body.user_id, slug=body.slug, context=body.context)
