from __future__ import annotations

from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.common.db import begin_if_needed
from app.core.exceptions import EntityNotFoundException, NeuroGlossException
from app.features.users.models import User
from app.features.users.schemas import UserUpdateLanguages, UserUpdate

from datetime import datetime
from uuid import UUID


def _normalize_storageapi_url(value: Any) -> Any:
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    url = value.strip()
    if not url:
        return None
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        host = parsed.netloc
        if not host.endswith("storageapi.dev"):
            return url
        parts = host.split(".")
        if len(parts) < 3:
            return url
        bucket = parts[0]
        base_host = ".".join(parts[1:])
        path = parsed.path or ""
        if not path.startswith("/"):
            path = f"/{path}"
        if path.startswith(f"/{bucket}/"):
            return url
        fixed = f"{parsed.scheme or 'https'}://{base_host}/{bucket}{path}"
        if parsed.query:
            fixed = f"{fixed}?{parsed.query}"
        return fixed
    except Exception:
        return url


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_languages(self, *, current_user: User, languages: UserUpdateLanguages) -> User:
        async with begin_if_needed(self.db):
            current_user.target_language = languages.target_language
            current_user.native_language = languages.native_language
            self.db.add(current_user)

        await self.db.refresh(current_user)
        return current_user

    async def get_subscription_status(self, *, current_user: User) -> tuple[str, datetime | None, bool]:
        tier = (getattr(current_user, "subscription_tier", None) or "free").strip() or "free"
        expires_at = getattr(current_user, "subscription_expires_at", None)
        is_active = tier != "free" and (expires_at is None or expires_at > datetime.utcnow())
        return tier, expires_at, is_active

    async def cancel_subscription(self, *, current_user: User, cancel_now: bool) -> tuple[str, datetime | None, bool]:
        async with begin_if_needed(self.db):
            current_user.subscription_tier = "free"
            current_user.subscription_expires_at = None
            self.db.add(current_user)
        await self.db.refresh(current_user)
        return await self.get_subscription_status(current_user=current_user)

    async def admin_set_subscription(
        self,
        *,
        admin_user: User,
        user_id: str,
        tier: str,
        expires_at: datetime | None,
    ) -> tuple[str, datetime | None, bool]:
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

        async with begin_if_needed(self.db):
            user.subscription_tier = t
            user.subscription_expires_at = expires_at
            self.db.add(user)

        await self.db.refresh(user)
        return await self.get_subscription_status(current_user=user)

    async def update_me(self, *, current_user: User, body: UserUpdate) -> User:
        update_data = body.model_dump(exclude_unset=True)

        if "avatar_url" in update_data:
            update_data["avatar_url"] = _normalize_storageapi_url(update_data.get("avatar_url"))
        if "thumbnail_url" in update_data:
            update_data["thumbnail_url"] = _normalize_storageapi_url(update_data.get("thumbnail_url"))
        if "banner_url" in update_data:
            update_data["banner_url"] = _normalize_storageapi_url(update_data.get("banner_url"))

        async with begin_if_needed(self.db):
            for field, value in update_data.items():
                if hasattr(current_user, field):
                    setattr(current_user, field, value)
            self.db.add(current_user)

        await self.db.refresh(current_user)
        return current_user
