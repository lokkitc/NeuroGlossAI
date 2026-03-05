from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.common.db import BaseRepository
from app.features.subscriptions.models import UserSubscription, SubscriptionStatus


class UserSubscriptionRepository(BaseRepository[UserSubscription]):
    def __init__(self, db: AsyncSession):
        super().__init__(UserSubscription, db)

    async def get_latest_for_user(self, *, user_id: UUID) -> UserSubscription | None:
        res = await self.db.execute(
            select(UserSubscription)
            .where(UserSubscription.user_id == user_id)
            .order_by(UserSubscription.created_at.desc())
            .limit(1)
        )
        return res.scalars().first()

    async def get_active_for_user(self, *, user_id: UUID, now: datetime) -> UserSubscription | None:
        res = await self.db.execute(
            select(UserSubscription)
            .where(UserSubscription.user_id == user_id)
            .where(UserSubscription.status == SubscriptionStatus.active.value)
            .where((UserSubscription.expires_at.is_(None)) | (UserSubscription.expires_at > now))
            .order_by(UserSubscription.created_at.desc())
            .limit(1)
        )
        return res.scalars().first()

    async def list_for_user(self, *, user_id: UUID, skip: int, limit: int) -> list[UserSubscription]:
        res = await self.db.execute(
            select(UserSubscription)
            .where(UserSubscription.user_id == user_id)
            .order_by(UserSubscription.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(res.scalars().all())
