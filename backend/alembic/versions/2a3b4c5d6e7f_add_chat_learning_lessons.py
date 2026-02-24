"""add_chat_learning_lessons

Revision ID: 2a3b4c5d6e7f
Revises: 1f2a3b4c5d6e
Create Date: 2026-02-24

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2a3b4c5d6e7f"
down_revision: Union[str, None] = "1f2a3b4c5d6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # chat_sessions: add cadence state
    op.add_column(
        "chat_sessions",
        sa.Column("last_learning_lesson_at_turn", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "chat_learning_lessons",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_user_id", sa.UUID(), nullable=False),
        sa.Column("chat_session_id", sa.UUID(), nullable=False),
        sa.Column("source_turn_from", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_turn_to", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("topic_snapshot", sa.String(), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("vocabulary", sa.JSON(), nullable=True),
        sa.Column("exercises", sa.JSON(), nullable=True),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("quality_status", sa.String(), nullable=True),
        sa.Column("raw_model_output", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chat_session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_learning_session_created", "chat_learning_lessons", ["chat_session_id", "created_at"], unique=False)
    op.create_index("ix_chat_learning_owner_created", "chat_learning_lessons", ["owner_user_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_chat_learning_owner_created", table_name="chat_learning_lessons")
    op.drop_index("ix_chat_learning_session_created", table_name="chat_learning_lessons")
    op.drop_table("chat_learning_lessons")

    op.drop_column("chat_sessions", "last_learning_lesson_at_turn")
