"""PostgreSQL storage adapter (Urdr)."""

from typing import TYPE_CHECKING

from sqlalchemy import or_, select

from nornweave.urdr.adapters.base import BaseSQLAlchemyAdapter
from nornweave.urdr.orm import MessageORM

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from nornweave.models.message import Message


class PostgresAdapter(BaseSQLAlchemyAdapter):
    """PostgreSQL implementation of StorageInterface.

    Uses asyncpg for async database access and ILIKE for case-insensitive search.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session (asyncpg-backed)."""
        super().__init__(session)

    async def search_messages(
        self,
        inbox_id: str,
        query: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        """Search messages using PostgreSQL ILIKE for case-insensitive matching."""
        pattern = f"%{query}%"
        stmt = (
            select(MessageORM)
            .where(
                MessageORM.inbox_id == inbox_id,
                or_(
                    MessageORM.content_clean.ilike(pattern),
                    MessageORM.content_raw.ilike(pattern),
                ),
            )
            .order_by(MessageORM.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [row.to_pydantic() for row in result.scalars().all()]
