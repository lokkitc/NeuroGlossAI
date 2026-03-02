"""social_security_analytics_fields

Revision ID: f2c4d6e8a0b1
Revises: e1b2c3d4e5f6
Create Date: 2026-03-02

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2c4d6e8a0b1"
down_revision: Union[str, None] = "e1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # posts: soft delete + counters + updated_at
    op.add_column("posts", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("posts", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("posts", sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("posts", sa.Column("comment_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("posts", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True))

    # post_comments
    op.create_table(
        "post_comments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("post_id", sa.UUID(), nullable=False),
        sa.Column("author_user_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["post_comments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_post_comments_post_created", "post_comments", ["post_id", "created_at"], unique=False)
    op.create_index("ix_post_comments_author_created", "post_comments", ["author_user_id", "created_at"], unique=False)

    # refresh_tokens: metadata
    op.add_column("refresh_tokens", sa.Column("created_ip", sa.String(), nullable=True))
    op.add_column("refresh_tokens", sa.Column("created_user_agent", sa.String(), nullable=True))
    op.add_column("refresh_tokens", sa.Column("created_app_version", sa.String(), nullable=True))
    op.add_column("refresh_tokens", sa.Column("last_ip", sa.String(), nullable=True))
    op.add_column("refresh_tokens", sa.Column("last_user_agent", sa.String(), nullable=True))
    op.add_column("refresh_tokens", sa.Column("last_app_version", sa.String(), nullable=True))

    # chat_sessions: activity + counters
    op.add_column("chat_sessions", sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("chat_sessions", sa.Column("turns_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("chat_sessions", sa.Column("user_turns_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("chat_sessions", sa.Column("assistant_turns_count", sa.Integer(), nullable=False, server_default="0"))

    # memory_items: usage
    op.add_column("memory_items", sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("memory_items", sa.Column("use_count", sa.Integer(), nullable=False, server_default="0"))

    # uploads: processing + analytics
    op.add_column("uploads", sa.Column("status", sa.String(length=32), nullable=False, server_default="uploaded"))
    op.add_column("uploads", sa.Column("sha256", sa.String(length=64), nullable=True))
    op.add_column("uploads", sa.Column("error_code", sa.String(length=64), nullable=True))
    op.add_column("uploads", sa.Column("error_detail", sa.String(length=512), nullable=True))
    op.add_column("uploads", sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("uploads", sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True))

    # Drop server defaults where appropriate
    op.alter_column("posts", "is_deleted", server_default=None)
    op.alter_column("posts", "like_count", server_default=None)
    op.alter_column("posts", "comment_count", server_default=None)

    op.alter_column("chat_sessions", "turns_count", server_default=None)
    op.alter_column("chat_sessions", "user_turns_count", server_default=None)
    op.alter_column("chat_sessions", "assistant_turns_count", server_default=None)

    op.alter_column("memory_items", "use_count", server_default=None)

    op.alter_column("uploads", "status", server_default=None)
    op.alter_column("uploads", "access_count", server_default=None)


def downgrade() -> None:
    op.drop_column("uploads", "last_accessed_at")
    op.drop_column("uploads", "access_count")
    op.drop_column("uploads", "error_detail")
    op.drop_column("uploads", "error_code")
    op.drop_column("uploads", "sha256")
    op.drop_column("uploads", "status")

    op.drop_column("memory_items", "use_count")
    op.drop_column("memory_items", "last_used_at")

    op.drop_column("chat_sessions", "assistant_turns_count")
    op.drop_column("chat_sessions", "user_turns_count")
    op.drop_column("chat_sessions", "turns_count")
    op.drop_column("chat_sessions", "last_activity_at")

    op.drop_column("refresh_tokens", "last_app_version")
    op.drop_column("refresh_tokens", "last_user_agent")
    op.drop_column("refresh_tokens", "last_ip")
    op.drop_column("refresh_tokens", "created_app_version")
    op.drop_column("refresh_tokens", "created_user_agent")
    op.drop_column("refresh_tokens", "created_ip")

    op.drop_index("ix_post_comments_author_created", table_name="post_comments")
    op.drop_index("ix_post_comments_post_created", table_name="post_comments")
    op.drop_table("post_comments")

    op.drop_column("posts", "updated_at")
    op.drop_column("posts", "comment_count")
    op.drop_column("posts", "like_count")
    op.drop_column("posts", "deleted_at")
    op.drop_column("posts", "is_deleted")
