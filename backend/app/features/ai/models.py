import uuid

from sqlalchemy import Column, DateTime, Integer, JSON, String, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.custom_types import GUID


class LLMCacheEntry(Base):
    __tablename__ = "llm_cache_entries"
    __table_args__ = (
        UniqueConstraint("prompt_hash", name="uq_llm_cache_prompt_hash"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    prompt_hash = Column(String, nullable=False)
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)

    prompt = Column(String, nullable=False, default="")
    response_json = Column(JSON, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AIGenerationEvent(Base):
    __tablename__ = "ai_generation_events"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    enrollment_id = Column(GUID, ForeignKey("enrollments.id", ondelete="SET NULL"), nullable=True)
    generated_lesson_id = Column(GUID, ForeignKey("generated_lessons.id", ondelete="SET NULL"), nullable=True)

    operation = Column(String, nullable=False, default="")
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    generation_mode = Column(String, nullable=True)

    latency_ms = Column(Integer, nullable=True)
    repair_count = Column(Integer, nullable=True)
    quality_status = Column(String, nullable=True)

    error_codes = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    enrollment = relationship("Enrollment")
    generated_lesson = relationship("GeneratedLesson")
