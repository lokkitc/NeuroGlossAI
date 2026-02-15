"""link_lessons_to_levels_and_add_path_uniques

Revision ID: 7b1f5c2a9d10
Revises: 4ee2a3e318ee
Create Date: 2026-02-15

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.models.custom_types


# revision identifiers, used by Alembic.
revision: str = "7b1f5c2a9d10"
down_revision: Union[str, None] = "4ee2a3e318ee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # lessons.level_id -> levels.id (nullable) + unique
    op.add_column(
        "lessons",
        sa.Column("level_id", app.models.custom_types.GUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_lessons_level_id_levels",
        "lessons",
        "levels",
        ["level_id"],
        ["id"],
    )
    op.create_unique_constraint("uq_lessons_level_id", "lessons", ["level_id"])

    # Path uniqueness constraints
    op.create_unique_constraint("uq_sections_user_order", "sections", ["user_id", "order"])
    op.create_unique_constraint("uq_units_section_order", "units", ["section_id", "order"])
    op.create_unique_constraint("uq_levels_unit_order", "levels", ["unit_id", "order"])


def downgrade() -> None:
    op.drop_constraint("uq_levels_unit_order", "levels", type_="unique")
    op.drop_constraint("uq_units_section_order", "units", type_="unique")
    op.drop_constraint("uq_sections_user_order", "sections", type_="unique")

    op.drop_constraint("uq_lessons_level_id", "lessons", type_="unique")
    op.drop_constraint("fk_lessons_level_id_levels", "lessons", type_="foreignkey")
    op.drop_column("lessons", "level_id")
