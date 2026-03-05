from __future__ import annotations

from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.common.db import begin_if_needed
from app.core.exceptions import EntityNotFoundException, NeuroGlossException
from app.features.users.models import User
from app.features.users.schemas import UserUpdateLanguages, UserUpdate

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
