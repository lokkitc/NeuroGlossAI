"""make_course_template_slug_not_null

Revision ID: 7a2e1c3d5f90
Revises: 4c9a1d7e2b11
Create Date: 2026-02-18

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7a2e1c3d5f90"
down_revision: Union[str, None] = "4c9a1d7e2b11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else ""

    # Backfill slug for null/empty values.
    bind.execute(
        sa.text(
            """
            UPDATE course_templates
            SET slug = coalesce(slug, '')
            """
        )
    )

    rows = bind.execute(
        sa.text(
            """
            SELECT id, target_language, cefr_level, theme
            FROM course_templates
            WHERE slug IS NULL OR trim(slug) = ''
            """
        )
    ).mappings().all()

    def slugify(s: str) -> str:
        s = (s or "").strip().lower()
        out = []
        prev_us = False
        for ch in s:
            ok = "a" <= ch <= "z" or "0" <= ch <= "9"
            if ok:
                out.append(ch)
                prev_us = False
            else:
                if not prev_us:
                    out.append("_")
                    prev_us = True
        slug = "".join(out).strip("_")
        return slug or "course"

    for r in rows:
        theme = r.get("theme") or "general"
        base = slugify(f"{r.get('target_language')}_{r.get('cefr_level')}_{theme}")
        # Ensure uniqueness for existing rows by adding deterministic suffix from id
        suffix = str(r["id"]).replace("-", "")[:8]
        slug = f"{base}_{suffix}" if suffix else base
        bind.execute(
            sa.text("UPDATE course_templates SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": r["id"]},
        )

    # Enforce NOT NULL where supported.
    if dialect == "postgresql":
        op.execute("ALTER TABLE course_templates ALTER COLUMN slug SET NOT NULL")
    elif dialect == "sqlite":
        # SQLite: cannot alter column nullability easily without table rebuild.
        # Keep as-is; slug is now backfilled in app code.
        return
    else:
        try:
            op.alter_column("course_templates", "slug", existing_type=sa.String(), nullable=False)
        except Exception:
            pass


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else ""
    if dialect == "postgresql":
        op.execute("ALTER TABLE course_templates ALTER COLUMN slug DROP NOT NULL")
    else:
        try:
            op.alter_column("course_templates", "slug", existing_type=sa.String(), nullable=True)
        except Exception:
            pass
