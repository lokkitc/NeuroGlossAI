"""progress_analytics_fields

Revision ID: a7b8c9d0e1f2
Revises: f2c4d6e8a0b1
Create Date: 2026-03-02

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "f2c4d6e8a0b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if "enrollments" in tables:
        op.add_column("enrollments", sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True))
        op.add_column("enrollments", sa.Column("completed_levels", sa.Integer(), nullable=False, server_default="0"))
        op.add_column("enrollments", sa.Column("total_levels", sa.Integer(), nullable=False, server_default="0"))

        op.create_index("ix_enrollments_user_status", "enrollments", ["user_id", "status"], unique=False)
        op.create_index("ix_enrollments_last_activity", "enrollments", ["last_activity_at"], unique=False)

        op.alter_column("enrollments", "completed_levels", server_default=None)
        op.alter_column("enrollments", "total_levels", server_default=None)

    if "user_level_progress" in tables:
        op.add_column("user_level_progress", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
        op.add_column("user_level_progress", sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True))

        op.create_index(
            "ix_user_level_progress_last_activity",
            "user_level_progress",
            ["last_activity_at"],
            unique=False,
        )

        op.alter_column("user_level_progress", "attempt_count", server_default=None)

    if "generated_lessons" in tables:
        op.add_column("generated_lessons", sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"))
        op.add_column("generated_lessons", sa.Column("generation_ms", sa.Integer(), nullable=False, server_default="0"))

        op.alter_column("generated_lessons", "token_count", server_default=None)
        op.alter_column("generated_lessons", "generation_ms", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if "user_level_progress" in tables:
        op.drop_index("ix_user_level_progress_last_activity", table_name="user_level_progress")
        op.drop_column("user_level_progress", "last_activity_at")
        op.drop_column("user_level_progress", "attempt_count")

    if "enrollments" in tables:
        op.drop_index("ix_enrollments_last_activity", table_name="enrollments")
        op.drop_index("ix_enrollments_user_status", table_name="enrollments")
        op.drop_column("enrollments", "total_levels")
        op.drop_column("enrollments", "completed_levels")
        op.drop_column("enrollments", "last_activity_at")

    if "generated_lessons" in tables:
        op.drop_column("generated_lessons", "generation_ms")
        op.drop_column("generated_lessons", "token_count")
