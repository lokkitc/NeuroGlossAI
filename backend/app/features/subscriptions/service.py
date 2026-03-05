from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException, NeuroGlossException
from app.features.common.db import begin_if_needed
from app.features.subscriptions.models import UserSubscription, SubscriptionStatus
from app.features.subscriptions.repository import UserSubscriptionRepository
from app.features.users.models import User


class SubscriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.subscriptions = UserSubscriptionRepository(db)

    async def get_active_subscription(self, *, user_id: UUID, now: datetime | None = None) -> UserSubscription | None:
        now = now or datetime.utcnow()
        return await self.subscriptions.get_active_for_user(user_id=user_id, now=now)

    async def get_subscription_status(self, *, user_id: UUID) -> tuple[str, Any | None, bool]:
        now = datetime.utcnow()
        sub = await self.get_active_subscription(user_id=user_id, now=now)
        if sub is None:
            return "free", None, False
        tier = (sub.tier or "free").strip().lower() or "free"
        expires_at = sub.expires_at
        is_active = tier != "free" and (expires_at is None or expires_at > now)
        return tier, expires_at, is_active

    async def cancel_subscription(self, *, user: User, cancel_now: bool) -> tuple[str, Any | None, bool]:
        now = datetime.utcnow()
        active = await self.get_active_subscription(user_id=user.id, now=now)

        async with begin_if_needed(self.db):
            if active is not None:
                active.status = SubscriptionStatus.canceled.value
                active.ended_at = now if cancel_now else (active.expires_at or now)
                self.db.add(active)

        return await self.get_subscription_status(user_id=user.id)

    async def admin_set_subscription(
        self,
        *,
        admin_user: User,
        user_id: str,
        tier: str,
        expires_at: datetime | None,
    ) -> tuple[str, Any | None, bool]:
        try:
            uid = UUID(str(user_id))
        except Exception:
            raise NeuroGlossException(status_code=400, code="invalid_request", detail="Invalid user_id")

        user = await self.db.get(User, uid)
        if user is None:
            raise EntityNotFoundException("User", uid)

        t = (tier or "").strip().lower() or "free"
        if t not in {"free", "plus", "pro"}:
            raise NeuroGlossException(status_code=400, code="invalid_request", detail="Invalid tier")

        now = datetime.utcnow()

        async with begin_if_needed(self.db):
            if t == "free":
                return await self.get_subscription_status(user_id=user.id)

            prev = await self.get_active_subscription(user_id=user.id, now=now)
            if prev is not None:
                prev.status = SubscriptionStatus.superseded.value
                prev.ended_at = now
                self.db.add(prev)

            grant = UserSubscription(
                user_id=user.id,
                tier=t,
                status=SubscriptionStatus.active.value,
                started_at=now,
                expires_at=expires_at,
                ended_at=None,
                provider="admin",
                external_customer_id=None,
            )
            await self.subscriptions.create(grant)

        return await self.get_subscription_status(user_id=user.id)

    async def list_history(self, *, user_id: UUID, skip: int, limit: int) -> list[UserSubscription]:
        return await self.subscriptions.list_for_user(user_id=user_id, skip=skip, limit=limit)
