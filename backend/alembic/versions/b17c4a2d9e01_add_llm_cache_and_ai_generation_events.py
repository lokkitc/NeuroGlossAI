"""add_llm_cache_and_ai_generation_events

Revision ID: b17c4a2d9e01
Revises: 0c2d9a8b7e6f
Create Date: 2026-02-15

Adds:
- llm_cache_entries: DB-backed cache for LLM JSON responses by prompt_hash
- ai_generation_events: analytics events for AI generation operations

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.models.custom_types


# revision identifiers, used by Alembic.
revision: str = "b17c4a2d9e01"
down_revision: Union[str, None] = "0c2d9a8b7e6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "llm_cache_entries",
        sa.Column("id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("prompt_hash", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("prompt", sa.String(), nullable=False, server_default=""),
        sa.Column("response_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("prompt_hash", name="uq_llm_cache_prompt_hash"),
    )
    op.create_index("ix_llm_cache_entries_prompt_hash", "llm_cache_entries", ["prompt_hash"])

    op.create_table(
        "ai_generation_events",
        sa.Column("id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("enrollment_id", app.models.custom_types.GUID(), nullable=True),
        sa.Column("generated_lesson_id", app.models.custom_types.GUID(), nullable=True),
        sa.Column("operation", sa.String(), nullable=False, server_default=""),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("generation_mode", sa.String(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("repair_count", sa.Integer(), nullable=True),
        sa.Column("quality_status", sa.String(), nullable=True),
        sa.Column("error_codes", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["generated_lesson_id"], ["generated_lessons.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_generation_events_created_at", "ai_generation_events", ["created_at"])
    op.create_index("ix_ai_generation_events_enrollment_id", "ai_generation_events", ["enrollment_id"])
    op.create_index("ix_ai_generation_events_generated_lesson_id", "ai_generation_events", ["generated_lesson_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_generation_events_generated_lesson_id", table_name="ai_generation_events")
    op.drop_index("ix_ai_generation_events_enrollment_id", table_name="ai_generation_events")
    op.drop_index("ix_ai_generation_events_created_at", table_name="ai_generation_events")
    op.drop_table("ai_generation_events")

    op.drop_index("ix_llm_cache_entries_prompt_hash", table_name="llm_cache_entries")
    op.drop_table("llm_cache_entries")
