import uuid

from sqlalchemy import Column, DateTime, String, Boolean, Integer, JSON, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.custom_types import GUID


class MemoryItem(Base):
    __tablename__ = "memory_items"
    __table_args__ = (
        Index("ix_memory_owner_created", "owner_user_id", "created_at"),
        Index("ix_memory_owner_character", "owner_user_id", "character_id"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    owner_user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Optional scope: per character or per room. If none -> global for user.
    character_id = Column(GUID, ForeignKey("characters.id", ondelete="CASCADE"), nullable=True)
    room_id = Column(GUID, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=True)

    # Optional origin session
    session_id = Column(GUID, ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True)

    # Visible memory fields
    title = Column(String, nullable=False, default="")
    content = Column(Text, nullable=False, default="")

    # If pinned: always included in context
    is_pinned = Column(Boolean, nullable=False, default=False)

    # If disabled: memory is preserved but not used for generation
    is_enabled = Column(Boolean, nullable=False, default=True)

    # Optional tags, importance, etc.
    tags = Column(JSON, nullable=True)
    importance = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User")
    character = relationship("Character")
    room = relationship("Room")
    session = relationship("ChatSession")
