import uuid

from sqlalchemy import Column, DateTime, String, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.custom_types import GUID


class Theme(Base):
    __tablename__ = "themes"
    __table_args__ = (
        Index("ix_themes_type_public", "theme_type", "is_public"),
        Index("ix_themes_owner", "owner_user_id"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    theme_type = Column(String, nullable=False, default="USER")

    slug = Column(String, nullable=False, default="")
    display_name = Column(String, nullable=False, default="")
    description = Column(String, nullable=False, default="")

    is_public = Column(Boolean, nullable=False, default=False)

    owner_user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Extensible token payloads.
    # Expected shape (recommended):
    # {"version": 1, "palette": {...}, "typography": {...}, "components": {...}, "extensions": {...}}
    light_tokens = Column(JSON, nullable=True)
    dark_tokens = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User")
