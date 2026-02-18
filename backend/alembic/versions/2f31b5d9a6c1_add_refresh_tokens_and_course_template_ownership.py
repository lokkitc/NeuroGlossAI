"""add_refresh_tokens_and_course_template_ownership

Revision ID: 2f31b5d9a6c1
Revises: 0c2d9a8b7e6f
Create Date: 2026-02-18

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.models.custom_types


revision: str = "2f31b5d9a6c1"
down_revision: Union[str, None] = "b17c4a2d9e01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("user_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("replaced_by_id", app.models.custom_types.GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["replaced_by_id"], ["refresh_tokens.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])

    op.add_column(
        "course_templates",
        sa.Column("created_by_user_id", app.models.custom_types.GUID(), nullable=True),
    )
    op.create_index("ix_course_templates_created_by_user_id", "course_templates", ["created_by_user_id"])
    op.create_foreign_key(
        "fk_course_templates_created_by_user_id",
        "course_templates",
        "users",
        ["created_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE course_templates ct
            SET created_by_user_id = sub.user_id
            FROM (
                SELECT DISTINCT ON (e.course_template_id)
                    e.course_template_id,
                    e.user_id
                FROM enrollments e
                ORDER BY e.course_template_id, e.created_at DESC
            ) sub
            WHERE ct.id = sub.course_template_id
              AND ct.created_by_user_id IS NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_constraint("fk_course_templates_created_by_user_id", "course_templates", type_="foreignkey")
    op.drop_index("ix_course_templates_created_by_user_id", table_name="course_templates")
    op.drop_column("course_templates", "created_by_user_id")

    op.drop_index("ix_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
