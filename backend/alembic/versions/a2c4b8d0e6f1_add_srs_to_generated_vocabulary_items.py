"""add_srs_to_generated_vocabulary_items

Revision ID: a2c4b8d0e6f1
Revises: f1a8c3d91c02
Create Date: 2026-02-15

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a2c4b8d0e6f1"
down_revision: Union[str, None] = "f1a8c3d91c02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("generated_vocabulary_items", sa.Column("mastery_level", sa.Integer(), nullable=False, server_default="0"))
    op.add_column(
        "generated_vocabulary_items",
        sa.Column("next_review_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("generated_vocabulary_items", "next_review_at")
    op.drop_column("generated_vocabulary_items", "mastery_level")
