"""add_themes_and_theme_selection

Revision ID: b5c2e9d1a0f3
Revises: 9a21c7d4e8b0
Create Date: 2026-02-26

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b5c2e9d1a0f3"
down_revision: Union[str, None] = "9a21c7d4e8b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "themes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("theme_type", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("owner_user_id", sa.UUID(), nullable=True),
        sa.Column("light_tokens", sa.JSON(), nullable=True),
        sa.Column("dark_tokens", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_themes_type_public", "themes", ["theme_type", "is_public"], unique=False)
    op.create_index("ix_themes_owner", "themes", ["owner_user_id"], unique=False)

    op.add_column("users", sa.Column("selected_theme_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_users_selected_theme_id",
        "users",
        "themes",
        ["selected_theme_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("characters", sa.Column("chat_theme_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_characters_chat_theme_id",
        "characters",
        "themes",
        ["chat_theme_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_characters_chat_theme_id", "characters", type_="foreignkey")
    op.drop_column("characters", "chat_theme_id")

    op.drop_constraint("fk_users_selected_theme_id", "users", type_="foreignkey")
    op.drop_column("users", "selected_theme_id")

    op.drop_index("ix_themes_owner", table_name="themes")
    op.drop_index("ix_themes_type_public", table_name="themes")
    op.drop_table("themes")
