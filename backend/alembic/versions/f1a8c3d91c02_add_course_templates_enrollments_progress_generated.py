"""add_course_templates_enrollments_progress_generated

Revision ID: f1a8c3d91c02
Revises: 7b1f5c2a9d10
Create Date: 2026-02-15

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.models.custom_types


# revision identifiers, used by Alembic.
revision: str = "f1a8c3d91c02"
down_revision: Union[str, None] = "7b1f5c2a9d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "course_templates",
        sa.Column("id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("target_language", sa.String(), nullable=False),
        sa.Column("theme", sa.String(), nullable=True),
        sa.Column("cefr_level", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("interests", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "course_section_templates",
        sa.Column("id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("course_template_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["course_template_id"], ["course_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_template_id", "order", name="uq_course_section_course_order"),
    )

    op.create_table(
        "course_unit_templates",
        sa.Column("id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("section_template_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("topic", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("icon", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["section_template_id"], ["course_section_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("section_template_id", "order", name="uq_course_unit_section_order"),
    )

    op.create_table(
        "course_level_templates",
        sa.Column("id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("unit_template_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("total_steps", sa.Integer(), nullable=False),
        sa.Column("goal", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["unit_template_id"], ["course_unit_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("unit_template_id", "order", name="uq_course_level_unit_order"),
    )

    op.create_table(
        "enrollments",
        sa.Column("id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("user_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("course_template_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["course_template_id"], ["course_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "course_template_id", name="uq_enrollment_user_course"),
    )

    op.create_table(
        "user_level_progress",
        sa.Column("id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("enrollment_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("level_template_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"]),
        sa.ForeignKeyConstraint(["level_template_id"], ["course_level_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("enrollment_id", "level_template_id", name="uq_progress_enrollment_level"),
    )

    op.create_table(
        "generated_lessons",
        sa.Column("id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("enrollment_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("level_template_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("topic_snapshot", sa.String(), nullable=True),
        sa.Column("prompt_version", sa.String(), nullable=True),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("content_text", sa.String(), nullable=False),
        sa.Column("exercises", sa.JSON(), nullable=True),
        sa.Column("quality_status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"]),
        sa.ForeignKeyConstraint(["level_template_id"], ["course_level_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("enrollment_id", "level_template_id", name="uq_generated_lesson_enrollment_level"),
    )

    op.create_table(
        "generated_vocabulary_items",
        sa.Column("id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("generated_lesson_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("word", sa.String(), nullable=True),
        sa.Column("translation", sa.String(), nullable=True),
        sa.Column("context_sentence", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["generated_lesson_id"], ["generated_lessons.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_enrollments_user_id", "enrollments", ["user_id"])
    op.create_index("ix_user_level_progress_enrollment_id", "user_level_progress", ["enrollment_id"])
    op.create_index("ix_generated_lessons_enrollment_id", "generated_lessons", ["enrollment_id"])


def downgrade() -> None:
    op.drop_index("ix_generated_lessons_enrollment_id", table_name="generated_lessons")
    op.drop_index("ix_user_level_progress_enrollment_id", table_name="user_level_progress")
    op.drop_index("ix_enrollments_user_id", table_name="enrollments")

    op.drop_table("generated_vocabulary_items")
    op.drop_table("generated_lessons")
    op.drop_table("user_level_progress")
    op.drop_table("enrollments")
    op.drop_table("course_level_templates")
    op.drop_table("course_unit_templates")
    op.drop_table("course_section_templates")
    op.drop_table("course_templates")
