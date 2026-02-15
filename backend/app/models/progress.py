import uuid
import enum
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.custom_types import GUID


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
    enrollment_id = Column(GUID, ForeignKey("enrollments.id"), nullable=False)
    level_template_id = Column(GUID, ForeignKey("course_level_templates.id"), nullable=False)

    status = Column(String, nullable=False, default=ProgressStatus.LOCKED.value)
    stars = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    enrollment = relationship("Enrollment", back_populates="progresses")
    level_template = relationship("CourseLevelTemplate", back_populates="progresses")
