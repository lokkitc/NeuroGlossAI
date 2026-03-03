from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.features.users.models import User
from app.features.users.service import UserService


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


def _features(tier: str) -> dict[str, bool]:
    return deps.subscription_features_for_tier(tier)


@router.get("/me", response_model=SubscriptionStatusResponse)
async def get_my_subscription(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    tier, expires_at, is_active = await UserService(db).get_subscription_status(current_user=current_user)
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
    tier, expires_at, is_active = await UserService(db).cancel_subscription(current_user=current_user, cancel_now=body.cancel_now)
    return SubscriptionStatusResponse(
        tier=tier,
        expires_at=expires_at,
        is_active=is_active,
        features=_features(tier),
    )


@router.post("/admin/set", response_model=SubscriptionStatusResponse)
async def admin_set_subscription(
    body: AdminSetSubscriptionRequest,
    current_user: User = Depends(deps.require_admin),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    tier, expires_at, is_active = await UserService(db).admin_set_subscription(
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
