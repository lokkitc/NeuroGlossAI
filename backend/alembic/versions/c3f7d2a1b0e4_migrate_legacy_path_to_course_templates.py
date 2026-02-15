"""migrate_legacy_path_to_course_templates

Revision ID: c3f7d2a1b0e4
Revises: a2c4b8d0e6f1
Create Date: 2026-02-15

Best-effort migration:
- For each user that has legacy sections/units/levels, create a CourseTemplate that mirrors that structure.
- Create an active Enrollment for that user (if they don't already have any enrollment).
- Create UserLevelProgress rows using legacy level status/stars.

It does NOT migrate legacy Lesson/VocabularyItem into GeneratedLesson/GeneratedVocabularyItem.
"""

from typing import Sequence, Union
import uuid
import json

from alembic import op
import sqlalchemy as sa
import app.models.custom_types


# revision identifiers, used by Alembic.
revision: str = "c3f7d2a1b0e4"
down_revision: Union[str, None] = "a2c4b8d0e6f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    users_with_path = bind.execute(sa.text("SELECT DISTINCT user_id FROM sections"))
    user_ids = [row[0] for row in users_with_path.fetchall()]
    if not user_ids:
        return

    for user_id in user_ids:
        # If user already has enrollments, skip (avoid creating duplicates)
        existing = bind.execute(
            sa.text("SELECT id FROM enrollments WHERE user_id = :uid LIMIT 1"),
            {"uid": str(user_id)},
        ).fetchone()
        if existing:
            continue

        user_row = bind.execute(
            sa.text("SELECT target_language, interests FROM users WHERE id = :uid"),
            {"uid": str(user_id)},
        ).fetchone()
        target_language = (user_row[0] if user_row and user_row[0] else "Kazakh")
        interests = (user_row[1] if user_row and user_row[1] is not None else [])
        interests_json = json.dumps(interests)

        course_template_id = str(uuid.uuid4())
        bind.execute(
            sa.text(
                """
                INSERT INTO course_templates (id, target_language, theme, cefr_level, version, is_active, interests, created_at)
                VALUES (:id, :tl, :theme, :cefr, 1, TRUE, :interests, now())
                """
            ),
            {
                "id": course_template_id,
                "tl": target_language,
                "theme": "migrated_legacy_path",
                "cefr": "A1",
                "interests": interests_json,
            },
        )

        enrollment_id = str(uuid.uuid4())
        bind.execute(
            sa.text(
                """
                INSERT INTO enrollments (id, user_id, course_template_id, status, created_at)
                VALUES (:id, :uid, :ctid, 'active', now())
                """
            ),
            {"id": enrollment_id, "uid": str(user_id), "ctid": course_template_id},
        )

        sections = bind.execute(
            sa.text(
                """
                SELECT id, "order", title, description
                FROM sections
                WHERE user_id = :uid
                ORDER BY "order"
                """
            ),
            {"uid": str(user_id)},
        ).fetchall()

        for sec in sections:
            legacy_section_id, sec_order, sec_title, sec_desc = sec
            section_template_id = str(uuid.uuid4())
            bind.execute(
                sa.text(
                    """
                    INSERT INTO course_section_templates (id, course_template_id, "order", title, description)
                    VALUES (:id, :ctid, :ord, :title, :desc)
                    """
                ),
                {
                    "id": section_template_id,
                    "ctid": course_template_id,
                    "ord": int(sec_order),
                    "title": sec_title,
                    "desc": sec_desc,
                },
            )

            units = bind.execute(
                sa.text(
                    """
                    SELECT id, "order", topic, description, icon
                    FROM units
                    WHERE section_id = :sid
                    ORDER BY "order"
                    """
                ),
                {"sid": str(legacy_section_id)},
            ).fetchall()

            for unit in units:
                legacy_unit_id, unit_order, topic, unit_desc, icon = unit
                unit_template_id = str(uuid.uuid4())
                bind.execute(
                    sa.text(
                        """
                        INSERT INTO course_unit_templates (id, section_template_id, "order", topic, description, icon)
                        VALUES (:id, :sid, :ord, :topic, :desc, :icon)
                        """
                    ),
                    {
                        "id": unit_template_id,
                        "sid": section_template_id,
                        "ord": int(unit_order),
                        "topic": topic,
                        "desc": unit_desc,
                        "icon": icon,
                    },
                )

                levels = bind.execute(
                    sa.text(
                        """
                        SELECT id, "order", type, total_steps, status, stars
                        FROM levels
                        WHERE unit_id = :uid
                        ORDER BY "order"
                        """
                    ),
                    {"uid": str(legacy_unit_id)},
                ).fetchall()

                for lvl in levels:
                    legacy_level_id, lvl_order, lvl_type, total_steps, status, stars = lvl
                    level_template_id = str(uuid.uuid4())
                    bind.execute(
                        sa.text(
                            """
                            INSERT INTO course_level_templates (id, unit_template_id, "order", type, total_steps, goal)
                            VALUES (:id, :uid, :ord, :type, :steps, NULL)
                            """
                        ),
                        {
                            "id": level_template_id,
                            "uid": unit_template_id,
                            "ord": int(lvl_order),
                            "type": lvl_type or "lesson",
                            "steps": int(total_steps) if total_steps is not None else 5,
                        },
                    )

                    bind.execute(
                        sa.text(
                            """
                            INSERT INTO user_level_progress (id, enrollment_id, level_template_id, status, stars, created_at, completed_at)
                            VALUES (:id, :eid, :ltid, :status, :stars, now(), NULL)
                            """
                        ),
                        {
                            "id": str(uuid.uuid4()),
                            "eid": enrollment_id,
                            "ltid": level_template_id,
                            "status": status or "locked",
                            "stars": int(stars) if stars is not None else 0,
                        },
                    )


def downgrade() -> None:
    # Irreversible best-effort migration.
    pass
