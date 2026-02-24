"""bind_chat_sessions_to_enrollment_and_level

Revision ID: 3b4c5d6e7f80
Revises: 2a3b4c5d6e7f
Create Date: 2026-02-24

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3b4c5d6e7f80"
down_revision: Union[str, None] = "2a3b4c5d6e7f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chat_sessions",
        sa.Column("enrollment_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "chat_sessions",
        sa.Column("active_level_template_id", sa.UUID(), nullable=True),
    )

    op.create_index(op.f("ix_chat_sessions_enrollment_id"), "chat_sessions", ["enrollment_id"], unique=False)
    op.create_index(op.f("ix_chat_sessions_active_level_template_id"), "chat_sessions", ["active_level_template_id"], unique=False)

    op.create_foreign_key(
        "fk_chat_sessions_enrollment_id",
        "chat_sessions",
        "enrollments",
        ["enrollment_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_chat_sessions_active_level_template_id",
        "chat_sessions",
        "course_level_templates",
        ["active_level_template_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_chat_sessions_active_level_template_id", "chat_sessions", type_="foreignkey")
    op.drop_constraint("fk_chat_sessions_enrollment_id", "chat_sessions", type_="foreignkey")

    op.drop_index(op.f("ix_chat_sessions_active_level_template_id"), table_name="chat_sessions")
    op.drop_index(op.f("ix_chat_sessions_enrollment_id"), table_name="chat_sessions")

    op.drop_column("chat_sessions", "active_level_template_id")
    op.drop_column("chat_sessions", "enrollment_id")
