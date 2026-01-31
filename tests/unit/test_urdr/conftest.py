"""Pytest fixtures for URDR storage adapter tests."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from nornweave.urdr.orm import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def sqlite_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create an in-memory SQLite async engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn: Any, _connection_record: Any) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def sqlite_session(
    sqlite_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """Create an async session for testing."""
    session_factory = async_sessionmaker(
        sqlite_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session
        await session.rollback()
