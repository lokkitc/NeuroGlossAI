from typing import Any
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api import deps
from app.features.users.models import User
from app.features.subscriptions.service import SubscriptionService


router = APIRouter()


class SubscriptionStatusResponse(BaseModel):
    tier: str
    expires_at: Any | None = None
    is_active: bool
    features: dict[str, bool]


class SubscriptionCancelRequest(BaseModel):
    cancel_now: bool = True


class AdminSetSubscriptionRequest(BaseModel):
    user_id: str
    tier: str
    expires_at: Any | None = None


class SubscriptionHistoryItem(BaseModel):
    id: UUID
    user_id: UUID
    tier: str
    status: str
    started_at: datetime | None = None
    expires_at: datetime | None = None
    ended_at: datetime | None = None
    provider: str | None = None
    external_customer_id: str | None = None
    external_subscription_id: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


def _features(tier: str) -> dict[str, bool]:
    return deps.subscription_features_for_tier(tier)


@router.get("/me", response_model=SubscriptionStatusResponse)
async def get_my_subscription(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    tier, expires_at, is_active = await SubscriptionService(db).get_subscription_status(user_id=current_user.id)
    return SubscriptionStatusResponse(
        tier=tier,
        expires_at=expires_at,
        is_active=is_active,
        features=deps.subscription_features_for_tier(tier),
    )


@router.post("/cancel", response_model=SubscriptionStatusResponse)
async def cancel_my_subscription(
    body: SubscriptionCancelRequest,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    tier, expires_at, is_active = await SubscriptionService(db).cancel_subscription(
        user=current_user,
        cancel_now=body.cancel_now,
    )
    return SubscriptionStatusResponse(
        tier=tier,
        expires_at=expires_at,
        is_active=is_active,
        features=_features(tier),
    )


@router.get("/history", response_model=list[SubscriptionHistoryItem])
async def my_subscription_history(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    items = await SubscriptionService(db).list_history(user_id=current_user.id, skip=skip, limit=limit)
    return [SubscriptionHistoryItem.model_validate(x, from_attributes=True) for x in items]


@router.get("/admin/history/{user_id}", response_model=list[SubscriptionHistoryItem])
async def admin_subscription_history(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.require_admin),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    items = await SubscriptionService(db).list_history(user_id=user_id, skip=skip, limit=limit)
    return [SubscriptionHistoryItem.model_validate(x, from_attributes=True) for x in items]


@router.post("/admin/set", response_model=SubscriptionStatusResponse)
async def admin_set_subscription(
    body: AdminSetSubscriptionRequest,
    current_user: User = Depends(deps.require_admin),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    tier, expires_at, is_active = await SubscriptionService(db).admin_set_subscription(
        admin_user=current_user,
        user_id=body.user_id,
        tier=body.tier,
        expires_at=body.expires_at,
    )
    return SubscriptionStatusResponse(
        tier=tier,
        expires_at=expires_at,
        is_active=is_active,
        features=_features(tier),
    )
