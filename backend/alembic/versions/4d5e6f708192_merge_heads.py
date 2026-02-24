"""merge heads

Revision ID: 4d5e6f708192
Revises: 3b4c5d6e7f80, c7a1b3d9e2f0
Create Date: 2026-02-24

"""

from typing import Sequence, Union


revision: str = "4d5e6f708192"
down_revision: Union[str, Sequence[str], None] = ("3b4c5d6e7f80", "c7a1b3d9e2f0")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
