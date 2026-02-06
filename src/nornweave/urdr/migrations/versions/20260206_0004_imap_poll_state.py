"""Add imap_poll_state table for IMAP UID-based polling state tracking.

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-06

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create imap_poll_state table."""
    op.create_table(
        "imap_poll_state",
        sa.Column(
            "inbox_id",
            sa.String(36),
            sa.ForeignKey("inboxes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("last_uid", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uid_validity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mailbox", sa.String(255), nullable=False, server_default="INBOX"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    """Drop imap_poll_state table."""
    op.drop_table("imap_poll_state")
