"""remove_learning_domain

Revision ID: c9f0a1b2c3d4
Revises: b5c2e9d1a0f3
Create Date: 2026-03-02

This migration removes the Duolingo-like learning domain from the database.

It drops course/path/progress/lesson/vocabulary/SRS/chat-learning tables and
removes related columns from existing tables.

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9f0a1b2c3d4"
down_revision: Union[str, None] = "b5c2e9d1a0f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind is not None and bind.dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        raise RuntimeError("remove_learning_domain migration is only implemented for PostgreSQL")

    # Drop dependent/newer tables first.
    op.execute(sa.text("DROP TABLE IF EXISTS chat_learning_lessons CASCADE"))

    # Drop SRS / vocabulary / generated content.
    op.execute(sa.text("DROP TABLE IF EXISTS lesson_lexemes CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS generated_vocabulary_items CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS generated_lessons CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS user_lexemes CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS lexemes CASCADE"))

    # Drop progress / attempts.
    op.execute(sa.text("DROP TABLE IF EXISTS user_level_attempts CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS user_level_progress CASCADE"))

    # Drop enrollments.
    op.execute(sa.text("DROP TABLE IF EXISTS enrollments CASCADE"))

    # Drop course templates/path.
    op.execute(sa.text("DROP TABLE IF EXISTS course_level_templates CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS course_unit_templates CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS course_section_templates CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS course_templates CASCADE"))

    # Drop gamification.
    op.execute(sa.text("DROP TABLE IF EXISTS streaks CASCADE"))

    # Remove columns from existing tables.
    op.execute(sa.text("ALTER TABLE IF EXISTS users DROP COLUMN IF EXISTS xp CASCADE"))

    op.execute(sa.text("ALTER TABLE IF EXISTS ai_generation_events DROP COLUMN IF EXISTS enrollment_id CASCADE"))
    op.execute(sa.text("ALTER TABLE IF EXISTS ai_generation_events DROP COLUMN IF EXISTS generated_lesson_id CASCADE"))

    op.execute(sa.text("ALTER TABLE IF EXISTS chat_sessions DROP COLUMN IF EXISTS enrollment_id CASCADE"))
    op.execute(sa.text("ALTER TABLE IF EXISTS chat_sessions DROP COLUMN IF EXISTS active_level_template_id CASCADE"))
    op.execute(sa.text("ALTER TABLE IF EXISTS chat_sessions DROP COLUMN IF EXISTS last_learning_lesson_at_turn CASCADE"))


def downgrade() -> None:
    raise RuntimeError("Learning domain was removed and cannot be restored automatically.")
