"""link_generated_vocab_to_user_lexemes

Revision ID: f9c1d2e3a4b5
Revises: e6b2c1f9a7d3
Create Date: 2026-02-15

Adds optional FK generated_vocabulary_items.user_lexeme_id -> user_lexemes.id
so API can return canonical SRS ids alongside lesson vocabulary.

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.models.custom_types


# revision identifiers, used by Alembic.
revision: str = "f9c1d2e3a4b5"
down_revision: Union[str, None] = "e6b2c1f9a7d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "generated_vocabulary_items",
        sa.Column("user_lexeme_id", app.models.custom_types.GUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_generated_vocab_user_lexeme_id",
        "generated_vocabulary_items",
        "user_lexemes",
        ["user_lexeme_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_generated_vocabulary_items_user_lexeme_id",
        "generated_vocabulary_items",
        ["user_lexeme_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_generated_vocabulary_items_user_lexeme_id", table_name="generated_vocabulary_items")
    op.drop_constraint(
        "fk_generated_vocab_user_lexeme_id",
        "generated_vocabulary_items",
        type_="foreignkey",
    )
    op.drop_column("generated_vocabulary_items", "user_lexeme_id")
