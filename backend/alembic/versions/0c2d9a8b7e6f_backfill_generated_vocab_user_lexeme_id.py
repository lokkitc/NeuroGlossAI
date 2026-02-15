"""backfill_generated_vocab_user_lexeme_id

Revision ID: 0c2d9a8b7e6f
Revises: f9c1d2e3a4b5
Create Date: 2026-02-15

Backfills generated_vocabulary_items.user_lexeme_id where possible by linking
existing normalized lexemes and user_lexemes.

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0c2d9a8b7e6f"
down_revision: Union[str, None] = "f9c1d2e3a4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # Best-effort backfill for rows where we can infer:
    # - user_id via enrollments -> generated_lessons
    # - target_language via course_templates
    # - lexeme_id via lexemes(target_language, normalized)
    # - user_lexeme_id via user_lexemes(user_id, lexeme_id)
    bind.execute(
        sa.text(
            """
        WITH candidates AS (
            SELECT
                gvi.id AS gvi_id,
                ul.id AS user_lexeme_id
            FROM generated_vocabulary_items gvi
            JOIN generated_lessons gl ON gl.id = gvi.generated_lesson_id
            JOIN enrollments e ON e.id = gl.enrollment_id
            JOIN course_templates ct ON ct.id = e.course_template_id
            JOIN lexemes lx ON lx.target_language = ct.target_language
                         AND lx.normalized = lower(trim(coalesce(gvi.word, '')))
            JOIN user_lexemes ul ON ul.user_id = e.user_id AND ul.lexeme_id = lx.id
            WHERE gvi.user_lexeme_id IS NULL
              AND gvi.word IS NOT NULL
              AND trim(gvi.word) <> ''
        )
        UPDATE generated_vocabulary_items gvi
        SET user_lexeme_id = c.user_lexeme_id
        FROM candidates c
        WHERE gvi.id = c.gvi_id
            """
        )
    )


def downgrade() -> None:
    # No safe downgrade; keep populated links.
    pass
