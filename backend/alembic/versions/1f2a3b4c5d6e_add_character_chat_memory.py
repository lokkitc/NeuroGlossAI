"""add_character_chat_memory

Revision ID: 1f2a3b4c5d6e
Revises: 0c2d9a8b7e6f
Create Date: 2026-02-24

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1f2a3b4c5d6e"
down_revision: Union[str, None] = "0c2d9a8b7e6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "characters",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_user_id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("system_prompt", sa.String(), nullable=False),
        sa.Column("style_prompt", sa.String(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_nsfw", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_user_id", "slug", name="uq_character_owner_slug"),
    )
    op.create_index(op.f("ix_characters_owner_user_id"), "characters", ["owner_user_id"], unique=False)

    op.create_table(
        "rooms",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_nsfw", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rooms_owner_user_id"), "rooms", ["owner_user_id"], unique=False)

    op.create_table(
        "room_participants",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("room_id", sa.UUID(), nullable=False),
        sa.Column("character_id", sa.UUID(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("room_id", "character_id", name="uq_room_character"),
    )
    op.create_index(op.f("ix_room_participants_room_id"), "room_participants", ["room_id"], unique=False)

    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_user_id", sa.UUID(), nullable=False),
        sa.Column("character_id", sa.UUID(), nullable=True),
        sa.Column("room_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_summary_at_turn", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_sessions_owner_user_id"), "chat_sessions", ["owner_user_id"], unique=False)

    op.create_table(
        "chat_turns",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("turn_index", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("character_id", sa.UUID(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "turn_index", name="uq_chat_turn_session_index"),
    )
    op.create_index("ix_chat_turns_session_created", "chat_turns", ["session_id", "created_at"], unique=False)

    op.create_table(
        "memory_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_user_id", sa.UUID(), nullable=False),
        sa.Column("character_id", sa.UUID(), nullable=True),
        sa.Column("room_id", sa.UUID(), nullable=True),
        sa.Column("session_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("importance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_memory_owner_created", "memory_items", ["owner_user_id", "created_at"], unique=False)
    op.create_index("ix_memory_owner_character", "memory_items", ["owner_user_id", "character_id"], unique=False)

    op.create_table(
        "chat_session_summaries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("up_to_turn_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_summary_session_created", "chat_session_summaries", ["session_id", "created_at"], unique=False)

    op.create_table(
        "moderation_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_user_id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=True),
        sa.Column("turn_id", sa.UUID(), nullable=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["turn_id"], ["chat_turns.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_moderation_owner_created", "moderation_events", ["owner_user_id", "created_at"], unique=False)
    op.create_index("ix_moderation_session_created", "moderation_events", ["session_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_moderation_session_created", table_name="moderation_events")
    op.drop_index("ix_moderation_owner_created", table_name="moderation_events")
    op.drop_table("moderation_events")

    op.drop_index("ix_chat_summary_session_created", table_name="chat_session_summaries")
    op.drop_table("chat_session_summaries")

    op.drop_index("ix_memory_owner_character", table_name="memory_items")
    op.drop_index("ix_memory_owner_created", table_name="memory_items")
    op.drop_table("memory_items")

    op.drop_index("ix_chat_turns_session_created", table_name="chat_turns")
    op.drop_table("chat_turns")

    op.drop_index(op.f("ix_chat_sessions_owner_user_id"), table_name="chat_sessions")
    op.drop_table("chat_sessions")

    op.drop_index(op.f("ix_room_participants_room_id"), table_name="room_participants")
    op.drop_table("room_participants")

    op.drop_index(op.f("ix_rooms_owner_user_id"), table_name="rooms")
    op.drop_table("rooms")

    op.drop_index(op.f("ix_characters_owner_user_id"), table_name="characters")
    op.drop_table("characters")
