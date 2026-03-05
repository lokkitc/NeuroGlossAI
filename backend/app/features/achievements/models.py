from __future__ import annotations

import uuid

from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.custom_types import GUID


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    slug = Column(String, nullable=False, unique=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False, default="")
    icon = Column(String, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_achievements = relationship(
        "UserAchievement",
        back_populates="achievement",
        cascade="all, delete-orphan",
    )


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id = Column(
        GUID,
        ForeignKey("achievements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    earned_at = Column(DateTime(timezone=True), server_default=func.now())
    context = Column(JSON, nullable=False, default=dict)

    achievement = relationship("Achievement", back_populates="user_achievements")
