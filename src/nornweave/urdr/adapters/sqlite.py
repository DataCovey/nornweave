"""SQLite storage adapter (Urdr) for local development."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from nornweave.models.message import Message
from nornweave.urdr.adapters.base import BaseSQLAlchemyAdapter
from nornweave.urdr.orm import MessageORM


class SQLiteAdapter(BaseSQLAlchemyAdapter):
    """SQLite implementation of StorageInterface.

    Uses aiosqlite for async database access. SQLite LIKE is case-insensitive
    by default for ASCII, but we use lower() for consistent behavior.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session (aiosqlite-backed)."""
        super().__init__(session)

    async def search_messages(
        self,
        inbox_id: str,
        query: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        """Search messages using SQLite LIKE with lower() for case-insensitive matching."""
        pattern = f"%{query.lower()}%"
        stmt = (
            select(MessageORM)
            .where(
                MessageORM.inbox_id == inbox_id,
                or_(
                    func.lower(MessageORM.content_clean).like(pattern),
                    func.lower(MessageORM.content_raw).like(pattern),
                ),
            )
            .order_by(MessageORM.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [row.to_pydantic() for row in result.scalars().all()]
