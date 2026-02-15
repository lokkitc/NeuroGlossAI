import uuid
from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
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
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    course_template_id = Column(GUID, ForeignKey("course_templates.id"), nullable=False)

    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    course_template = relationship("CourseTemplate")
    progresses = relationship("UserLevelProgress", back_populates="enrollment", cascade="all, delete-orphan")
    generated_lessons = relationship("GeneratedLesson", back_populates="enrollment", cascade="all, delete-orphan")
