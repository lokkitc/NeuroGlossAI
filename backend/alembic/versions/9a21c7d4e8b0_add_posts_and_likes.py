"""add_posts_and_likes

Revision ID: 9a21c7d4e8b0
Revises: 8c3d1a2b4f10
Create Date: 2026-02-26

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9a21c7d4e8b0"
down_revision: Union[str, None] = "8c3d1a2b4f10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "posts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("author_user_id", sa.UUID(), nullable=False),
        sa.Column("character_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("media", sa.JSON(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_posts_public_created", "posts", ["is_public", "created_at"], unique=False)
    op.create_index("ix_posts_author_created", "posts", ["author_user_id", "created_at"], unique=False)

    op.create_table(
        "post_likes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("post_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_post_like"),
    )
    op.create_index("ix_post_likes_post_created", "post_likes", ["post_id", "created_at"], unique=False)
    op.create_index("ix_post_likes_user_created", "post_likes", ["user_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_post_likes_user_created", table_name="post_likes")
    op.drop_index("ix_post_likes_post_created", table_name="post_likes")
    op.drop_table("post_likes")

    op.drop_index("ix_posts_author_created", table_name="posts")
    op.drop_index("ix_posts_public_created", table_name="posts")
    op.drop_table("posts")
