import uuid

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.custom_types import GUID


class CourseTemplate(Base):
    __tablename__ = "course_templates"

    __table_args__ = (
        UniqueConstraint("slug", "version", name="uq_course_template_slug_version"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    slug = Column(String, nullable=True)

    created_by_user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    target_language = Column(String, nullable=False)
    theme = Column(String, nullable=True)
    cefr_level = Column(String, nullable=False, default="A1")
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)

    interests = Column(JSON, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sections = relationship(
        "CourseSectionTemplate",
        back_populates="course_template",
        order_by="CourseSectionTemplate.order",
        cascade="all, delete-orphan",
    )


class CourseSectionTemplate(Base):
    __tablename__ = "course_section_templates"
    __table_args__ = (
        UniqueConstraint("course_template_id", "order", name="uq_course_section_course_order"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    course_template_id = Column(GUID, ForeignKey("course_templates.id", ondelete="CASCADE"), nullable=False)

    order = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)

    course_template = relationship("CourseTemplate", back_populates="sections")
    units = relationship(
        "CourseUnitTemplate",
        back_populates="section_template",
        order_by="CourseUnitTemplate.order",
        cascade="all, delete-orphan",
    )


class CourseUnitTemplate(Base):
    __tablename__ = "course_unit_templates"
    __table_args__ = (
        UniqueConstraint("section_template_id", "order", name="uq_course_unit_section_order"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    section_template_id = Column(GUID, ForeignKey("course_section_templates.id", ondelete="CASCADE"), nullable=False)

    order = Column(Integer, nullable=False)
    topic = Column(String, nullable=False)
    description = Column(String, nullable=True)
    icon = Column(String, nullable=True)

    section_template = relationship("CourseSectionTemplate", back_populates="units")
    levels = relationship(
        "CourseLevelTemplate",
        back_populates="unit_template",
        order_by="CourseLevelTemplate.order",
        cascade="all, delete-orphan",
    )


class CourseLevelTemplate(Base):
    __tablename__ = "course_level_templates"
    __table_args__ = (
        UniqueConstraint("unit_template_id", "order", name="uq_course_level_unit_order"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    unit_template_id = Column(GUID, ForeignKey("course_unit_templates.id", ondelete="CASCADE"), nullable=False)

    order = Column(Integer, nullable=False)
    type = Column(String, nullable=False, default="lesson")
    total_steps = Column(Integer, nullable=False, default=5)

    goal = Column(String, nullable=True)

    unit_template = relationship("CourseUnitTemplate", back_populates="levels")
    progresses = relationship("UserLevelProgress", back_populates="level_template")
    generated_lessons = relationship("GeneratedLesson", back_populates="level_template")
