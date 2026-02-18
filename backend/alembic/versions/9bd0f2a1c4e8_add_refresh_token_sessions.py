"""add_refresh_token_sessions

Revision ID: 9bd0f2a1c4e8
Revises: 2f31b5d9a6c1
Create Date: 2026-02-18

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9bd0f2a1c4e8"
down_revision: Union[str, None] = "7a2e1c3d5f90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # refresh_tokens: add session_id/device_id + index on (user_id, session_id)
    op.add_column("refresh_tokens", sa.Column("session_id", sa.String(), nullable=True))
    op.add_column("refresh_tokens", sa.Column("device_id", sa.String(), nullable=True))

    op.create_index("ix_refresh_tokens_session_id", "refresh_tokens", ["session_id"])
    op.create_index("ix_refresh_tokens_device_id", "refresh_tokens", ["device_id"])
    op.create_index("ix_refresh_tokens_user_session", "refresh_tokens", ["user_id", "session_id"])

    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else ""

    # Backfill session_id for existing rows.
    if dialect == "postgresql":
        # Avoid pgcrypto dependency: build a deterministic-ish token from md5(random + clock + id)
        op.execute(
            """
            UPDATE refresh_tokens
            SET session_id = substring(md5(random()::text || clock_timestamp()::text || id::text) for 32)
            WHERE session_id IS NULL
            """
        )
    else:
        # Fallback deterministic-ish session_id for SQLite/dev: use id string
        bind.execute(sa.text("UPDATE refresh_tokens SET session_id = CAST(id AS TEXT) WHERE session_id IS NULL"))

    # Make session_id NOT NULL where possible
    if dialect == "postgresql":
        op.execute("ALTER TABLE refresh_tokens ALTER COLUMN session_id SET NOT NULL")
    elif dialect == "sqlite":
        return
    else:
        try:
            op.alter_column("refresh_tokens", "session_id", existing_type=sa.String(), nullable=False)
        except Exception:
            pass


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_user_session", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_device_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_session_id", table_name="refresh_tokens")
    op.drop_column("refresh_tokens", "device_id")
    op.drop_column("refresh_tokens", "session_id")
