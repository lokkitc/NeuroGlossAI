"""add_character_extended_profile

Revision ID: 8c3d1a2b4f10
Revises: 6f1b2c3d4e5a
Create Date: 2026-02-26

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c3d1a2b4f10"
down_revision: Union[str, None] = "6f1b2c3d4e5a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("characters", sa.Column("avatar_url", sa.String(), nullable=True))
    op.add_column("characters", sa.Column("thumbnail_url", sa.String(), nullable=True))
    op.add_column("characters", sa.Column("banner_url", sa.String(), nullable=True))

    op.add_column("characters", sa.Column("greeting", sa.String(), nullable=True))

    op.add_column("characters", sa.Column("tags", sa.JSON(), nullable=True))

    op.add_column("characters", sa.Column("voice_provider", sa.String(), nullable=True))
    op.add_column("characters", sa.Column("voice_id", sa.String(), nullable=True))
    op.add_column("characters", sa.Column("voice_settings", sa.JSON(), nullable=True))

    op.add_column("characters", sa.Column("chat_settings", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("characters", "chat_settings")

    op.drop_column("characters", "voice_settings")
    op.drop_column("characters", "voice_id")
    op.drop_column("characters", "voice_provider")

    op.drop_column("characters", "tags")

    op.drop_column("characters", "greeting")

    op.drop_column("characters", "banner_url")
    op.drop_column("characters", "thumbnail_url")
    op.drop_column("characters", "avatar_url")
