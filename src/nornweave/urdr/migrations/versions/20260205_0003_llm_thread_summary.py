"""Add LLM thread summary: summary column on threads, llm_token_usage table.

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-05

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add summary column to threads and create llm_token_usage table."""
    # ==========================================================================
    # Add summary column to threads table
    # ==========================================================================
    op.add_column(
        "threads",
        sa.Column("summary", sa.Text(), nullable=True),
    )

    # ==========================================================================
    # Create llm_token_usage table
    # ==========================================================================
    op.create_table(
        "llm_token_usage",
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("date"),
    )


def downgrade() -> None:
    """Remove summary column from threads and drop llm_token_usage table."""
    op.drop_table("llm_token_usage")
    op.drop_column("threads", "summary")
