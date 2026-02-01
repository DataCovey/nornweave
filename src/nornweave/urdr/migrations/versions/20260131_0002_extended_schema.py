"""Add extended schema fields: attachments table, extended messages/threads/events.

Revision ID: 0002
Revises: 0001
Create Date: 2026-01-31

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add new tables and columns for extended schema support."""
    # ==========================================================================
    # Attachments table (new)
    # ==========================================================================
    op.create_table(
        "attachments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "message_id",
            sa.String(36),
            sa.ForeignKey("messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("content_type", sa.String(255), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("disposition", sa.String(20), nullable=False, server_default="attachment"),
        sa.Column("content_id", sa.String(255), nullable=True),
        sa.Column("content", sa.LargeBinary(), nullable=True),
        sa.Column("storage_path", sa.String(1024), nullable=True),
        sa.Column("storage_backend", sa.String(50), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_attachments_message_id", "attachments", ["message_id"])
    op.create_index("ix_attachments_content_id", "attachments", ["content_id"])

    # ==========================================================================
    # Threads table updates
    # ==========================================================================
    # Add new columns
    op.add_column("threads", sa.Column("labels", sa.JSON(), nullable=True))
    op.add_column(
        "threads",
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "threads",
        sa.Column("received_timestamp", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "threads",
        sa.Column("sent_timestamp", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "threads",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
        ),
    )
    op.add_column(
        "threads",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
        ),
    )
    op.add_column("threads", sa.Column("senders", sa.JSON(), nullable=True))
    op.add_column("threads", sa.Column("recipients", sa.JSON(), nullable=True))
    op.add_column("threads", sa.Column("normalized_subject", sa.String(512), nullable=True))
    op.add_column("threads", sa.Column("preview", sa.String(255), nullable=True))
    op.add_column("threads", sa.Column("last_message_id", sa.String(36), nullable=True))
    op.add_column(
        "threads", sa.Column("message_count", sa.Integer(), nullable=True, server_default="0")
    )
    op.add_column("threads", sa.Column("size", sa.Integer(), nullable=True, server_default="0"))

    # Create index on normalized_subject
    op.create_index(
        "ix_threads_inbox_normalized_subject",
        "threads",
        ["inbox_id", "normalized_subject"],
    )

    # ==========================================================================
    # Messages table updates
    # ==========================================================================
    # Add new columns
    op.add_column("messages", sa.Column("labels", sa.JSON(), nullable=True))
    op.add_column(
        "messages",
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "messages",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
        ),
    )
    op.add_column("messages", sa.Column("from_address", sa.String(512), nullable=True))
    op.add_column("messages", sa.Column("reply_to_addresses", sa.JSON(), nullable=True))
    op.add_column("messages", sa.Column("to_addresses", sa.JSON(), nullable=True))
    op.add_column("messages", sa.Column("cc_addresses", sa.JSON(), nullable=True))
    op.add_column("messages", sa.Column("bcc_addresses", sa.JSON(), nullable=True))
    op.add_column("messages", sa.Column("subject", sa.Text(), nullable=True))
    op.add_column("messages", sa.Column("preview", sa.String(255), nullable=True))
    op.add_column("messages", sa.Column("text", sa.Text(), nullable=True))
    op.add_column("messages", sa.Column("html", sa.Text(), nullable=True))
    op.add_column("messages", sa.Column("extracted_text", sa.Text(), nullable=True))
    op.add_column("messages", sa.Column("extracted_html", sa.Text(), nullable=True))
    op.add_column("messages", sa.Column("in_reply_to", sa.String(512), nullable=True))
    op.add_column("messages", sa.Column("references", sa.JSON(), nullable=True))
    op.add_column("messages", sa.Column("headers", sa.JSON(), nullable=True))
    op.add_column("messages", sa.Column("size", sa.Integer(), nullable=True, server_default="0"))

    # Create index on timestamp
    op.create_index("ix_messages_timestamp", "messages", ["timestamp"])

    # ==========================================================================
    # Events table updates
    # ==========================================================================
    # Add new columns
    op.add_column("events", sa.Column("event_type", sa.String(50), nullable=True))
    op.add_column(
        "events",
        sa.Column(
            "inbox_id",
            sa.String(36),
            sa.ForeignKey("inboxes.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "events",
        sa.Column(
            "thread_id",
            sa.String(36),
            sa.ForeignKey("threads.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "events",
        sa.Column(
            "message_id",
            sa.String(36),
            sa.ForeignKey("messages.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "events",
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes
    op.create_index("ix_events_event_type", "events", ["event_type"])
    op.create_index("ix_events_inbox_id", "events", ["inbox_id"])
    op.create_index("ix_events_timestamp", "events", [sa.text("timestamp DESC")])


def downgrade() -> None:
    """Remove extended schema updates."""
    # Drop events columns and indexes
    op.drop_index("ix_events_timestamp", table_name="events")
    op.drop_index("ix_events_inbox_id", table_name="events")
    op.drop_index("ix_events_event_type", table_name="events")
    op.drop_column("events", "timestamp")
    op.drop_column("events", "message_id")
    op.drop_column("events", "thread_id")
    op.drop_column("events", "inbox_id")
    op.drop_column("events", "event_type")

    # Drop messages columns and indexes
    op.drop_index("ix_messages_timestamp", table_name="messages")
    op.drop_column("messages", "size")
    op.drop_column("messages", "headers")
    op.drop_column("messages", "references")
    op.drop_column("messages", "in_reply_to")
    op.drop_column("messages", "extracted_html")
    op.drop_column("messages", "extracted_text")
    op.drop_column("messages", "html")
    op.drop_column("messages", "text")
    op.drop_column("messages", "preview")
    op.drop_column("messages", "subject")
    op.drop_column("messages", "bcc_addresses")
    op.drop_column("messages", "cc_addresses")
    op.drop_column("messages", "to_addresses")
    op.drop_column("messages", "reply_to_addresses")
    op.drop_column("messages", "from_address")
    op.drop_column("messages", "updated_at")
    op.drop_column("messages", "timestamp")
    op.drop_column("messages", "labels")

    # Drop threads columns and indexes
    op.drop_index("ix_threads_inbox_normalized_subject", table_name="threads")
    op.drop_column("threads", "size")
    op.drop_column("threads", "message_count")
    op.drop_column("threads", "last_message_id")
    op.drop_column("threads", "preview")
    op.drop_column("threads", "normalized_subject")
    op.drop_column("threads", "recipients")
    op.drop_column("threads", "senders")
    op.drop_column("threads", "updated_at")
    op.drop_column("threads", "created_at")
    op.drop_column("threads", "sent_timestamp")
    op.drop_column("threads", "received_timestamp")
    op.drop_column("threads", "timestamp")
    op.drop_column("threads", "labels")

    # Drop attachments table
    op.drop_index("ix_attachments_content_id", table_name="attachments")
    op.drop_index("ix_attachments_message_id", table_name="attachments")
    op.drop_table("attachments")
