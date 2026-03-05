from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel


class AchievementResponse(BaseModel):
    id: UUID
    slug: str
    title: str
    description: str
    icon: str | None = None
    is_active: bool
    created_at: Any | None = None

    class Config:
        from_attributes = True


class UserAchievementResponse(BaseModel):
    id: UUID
    user_id: UUID
    achievement_id: UUID
    earned_at: Any | None = None
    context: dict[str, Any]

    class Config:
        from_attributes = True


class AdminAwardAchievementRequest(BaseModel):
    user_id: UUID
    slug: str
    context: dict[str, Any] = {}
