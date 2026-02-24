"""add_user_thumbnail_and_banner

Revision ID: 6f1b2c3d4e5a
Revises: 5a8c2f1e3d4b
Create Date: 2026-02-24

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6f1b2c3d4e5a"
down_revision: Union[str, None] = "5a8c2f1e3d4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("thumbnail_url", sa.String(), nullable=True))
    op.add_column("users", sa.Column("banner_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "banner_url")
    op.drop_column("users", "thumbnail_url")
