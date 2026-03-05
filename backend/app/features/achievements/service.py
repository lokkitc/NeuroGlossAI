from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NeuroGlossException
from app.features.achievements.models import Achievement, UserAchievement
from app.features.achievements.repository import AchievementRepository, UserAchievementRepository
from app.features.common.db import begin_if_needed


class AchievementService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.achievements = AchievementRepository(db)
        self.user_achievements = UserAchievementRepository(db)

    async def list_achievements(self, *, skip: int, limit: int) -> list[Achievement]:
        return await self.achievements.list_active(skip=skip, limit=limit)

    async def list_my(self, *, user_id: UUID, skip: int, limit: int) -> list[UserAchievement]:
        return await self.user_achievements.list_for_user(user_id=user_id, skip=skip, limit=limit)

    async def award(
        self,
        *,
        user_id: UUID,
        slug: str,
        context: dict[str, Any] | None = None,
    ) -> UserAchievement | None:
        s = (slug or "").strip()
        if not s:
            raise NeuroGlossException(status_code=400, code="invalid_request", detail="Invalid achievement slug")

        achievement = await self.achievements.get_by_slug(slug=s)
        if achievement is None or not bool(getattr(achievement, "is_active", True)):
            raise NeuroGlossException(status_code=404, code="not_found", detail="Achievement not found")

        existing = await self.user_achievements.get_for_user_and_achievement(
            user_id=user_id,
            achievement_id=achievement.id,
        )
        if existing is not None:
            return None

        ctx = context or {}

        async with begin_if_needed(self.db):
            row = UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id,
                context=ctx,
            )
            await self.user_achievements.create(row)

        return row
