import uuid

from sqlalchemy import (
    Column,
    DateTime,
    String,
    Boolean,
    Integer,
    JSON,
    ForeignKey,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.custom_types import GUID

from app.features.memory.models import MemoryItem


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    owner_user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # For 1:1 sessions
    character_id = Column(GUID, ForeignKey("characters.id", ondelete="SET NULL"), nullable=True)

    # For rooms
    room_id = Column(GUID, ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True)

    # Optional binding to legacy course enrollment and active level
    enrollment_id = Column(GUID, ForeignKey("enrollments.id", ondelete="SET NULL"), nullable=True)
    active_level_template_id = Column(GUID, ForeignKey("course_level_templates.id", ondelete="SET NULL"), nullable=True)

    title = Column(String, nullable=False, default="")

    is_archived = Column(Boolean, nullable=False, default=False)

    # Rolling state for context building
    last_summary_at_turn = Column(Integer, nullable=False, default=0)

    # Auto-learning cadence state (turn_index of last generated lesson)
    last_learning_lesson_at_turn = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User")
    character = relationship("Character")
    room = relationship("Room")

    enrollment = relationship("Enrollment")
    active_level_template = relationship("CourseLevelTemplate")

    turns = relationship(
        "ChatTurn",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatTurn.turn_index.asc()",
    )

    summaries = relationship(
        "ChatSessionSummary",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatSessionSummary.created_at.desc()",
    )


class ChatTurn(Base):
    __tablename__ = "chat_turns"
    __table_args__ = (
        UniqueConstraint("session_id", "turn_index", name="uq_chat_turn_session_index"),
        Index("ix_chat_turns_session_created", "session_id", "created_at"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    session_id = Column(GUID, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)

    # Monotonic increasing index starting from 1
    turn_index = Column(Integer, nullable=False)

    # 'user' | 'assistant' | 'system' | 'director'
    role = Column(String, nullable=False, default="user")

    # If this message is spoken by a character in a room
    character_id = Column(GUID, ForeignKey("characters.id", ondelete="SET NULL"), nullable=True)

    content = Column(Text, nullable=False, default="")

    # Diagnostics from the model (provider/model/quality etc.)
    meta = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ChatSession", back_populates="turns")
    character = relationship("Character")


class ChatSessionSummary(Base):
    __tablename__ = "chat_session_summaries"
    __table_args__ = (Index("ix_chat_summary_session_created", "session_id", "created_at"),)

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    session_id = Column(GUID, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)

    # Summary covers turns up to this index
    up_to_turn_index = Column(Integer, nullable=False)

    content = Column(Text, nullable=False, default="")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ChatSession", back_populates="summaries")


class ModerationEvent(Base):
    __tablename__ = "moderation_events"
    __table_args__ = (
        Index("ix_moderation_owner_created", "owner_user_id", "created_at"),
        Index("ix_moderation_session_created", "session_id", "created_at"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    owner_user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    session_id = Column(GUID, ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True)
    turn_id = Column(GUID, ForeignKey("chat_turns.id", ondelete="SET NULL"), nullable=True)

    event_type = Column(String, nullable=False, default="")

    # 'allow' | 'block' | 'filter'
    decision = Column(String, nullable=False, default="allow")

    # Structured payload: categories, model output, etc.
    details = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User")
    session = relationship("ChatSession")
    turn = relationship("ChatTurn")
