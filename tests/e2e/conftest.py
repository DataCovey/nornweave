"""E2E test fixtures with dependency overrides.

Provides:
- Isolated in-memory SQLite database per test
- MockEmailProvider injected into the FastAPI app
- Async test client for API requests
- Direct storage access for assertions
"""

from collections.abc import AsyncGenerator  # noqa: TC003 - needed at runtime for pytest fixtures
from typing import TYPE_CHECKING, Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from nornweave.core.config import Settings, get_settings
from nornweave.urdr.adapters.sqlite import SQLiteAdapter
from nornweave.urdr.orm import Base
from nornweave.yggdrasil.dependencies import get_email_provider, get_storage
from tests.mocks.email_provider import MockEmailProvider

# Test email domain for E2E tests
TEST_EMAIL_DOMAIN = "test.nornweave.local"

if TYPE_CHECKING:
    from fastapi import FastAPI


# -----------------------------------------------------------------------------
# Database fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
async def e2e_engine() -> AsyncGenerator[AsyncEngine]:
    """Create an in-memory SQLite async engine for E2E testing."""
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
async def e2e_session_factory(
    e2e_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create a session factory for E2E tests."""
    return async_sessionmaker(
        e2e_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
async def e2e_session(
    e2e_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession]:
    """Create an async session for direct storage access in tests."""
    async with e2e_session_factory() as session:
        yield session


@pytest.fixture
async def e2e_storage(e2e_session: AsyncSession) -> SQLiteAdapter:
    """Get a storage adapter for direct database assertions."""
    return SQLiteAdapter(e2e_session)


# -----------------------------------------------------------------------------
# Mock provider fixture
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_provider() -> MockEmailProvider:
    """Create a mock email provider for testing."""
    return MockEmailProvider(domain=TEST_EMAIL_DOMAIN)


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with test domain."""
    return Settings(
        environment="test",
        db_driver="sqlite",
        email_provider="mailgun",
        email_domain=TEST_EMAIL_DOMAIN,
    )


# -----------------------------------------------------------------------------
# FastAPI app with overrides
# -----------------------------------------------------------------------------


@pytest.fixture
def e2e_app(
    e2e_session_factory: async_sessionmaker[AsyncSession],
    mock_provider: MockEmailProvider,
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> FastAPI:
    """Create a FastAPI app with test dependencies injected."""
    # Set environment variable for test domain before clearing cache
    monkeypatch.setenv("EMAIL_DOMAIN", TEST_EMAIL_DOMAIN)

    # Clear the LRU cache so it picks up the new env var
    get_settings.cache_clear()

    # Import here to avoid circular imports
    from nornweave.yggdrasil.app import create_app

    app = create_app()

    # Override storage dependency to use our test database
    async def override_get_storage() -> AsyncGenerator[SQLiteAdapter]:
        async with e2e_session_factory() as session:
            yield SQLiteAdapter(session)
            await session.commit()

    # Override email provider to use mock
    def override_get_email_provider() -> MockEmailProvider:
        return mock_provider

    # Override settings to use test domain
    def override_get_settings() -> Settings:
        return test_settings

    app.dependency_overrides[get_storage] = override_get_storage
    app.dependency_overrides[get_email_provider] = override_get_email_provider
    app.dependency_overrides[get_settings] = override_get_settings

    return app


@pytest.fixture
async def e2e_client(e2e_app: FastAPI) -> AsyncGenerator[AsyncClient]:
    """Create an async HTTP client for E2E tests."""
    # Use ASGI transport for async client
    transport = ASGITransport(app=e2e_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client


# -----------------------------------------------------------------------------
# Convenience fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def sample_inbox_data() -> dict[str, str]:
    """Sample data for creating an inbox."""
    return {
        "name": "Test Support",
        "email_username": "support",
    }


@pytest.fixture
def sample_email_data() -> dict[str, Any]:
    """Sample data for sending an email."""
    return {
        "to": ["alice@example.com"],
        "subject": "Hello from NornWeave",
        "body": "This is a test email.\n\nBest regards,\nSupport Team",
    }
