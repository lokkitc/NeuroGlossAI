"""add_course_versioning_attempts_and_srs

Revision ID: e6b2c1f9a7d3
Revises: d4a9e1c0f8aa
Create Date: 2026-02-15

Adds best-practice extensions:
- CourseTemplate.slug + unique(slug, version)
- GeneratedLesson debug/generation fields
- Attempts tracking (user_level_attempts)
- Normalized SRS vocabulary (lexemes, user_lexemes, lesson_lexemes) with backfill

"""

from __future__ import annotations

from typing import Sequence, Union
import re
import uuid

from alembic import op
import sqlalchemy as sa
import app.models.custom_types


# revision identifiers, used by Alembic.
revision: str = "e6b2c1f9a7d3"
down_revision: Union[str, None] = "d4a9e1c0f8aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_slug_safe_re = re.compile(r"[^a-z0-9]+")


def _slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = _slug_safe_re.sub("_", value).strip("_")
    return value or "course"


def upgrade() -> None:
    # --- course_templates.slug + unique constraint
    op.add_column("course_templates", sa.Column("slug", sa.String(), nullable=True))
    op.create_unique_constraint("uq_course_template_slug_version", "course_templates", ["slug", "version"])

    # best-effort slug backfill
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, target_language, cefr_level, theme FROM course_templates WHERE slug IS NULL"))
    for r in rows.mappings():
        theme = r.get("theme") or "general"
        slug = _slugify(f"{r['target_language']}_{r['cefr_level']}_{theme}")
        conn.execute(
            sa.text("UPDATE course_templates SET slug = :slug WHERE id = :id AND slug IS NULL"),
            {"slug": slug, "id": r["id"]},
        )

    # --- generated_lessons extra fields
    op.add_column("generated_lessons", sa.Column("input_context", sa.JSON(), nullable=True))
    op.add_column("generated_lessons", sa.Column("raw_model_output", sa.JSON(), nullable=True))
    op.add_column("generated_lessons", sa.Column("validation_errors", sa.JSON(), nullable=True))
    op.add_column(
        "generated_lessons",
        sa.Column("repair_count", sa.Integer(), nullable=False, server_default="0"),
    )

    # --- attempts
    op.create_table(
        "user_level_attempts",
        sa.Column("id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("enrollment_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("level_template_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("progress_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stars", sa.Integer(), nullable=True),
        sa.Column("xp_gained", sa.Integer(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("answers_snapshot", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"]),
        sa.ForeignKeyConstraint(["level_template_id"], ["course_level_templates.id"]),
        sa.ForeignKeyConstraint(["progress_id"], ["user_level_progress.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_level_attempts_enrollment_id", "user_level_attempts", ["enrollment_id"])

    # --- normalized SRS tables
    op.create_table(
        "lexemes",
        sa.Column("id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("target_language", sa.String(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("normalized", sa.String(), nullable=False),
        sa.Column("part_of_speech", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("target_language", "normalized", name="uq_lexeme_lang_norm"),
    )

    op.create_table(
        "user_lexemes",
        sa.Column("id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("user_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("enrollment_id", app.models.custom_types.GUID(), nullable=True),
        sa.Column("lexeme_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("translation_preferred", sa.String(), nullable=True),
        sa.Column("context_sentence_preferred", sa.String(), nullable=True),
        sa.Column("mastery_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_review_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"]),
        sa.ForeignKeyConstraint(["lexeme_id"], ["lexemes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "lexeme_id", name="uq_user_lexeme"),
    )
    op.create_index("ix_user_lexemes_user_id", "user_lexemes", ["user_id"])
    op.create_index("ix_user_lexemes_next_review_at", "user_lexemes", ["next_review_at"])

    op.create_table(
        "lesson_lexemes",
        sa.Column("id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("generated_lesson_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("lexeme_id", app.models.custom_types.GUID(), nullable=False),
        sa.Column("user_lexeme_id", app.models.custom_types.GUID(), nullable=True),
        sa.Column("translation", sa.String(), nullable=True),
        sa.Column("context_sentence", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["generated_lesson_id"], ["generated_lessons.id"]),
        sa.ForeignKeyConstraint(["lexeme_id"], ["lexemes.id"]),
        sa.ForeignKeyConstraint(["user_lexeme_id"], ["user_lexemes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("generated_lesson_id", "lexeme_id", name="uq_lesson_lexeme"),
    )
    op.create_index("ix_lesson_lexemes_lesson_id", "lesson_lexemes", ["generated_lesson_id"])

    # --- backfill lexemes/user_lexemes/lesson_lexemes from generated_vocabulary_items
    _backfill_srs(conn)


def _normalize_word(word: str) -> str:
    return (word or "").strip().lower()


def _backfill_srs(conn) -> None:
    # Fetch all vocab rows with user_id/enrollment_id/target_language
    vocab_rows = conn.execute(
        sa.text(
            """
            SELECT
                gvi.id AS gvi_id,
                gvi.generated_lesson_id,
                gvi.word,
                gvi.translation,
                gvi.context_sentence,
                gvi.mastery_level,
                gvi.next_review_at,
                enr.user_id,
                enr.id AS enrollment_id,
                ct.target_language
            FROM generated_vocabulary_items gvi
            JOIN generated_lessons gl ON gl.id = gvi.generated_lesson_id
            JOIN enrollments enr ON enr.id = gl.enrollment_id
            JOIN course_templates ct ON ct.id = enr.course_template_id
            """
        )
    ).mappings().all()

    if not vocab_rows:
        return

    # In-memory maps
    lexeme_id_by_key: dict[tuple[str, str], uuid.UUID] = {}
    user_lexeme_id_by_key: dict[tuple[uuid.UUID, uuid.UUID], uuid.UUID] = {}

    # Preload existing lexemes/user_lexemes if any
    existing_lex = conn.execute(sa.text("SELECT id, target_language, normalized FROM lexemes")).mappings().all()
    for r in existing_lex:
        lexeme_id_by_key[(r["target_language"], r["normalized"])] = r["id"]

    existing_ul = conn.execute(sa.text("SELECT id, user_id, lexeme_id FROM user_lexemes")).mappings().all()
    for r in existing_ul:
        user_lexeme_id_by_key[(r["user_id"], r["lexeme_id"])] = r["id"]

    # Insert missing
    for row in vocab_rows:
        word = (row.get("word") or "").strip()
        if not word:
            continue

        target_language = row.get("target_language") or "unknown"
        normalized = _normalize_word(word)

        lex_key = (target_language, normalized)
        lexeme_id = lexeme_id_by_key.get(lex_key)
        if lexeme_id is None:
            lexeme_id = uuid.uuid4()
            conn.execute(
                sa.text(
                    "INSERT INTO lexemes (id, target_language, text, normalized, created_at) VALUES (:id, :lang, :text, :norm, now())"
                ),
                {"id": lexeme_id, "lang": target_language, "text": word, "norm": normalized},
            )
            lexeme_id_by_key[lex_key] = lexeme_id

        user_id = row["user_id"]
        enrollment_id = row.get("enrollment_id")

        ul_key = (user_id, lexeme_id)
        user_lexeme_id = user_lexeme_id_by_key.get(ul_key)
        if user_lexeme_id is None:
            user_lexeme_id = uuid.uuid4()
            conn.execute(
                sa.text(
                    """
                    INSERT INTO user_lexemes (
                        id, user_id, enrollment_id, lexeme_id,
                        translation_preferred, context_sentence_preferred,
                        mastery_level, next_review_at, first_seen_at, created_at
                    ) VALUES (
                        :id, :user_id, :enrollment_id, :lexeme_id,
                        :translation, :context,
                        :mastery_level, :next_review_at, now(), now()
                    )
                    """
                ),
                {
                    "id": user_lexeme_id,
                    "user_id": user_id,
                    "enrollment_id": enrollment_id,
                    "lexeme_id": lexeme_id,
                    "translation": row.get("translation"),
                    "context": row.get("context_sentence"),
                    "mastery_level": row.get("mastery_level") or 0,
                    "next_review_at": row.get("next_review_at"),
                },
            )
            user_lexeme_id_by_key[ul_key] = user_lexeme_id
        else:
            # Best-effort aggregate: keep max mastery and earliest next_review_at
            conn.execute(
                sa.text(
                    """
                    UPDATE user_lexemes
                    SET mastery_level = GREATEST(mastery_level, :mastery_level),
                        next_review_at = LEAST(next_review_at, :next_review_at)
                    WHERE id = :id
                    """
                ),
                {
                    "id": user_lexeme_id,
                    "mastery_level": row.get("mastery_level") or 0,
                    "next_review_at": row.get("next_review_at"),
                },
            )

        # lesson_lexeme
        conn.execute(
            sa.text(
                """
                INSERT INTO lesson_lexemes (
                    id, generated_lesson_id, lexeme_id, user_lexeme_id,
                    translation, context_sentence, created_at
                ) VALUES (
                    :id, :lesson_id, :lexeme_id, :user_lexeme_id,
                    :translation, :context, now()
                )
                ON CONFLICT (generated_lesson_id, lexeme_id) DO NOTHING
                """
            ),
            {
                "id": uuid.uuid4(),
                "lesson_id": row["generated_lesson_id"],
                "lexeme_id": lexeme_id,
                "user_lexeme_id": user_lexeme_id,
                "translation": row.get("translation"),
                "context": row.get("context_sentence"),
            },
        )


def downgrade() -> None:
    op.drop_index("ix_lesson_lexemes_lesson_id", table_name="lesson_lexemes")
    op.drop_table("lesson_lexemes")

    op.drop_index("ix_user_lexemes_next_review_at", table_name="user_lexemes")
    op.drop_index("ix_user_lexemes_user_id", table_name="user_lexemes")
    op.drop_table("user_lexemes")

    op.drop_table("lexemes")

    op.drop_index("ix_user_level_attempts_enrollment_id", table_name="user_level_attempts")
    op.drop_table("user_level_attempts")

    op.drop_column("generated_lessons", "repair_count")
    op.drop_column("generated_lessons", "validation_errors")
    op.drop_column("generated_lessons", "raw_model_output")
    op.drop_column("generated_lessons", "input_context")

    op.drop_constraint("uq_course_template_slug_version", "course_templates", type_="unique")
    op.drop_column("course_templates", "slug")
