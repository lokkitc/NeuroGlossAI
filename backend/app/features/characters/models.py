import uuid

from sqlalchemy import Column, DateTime, String, Boolean, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.custom_types import GUID


class Character(Base):
    __tablename__ = "characters"
    __table_args__ = (
        UniqueConstraint("owner_user_id", "slug", name="uq_character_owner_slug"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    owner_user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    slug = Column(String, nullable=False, default="")
    display_name = Column(String, nullable=False, default="")
    description = Column(String, nullable=False, default="")

    # System prompt / persona configuration
    system_prompt = Column(String, nullable=False, default="")
    style_prompt = Column(String, nullable=True)

    is_public = Column(Boolean, nullable=False, default=False)
    is_nsfw = Column(Boolean, nullable=False, default=False)

    # Optional structured settings (temperature hints, etc.)
    settings = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User")
