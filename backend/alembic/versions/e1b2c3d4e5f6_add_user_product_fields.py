"""add_user_product_fields

Revision ID: e1b2c3d4e5f6
Revises: d1c3a7b2e9f0
Create Date: 2026-03-02

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e1b2c3d4e5f6"
down_revision: Union[str, None] = "d1c3a7b2e9f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("xp", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("streak", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("level", sa.Integer(), nullable=False, server_default="1"))

    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("login_count", sa.Integer(), nullable=False, server_default="0"))

    op.add_column("users", sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("location", sa.String(), nullable=True))
    op.add_column("users", sa.Column("social_links", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")))

    op.add_column("users", sa.Column("subscription_tier", sa.String(), nullable=False, server_default="free"))
    op.add_column("users", sa.Column("subscription_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("customer_id", sa.String(), nullable=True))

    op.add_column("users", sa.Column("last_ip", sa.String(), nullable=True))
    op.add_column("users", sa.Column("app_version", sa.String(), nullable=True))
    op.add_column("users", sa.Column("fcm_token", sa.String(), nullable=True))

    op.create_index("ix_users_is_active", "users", ["is_active"], unique=False)
    op.create_index("ix_users_is_public", "users", ["is_public"], unique=False)

    op.alter_column("users", "xp", server_default=None)
    op.alter_column("users", "streak", server_default=None)
    op.alter_column("users", "level", server_default=None)
    op.alter_column("users", "login_count", server_default=None)
    op.alter_column("users", "subscription_tier", server_default=None)
    op.alter_column("users", "is_active", server_default=None)
    op.alter_column("users", "is_verified", server_default=None)
    op.alter_column("users", "is_public", server_default=None)
    op.alter_column("users", "social_links", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_users_is_public", table_name="users")
    op.drop_index("ix_users_is_active", table_name="users")

    op.drop_column("users", "fcm_token")
    op.drop_column("users", "app_version")
    op.drop_column("users", "last_ip")

    op.drop_column("users", "customer_id")
    op.drop_column("users", "subscription_expires_at")
    op.drop_column("users", "subscription_tier")

    op.drop_column("users", "social_links")
    op.drop_column("users", "location")
    op.drop_column("users", "is_public")

    op.drop_column("users", "login_count")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "is_verified")
    op.drop_column("users", "is_active")

    op.drop_column("users", "level")
    op.drop_column("users", "last_activity_at")
    op.drop_column("users", "streak")
    op.drop_column("users", "xp")
