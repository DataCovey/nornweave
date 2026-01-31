"""Initial schema: inboxes, threads, messages, events.

Revision ID: 0001
Revises:
Create Date: 2026-01-31

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all tables and indexes."""
    # ==========================================================================
    # Inboxes table
    # ==========================================================================
    op.create_table(
        "inboxes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email_address", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("provider_config", sa.JSON(), nullable=False, server_default="{}"),
    )
    # Index on email_address is created by unique=True

    # ==========================================================================
    # Threads table
    # ==========================================================================
    op.create_table(
        "threads",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "inbox_id",
            sa.String(36),
            sa.ForeignKey("inboxes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("participant_hash", sa.String(64), nullable=True),
    )

    # Index for list_threads_for_inbox: ORDER BY last_message_at DESC
    op.create_index(
        "ix_threads_inbox_last_message",
        "threads",
        ["inbox_id", sa.text("last_message_at DESC")],
    )

    # Index for get_thread_by_participant_hash
    op.create_index(
        "ix_threads_inbox_participant_hash",
        "threads",
        ["inbox_id", "participant_hash"],
    )

    # ==========================================================================
    # Messages table
    # ==========================================================================
    op.create_table(
        "messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "thread_id",
            sa.String(36),
            sa.ForeignKey("threads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "inbox_id",
            sa.String(36),
            sa.ForeignKey("inboxes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider_message_id", sa.String(512), nullable=True),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("content_raw", sa.Text(), nullable=False, server_default=""),
        sa.Column("content_clean", sa.Text(), nullable=False, server_default=""),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
        ),
    )

    # Index for list_messages_for_thread: ORDER BY created_at
    op.create_index(
        "ix_messages_thread_created",
        "messages",
        ["thread_id", "created_at"],
    )

    # Index for list_messages_for_inbox: ORDER BY created_at
    op.create_index(
        "ix_messages_inbox_created",
        "messages",
        ["inbox_id", "created_at"],
    )

    # Index for search_messages: filter by inbox
    op.create_index(
        "ix_messages_inbox_id",
        "messages",
        ["inbox_id"],
    )

    # Partial unique index for deduplication (Postgres only, SQLite ignores where clause)
    # This prevents duplicate provider_message_id per inbox
    op.create_index(
        "ix_messages_inbox_provider_msg",
        "messages",
        ["inbox_id", "provider_message_id"],
        unique=True,
        postgresql_where=sa.text("provider_message_id IS NOT NULL"),
    )

    # ==========================================================================
    # Events table (Phase 3 webhooks)
    # ==========================================================================
    op.create_table(
        "events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
    )

    # Index for list_events: ORDER BY created_at DESC
    op.create_index(
        "ix_events_created_at",
        "events",
        [sa.text("created_at DESC")],
    )

    # Index for list_events(type=...): filter by type, ORDER BY created_at DESC
    op.create_index(
        "ix_events_type_created",
        "events",
        ["type", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    """Drop all tables and indexes."""
    # Drop events
    op.drop_index("ix_events_type_created", table_name="events")
    op.drop_index("ix_events_created_at", table_name="events")
    op.drop_table("events")

    # Drop messages
    op.drop_index("ix_messages_inbox_provider_msg", table_name="messages")
    op.drop_index("ix_messages_inbox_id", table_name="messages")
    op.drop_index("ix_messages_inbox_created", table_name="messages")
    op.drop_index("ix_messages_thread_created", table_name="messages")
    op.drop_table("messages")

    # Drop threads
    op.drop_index("ix_threads_inbox_participant_hash", table_name="threads")
    op.drop_index("ix_threads_inbox_last_message", table_name="threads")
    op.drop_table("threads")

    # Drop inboxes
    op.drop_table("inboxes")
