"""drop_legacy_path_and_lessons_tables

Revision ID: d4a9e1c0f8aa
Revises: c3f7d2a1b0e4
Create Date: 2026-02-15

Drops legacy, user-specific path + lesson tables that were replaced by the long-term
model (course templates + enrollments + progress + generated content).

Tables dropped:
- vocabulary_items
- lessons
- levels
- units
- sections

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4a9e1c0f8aa"
down_revision: Union[str, None] = "c3f7d2a1b0e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use CASCADE to drop any lingering FKs/constraints referencing legacy tables.
    op.execute(sa.text("DROP TABLE IF EXISTS vocabulary_items CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS lessons CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS levels CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS units CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS sections CASCADE"))


def downgrade() -> None:
    raise RuntimeError("Legacy tables were dropped and cannot be restored automatically.")
