"""add_user_profile_and_preferences

Revision ID: 5a8c2f1e3d4b
Revises: 4d5e6f708192
Create Date: 2026-02-24

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5a8c2f1e3d4b"
down_revision: Union[str, None] = "4d5e6f708192"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_url", sa.String(), nullable=True))
    op.add_column("users", sa.Column("preferred_name", sa.String(), nullable=True))
    op.add_column("users", sa.Column("bio", sa.String(), nullable=True))
    op.add_column("users", sa.Column("timezone", sa.String(), nullable=True, server_default="UTC"))
    op.add_column("users", sa.Column("ui_theme", sa.String(), nullable=True, server_default="system"))

    op.add_column("users", sa.Column("assistant_tone", sa.String(), nullable=True, server_default="friendly"))
    op.add_column("users", sa.Column("assistant_verbosity", sa.Integer(), nullable=True, server_default="3"))
    op.add_column("users", sa.Column("preferences", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "preferences")
    op.drop_column("users", "assistant_verbosity")
    op.drop_column("users", "assistant_tone")
    op.drop_column("users", "ui_theme")
    op.drop_column("users", "timezone")
    op.drop_column("users", "bio")
    op.drop_column("users", "preferred_name")
    op.drop_column("users", "avatar_url")
