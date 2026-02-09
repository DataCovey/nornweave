"""Tests for yggdrasil dependency injection (database init, etc.)."""

from __future__ import annotations

import pytest
from sqlalchemy import inspect, text

from nornweave.core.config import Settings
from nornweave.yggdrasil.dependencies import (
    close_database,
    get_database_url,
    init_database,
)

# ---------------------------------------------------------------------------
# get_database_url
# ---------------------------------------------------------------------------


class TestGetDatabaseUrl:
    """Tests for get_database_url()."""

    def test_sqlite_default_url_when_empty(self) -> None:
        """When DB_DRIVER=sqlite and DATABASE_URL is empty, a default is used."""
        settings = Settings(DB_DRIVER="sqlite", DATABASE_URL="")
        url = get_database_url(settings)
        assert url == "sqlite+aiosqlite:///./nornweave.db"

    def test_postgres_requires_database_url(self) -> None:
        """When DB_DRIVER=postgres and DATABASE_URL is empty, raise ValueError."""
        settings = Settings(DB_DRIVER="postgres", DATABASE_URL="")
        with pytest.raises(ValueError, match="DATABASE_URL must be set for PostgreSQL"):
            get_database_url(settings)

    def test_sqlite_explicit_url_preserved(self) -> None:
        """An explicit SQLite DATABASE_URL is used as-is (with async driver)."""
        settings = Settings(
            DB_DRIVER="sqlite",
            DATABASE_URL="sqlite+aiosqlite:///./custom.db",
        )
        url = get_database_url(settings)
        assert url == "sqlite+aiosqlite:///./custom.db"

    def test_sqlite_url_gets_async_driver(self) -> None:
        """A plain sqlite:// URL is upgraded to sqlite+aiosqlite://."""
        settings = Settings(
            DB_DRIVER="sqlite",
            DATABASE_URL="sqlite:///./plain.db",
        )
        url = get_database_url(settings)
        assert "aiosqlite" in url

    def test_postgres_url_gets_async_driver(self) -> None:
        """A plain postgresql:// URL is upgraded to postgresql+asyncpg://."""
        settings = Settings(
            DB_DRIVER="postgres",
            DATABASE_URL="postgresql://user:pass@localhost/db",
        )
        url = get_database_url(settings)
        assert "asyncpg" in url


# ---------------------------------------------------------------------------
# init_database - SQLite auto-creates tables
# ---------------------------------------------------------------------------


class TestInitDatabaseSqliteAutoCreate:
    """Verify that init_database() auto-creates tables for SQLite."""

    @pytest.fixture(autouse=True)
    async def _cleanup(self) -> None:
        """Ensure the database is closed after each test."""
        yield
        await close_database()

    @pytest.mark.asyncio
    async def test_sqlite_tables_created_automatically(self) -> None:
        """init_database with SQLite should create all ORM tables."""
        settings = Settings(
            DB_DRIVER="sqlite",
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
        )
        await init_database(settings)

        # Import after init so the engine exists
        from nornweave.yggdrasil.dependencies import _engine

        assert _engine is not None

        async with _engine.connect() as conn:
            table_names = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )

        expected_tables = {"inboxes", "threads", "messages", "attachments", "events"}
        assert expected_tables.issubset(set(table_names)), (
            f"Missing tables: {expected_tables - set(table_names)}"
        )

    @pytest.mark.asyncio
    async def test_sqlite_tables_usable_after_init(self) -> None:
        """After init_database, we should be able to query tables without errors."""
        settings = Settings(
            DB_DRIVER="sqlite",
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
        )
        await init_database(settings)

        from nornweave.yggdrasil.dependencies import _session_factory

        assert _session_factory is not None

        async with _session_factory() as session:
            # This is the exact query that was failing before the fix
            result = await session.execute(text("SELECT count(*) FROM inboxes"))
            count = result.scalar()
            assert count == 0

    @pytest.mark.asyncio
    async def test_sqlite_auto_create_is_idempotent(self) -> None:
        """Calling init_database twice on the same SQLite DB should not error."""
        settings = Settings(
            DB_DRIVER="sqlite",
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
        )
        await init_database(settings)
        # Close and re-init on a fresh in-memory DB (same URL, new engine)
        await close_database()
        await init_database(settings)

        from nornweave.yggdrasil.dependencies import _engine

        assert _engine is not None
