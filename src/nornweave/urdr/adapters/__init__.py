"""Storage adapters: Postgres, SQLite."""

from nornweave.urdr.adapters.base import BaseSQLAlchemyAdapter
from nornweave.urdr.adapters.sqlite import SQLiteAdapter

# PostgresAdapter requires asyncpg - import conditionally
try:
    from nornweave.urdr.adapters.postgres import PostgresAdapter
except ImportError:
    PostgresAdapter = None  # type: ignore[misc, assignment]

__all__ = [
    "BaseSQLAlchemyAdapter",
    "PostgresAdapter",
    "SQLiteAdapter",
]
