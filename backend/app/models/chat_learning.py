import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.custom_types import GUID


class ChatLearningLesson(Base):
    __tablename__ = "chat_learning_lessons"
    __table_args__ = (
        Index("ix_chat_learning_session_created", "chat_session_id", "created_at"),
        Index("ix_chat_learning_owner_created", "owner_user_id", "created_at"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    owner_user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    chat_session_id = Column(GUID, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)

    source_turn_from = Column(Integer, nullable=False, default=0)
    source_turn_to = Column(Integer, nullable=False, default=0)

    title = Column(String, nullable=False, default="")
    topic_snapshot = Column(String, nullable=True)

    content_text = Column(Text, nullable=False, default="")
    vocabulary = Column(JSON, nullable=True)
    exercises = Column(JSON, nullable=True)

    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    quality_status = Column(String, nullable=True)

    raw_model_output = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User")
    chat_session = relationship("ChatSession")
