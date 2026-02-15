import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.custom_types import GUID


class Lexeme(Base):
    __tablename__ = "lexemes"
    __table_args__ = (
        UniqueConstraint("target_language", "normalized", name="uq_lexeme_lang_norm"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    target_language = Column(String, nullable=False)
    text = Column(String, nullable=False)
    normalized = Column(String, nullable=False)

    part_of_speech = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_lexemes = relationship("UserLexeme", back_populates="lexeme")


class UserLexeme(Base):
    __tablename__ = "user_lexemes"
    __table_args__ = (
        UniqueConstraint("user_id", "lexeme_id", name="uq_user_lexeme"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    enrollment_id = Column(GUID, ForeignKey("enrollments.id"), nullable=True)
    lexeme_id = Column(GUID, ForeignKey("lexemes.id"), nullable=False)

    translation_preferred = Column(String, nullable=True)
    context_sentence_preferred = Column(String, nullable=True)

    mastery_level = Column(Integer, nullable=False, default=0)
    next_review_at = Column(DateTime(timezone=True), server_default=func.now())

    first_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)

    extra_metadata = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lexeme = relationship("Lexeme", back_populates="user_lexemes")
    lesson_lexemes = relationship("LessonLexeme", back_populates="user_lexeme", cascade="all, delete-orphan")


class LessonLexeme(Base):
    __tablename__ = "lesson_lexemes"
    __table_args__ = (
        UniqueConstraint("generated_lesson_id", "lexeme_id", name="uq_lesson_lexeme"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    generated_lesson_id = Column(GUID, ForeignKey("generated_lessons.id"), nullable=False)
    lexeme_id = Column(GUID, ForeignKey("lexemes.id"), nullable=False)
    user_lexeme_id = Column(GUID, ForeignKey("user_lexemes.id"), nullable=True)

    translation = Column(String, nullable=True)
    context_sentence = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_lexeme = relationship("UserLexeme", back_populates="lesson_lexemes")
    lexeme = relationship("Lexeme")
    generated_lesson = relationship("GeneratedLesson")
