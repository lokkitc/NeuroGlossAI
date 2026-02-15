import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.custom_types import GUID


class UserLevelAttempt(Base):
    __tablename__ = "user_level_attempts"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    enrollment_id = Column(GUID, ForeignKey("enrollments.id"), nullable=False)
    level_template_id = Column(GUID, ForeignKey("course_level_templates.id"), nullable=False)
    progress_id = Column(GUID, ForeignKey("user_level_progress.id"), nullable=False)

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
