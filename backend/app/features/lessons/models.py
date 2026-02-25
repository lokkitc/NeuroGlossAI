import uuid

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, UniqueConstraint, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.custom_types import GUID


class GeneratedLesson(Base):
    __tablename__ = "generated_lessons"
    __table_args__ = (
        UniqueConstraint("enrollment_id", "level_template_id", name="uq_generated_lesson_enrollment_level"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    enrollment_id = Column(GUID, ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False)
    level_template_id = Column(GUID, ForeignKey("course_level_templates.id", ondelete="RESTRICT"), nullable=False)

    topic_snapshot = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)

    input_context = Column(JSON, nullable=True)
    raw_model_output = Column(JSON, nullable=True)
    validation_errors = Column(JSON, nullable=True)
    repair_count = Column(Integer, nullable=False, default=0)

    content_text = Column(String, nullable=False, default="")
    exercises = Column(JSON, nullable=True)

    quality_status = Column(String, nullable=False, default="ok")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    enrollment = relationship("Enrollment", back_populates="generated_lessons")
    level_template = relationship("CourseLevelTemplate", back_populates="generated_lessons")
    vocabulary_items = relationship(
        "GeneratedVocabularyItem",
        back_populates="generated_lesson",
        cascade="all, delete-orphan",
    )


class GeneratedVocabularyItem(Base):
    __tablename__ = "generated_vocabulary_items"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    generated_lesson_id = Column(GUID, ForeignKey("generated_lessons.id", ondelete="CASCADE"), nullable=False)

    user_lexeme_id = Column(GUID, ForeignKey("user_lexemes.id", ondelete="SET NULL"), nullable=True)

    word = Column(String, nullable=True)
    translation = Column(String, nullable=True)
    context_sentence = Column(String, nullable=True)

    mastery_level = Column(Integer, nullable=False, default=0)
    next_review_at = Column(DateTime(timezone=True), server_default=func.now())

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    generated_lesson = relationship("GeneratedLesson", back_populates="vocabulary_items")

    user_lexeme = relationship("UserLexeme")
