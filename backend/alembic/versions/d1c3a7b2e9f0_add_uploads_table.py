"""add_uploads_table

Revision ID: d1c3a7b2e9f0
Revises: c9f0a1b2c3d4
Create Date: 2026-03-02

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.models.custom_types


revision: str = "d1c3a7b2e9f0"
down_revision: Union[str, None] = "c9f0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "uploads",
        sa.Column("id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("owner_user_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("public_id", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mime", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index("ix_uploads_owner_created", "uploads", ["owner_user_id", "created_at"], unique=False)
    op.create_index("ix_uploads_public_id", "uploads", ["public_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_uploads_public_id", table_name="uploads")
    op.drop_index("ix_uploads_owner_created", table_name="uploads")
    op.drop_table("uploads")
