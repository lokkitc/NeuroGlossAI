from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.common.db import BaseRepository
from app.features.achievements.models import Achievement, UserAchievement


class AchievementRepository(BaseRepository[Achievement]):
    def __init__(self, db: AsyncSession):
        super().__init__(Achievement, db)

    async def get_by_slug(self, *, slug: str) -> Achievement | None:
        res = await self.db.execute(select(Achievement).where(Achievement.slug == slug))
        return res.scalars().first()

    async def list_active(self, *, skip: int, limit: int) -> list[Achievement]:
        res = await self.db.execute(
            select(Achievement)
            .where(Achievement.is_active.is_(True))
            .order_by(Achievement.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(res.scalars().all())


class UserAchievementRepository(BaseRepository[UserAchievement]):
    def __init__(self, db: AsyncSession):
        super().__init__(UserAchievement, db)

    async def get_for_user_and_achievement(
        self,
        *,
        user_id: UUID,
        achievement_id: UUID,
    ) -> UserAchievement | None:
        res = await self.db.execute(
            select(UserAchievement)
            .where(UserAchievement.user_id == user_id)
            .where(UserAchievement.achievement_id == achievement_id)
            .limit(1)
        )
        return res.scalars().first()

    async def list_for_user(self, *, user_id: UUID, skip: int, limit: int) -> list[UserAchievement]:
        res = await self.db.execute(
            select(UserAchievement)
            .where(UserAchievement.user_id == user_id)
            .order_by(UserAchievement.earned_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(res.scalars().all())
