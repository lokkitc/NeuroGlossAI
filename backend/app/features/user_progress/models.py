import enum
import uuid

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.custom_types import GUID


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "course_template_id", name="uq_enrollment_user_course"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_template_id = Column(GUID, ForeignKey("course_templates.id", ondelete="RESTRICT"), nullable=False)

    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    course_template = relationship("CourseTemplate")
    progresses = relationship("UserLevelProgress", back_populates="enrollment", cascade="all, delete-orphan")
    generated_lessons = relationship("GeneratedLesson", back_populates="enrollment", cascade="all, delete-orphan")


class ProgressStatus(str, enum.Enum):
    LOCKED = "locked"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    GOLD = "gold"


class UserLevelProgress(Base):
    __tablename__ = "user_level_progress"
    __table_args__ = (
        UniqueConstraint("enrollment_id", "level_template_id", name="uq_progress_enrollment_level"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    enrollment_id = Column(GUID, ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False)
    level_template_id = Column(GUID, ForeignKey("course_level_templates.id", ondelete="RESTRICT"), nullable=False)

    status = Column(String, nullable=False, default=ProgressStatus.LOCKED.value)
    stars = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    enrollment = relationship("Enrollment", back_populates="progresses")
    level_template = relationship("CourseLevelTemplate", back_populates="progresses")


class UserLevelAttempt(Base):
    __tablename__ = "user_level_attempts"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    enrollment_id = Column(GUID, ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False)
    level_template_id = Column(GUID, ForeignKey("course_level_templates.id", ondelete="RESTRICT"), nullable=False)
    progress_id = Column(GUID, ForeignKey("user_level_progress.id", ondelete="CASCADE"), nullable=False)

    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)

    stars = Column(Integer, nullable=True)
    xp_gained = Column(Integer, nullable=True)

    score = Column(Integer, nullable=True)
    answers_snapshot = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    enrollment = relationship("Enrollment")
    level_template = relationship("CourseLevelTemplate")
    progress = relationship("UserLevelProgress")


class Streak(Base):
    __tablename__ = "streaks"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"))

    current_streak = Column(Integer, default=0)
    last_activity_date = Column(Date)

    user = relationship("User", back_populates="streaks")
