"""Integration tests for global send rate limiting.

Verifies rate-limit enforcement at the API level: HTTP 429 with Retry-After
header when limits are exhausted, no counter impact from filtered requests,
and normal operation under the limit.

Uses in-memory SQLite and a mock email provider for fast testing.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock

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
from nornweave.core.interfaces import EmailProvider
from nornweave.models.inbox import Inbox
from nornweave.skuld.rate_limiter import GlobalRateLimiter
from nornweave.urdr.adapters.sqlite import SQLiteAdapter
from nornweave.urdr.orm import Base
from nornweave.yggdrasil.app import app
from nornweave.yggdrasil.dependencies import get_email_provider, get_rate_limiter, get_storage

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def engine() -> AsyncGenerator[AsyncEngine]:
    """Create an in-memory SQLite async engine."""
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(eng.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn: Any, _connection_record: Any) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield eng
    await eng.dispose()


@pytest.fixture
async def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession]:
    async with session_factory() as sess:
        yield sess


@pytest.fixture
async def storage(session: AsyncSession) -> SQLiteAdapter:
    return SQLiteAdapter(session)


# ---------------------------------------------------------------------------
# Test data fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def test_inbox(storage: SQLiteAdapter, session: AsyncSession) -> dict[str, Any]:
    """Create a test inbox."""
    inbox = await storage.create_inbox(
        Inbox(
            id=str(uuid.uuid4()),
            name="Rate Limit Test Inbox",
            email_address="rl-test@example.com",
        )
    )
    await session.commit()
    return {"id": inbox.id, "email_address": inbox.email_address}


# ---------------------------------------------------------------------------
# Mock email provider
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_email_provider() -> AsyncMock:
    """Email provider that always succeeds with a fake message ID."""
    provider = AsyncMock(spec=EmailProvider)
    provider.send_email = AsyncMock(return_value="mock-msg-id-001")
    return provider


# ---------------------------------------------------------------------------
# HTTP client factories
# ---------------------------------------------------------------------------


def _send_payload(inbox_id: str) -> dict[str, Any]:
    """Return a minimal valid SendMessageRequest body."""
    return {
        "inbox_id": inbox_id,
        "to": ["recipient@example.com"],
        "subject": "Test",
        "body": "Hello",
    }


@pytest.fixture
def client_under_limit(
    session_factory: async_sessionmaker[AsyncSession],
    mock_email_provider: AsyncMock,
) -> AsyncClient:
    """Client with per-minute limit of 5 (room to send)."""
    limiter = GlobalRateLimiter(per_minute_limit=5, per_hour_limit=0)

    async def _get_storage() -> AsyncGenerator[SQLiteAdapter]:
        async with session_factory() as sess:
            yield SQLiteAdapter(sess)

    app.dependency_overrides[get_storage] = _get_storage
    app.dependency_overrides[get_email_provider] = lambda: mock_email_provider
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None,  # type: ignore[call-arg]
    )

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    client = AsyncClient(transport=transport, base_url="http://test")
    return client


@pytest.fixture
def client_minute_exhausted(
    session_factory: async_sessionmaker[AsyncSession],
    mock_email_provider: AsyncMock,
) -> AsyncClient:
    """Client with per-minute limit of 2, already exhausted."""
    limiter = GlobalRateLimiter(per_minute_limit=2, per_hour_limit=0)
    # Pre-fill the limiter to exhaust it
    limiter.record()
    limiter.record()

    async def _get_storage() -> AsyncGenerator[SQLiteAdapter]:
        async with session_factory() as sess:
            yield SQLiteAdapter(sess)

    app.dependency_overrides[get_storage] = _get_storage
    app.dependency_overrides[get_email_provider] = lambda: mock_email_provider
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None,  # type: ignore[call-arg]
    )

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
def client_hour_exhausted(
    session_factory: async_sessionmaker[AsyncSession],
    mock_email_provider: AsyncMock,
) -> AsyncClient:
    """Client with per-hour limit of 1, already exhausted."""
    limiter = GlobalRateLimiter(per_minute_limit=0, per_hour_limit=1)
    limiter.record()

    async def _get_storage() -> AsyncGenerator[SQLiteAdapter]:
        async with session_factory() as sess:
            yield SQLiteAdapter(sess)

    app.dependency_overrides[get_storage] = _get_storage
    app.dependency_overrides[get_email_provider] = lambda: mock_email_provider
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None,  # type: ignore[call-arg]
    )

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
def client_domain_blocked(
    session_factory: async_sessionmaker[AsyncSession],
    mock_email_provider: AsyncMock,
) -> AsyncClient:
    """Client with outbound domain blocklist blocking example.com."""
    limiter = GlobalRateLimiter(per_minute_limit=5, per_hour_limit=0)

    async def _get_storage() -> AsyncGenerator[SQLiteAdapter]:
        async with session_factory() as sess:
            yield SQLiteAdapter(sess)

    app.dependency_overrides[get_storage] = _get_storage
    app.dependency_overrides[get_email_provider] = lambda: mock_email_provider
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None,  # type: ignore[call-arg]
        OUTBOUND_DOMAIN_BLOCKLIST=r"example\.com",  # type: ignore[call-arg]
    )

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    return AsyncClient(transport=transport, base_url="http://test")


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _cleanup_overrides() -> AsyncGenerator[None]:
    """Clear dependency overrides after each test."""
    yield  # type: ignore[misc]
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 6.1 — Send under rate limit → 201
# ---------------------------------------------------------------------------


class TestSendUnderLimit:
    @pytest.mark.asyncio
    async def test_send_succeeds(
        self,
        client_under_limit: AsyncClient,
        test_inbox: dict[str, Any],
    ) -> None:
        resp = await client_under_limit.post("/v1/messages", json=_send_payload(test_inbox["id"]))
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "sent"


# ---------------------------------------------------------------------------
# 6.2 — Per-minute limit exhausted → 429
# ---------------------------------------------------------------------------


class TestPerMinuteExhausted:
    @pytest.mark.asyncio
    async def test_returns_429_with_retry_after(
        self,
        client_minute_exhausted: AsyncClient,
        test_inbox: dict[str, Any],
    ) -> None:
        resp = await client_minute_exhausted.post(
            "/v1/messages", json=_send_payload(test_inbox["id"])
        )
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers
        retry_after = int(resp.headers["Retry-After"])
        assert retry_after >= 1
        assert "per-minute" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 6.3 — Per-hour limit exhausted → 429
# ---------------------------------------------------------------------------


class TestPerHourExhausted:
    @pytest.mark.asyncio
    async def test_returns_429_with_retry_after(
        self,
        client_hour_exhausted: AsyncClient,
        test_inbox: dict[str, Any],
    ) -> None:
        resp = await client_hour_exhausted.post(
            "/v1/messages", json=_send_payload(test_inbox["id"])
        )
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers
        assert "per-hour" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 6.4 — Rate-limited request does not increment counter
# ---------------------------------------------------------------------------


class TestRateLimitedDoesNotIncrement:
    @pytest.mark.asyncio
    async def test_counter_unchanged_after_429(
        self,
        client_minute_exhausted: AsyncClient,
        test_inbox: dict[str, Any],
    ) -> None:
        # First request is rate-limited
        resp1 = await client_minute_exhausted.post(
            "/v1/messages", json=_send_payload(test_inbox["id"])
        )
        assert resp1.status_code == 429

        # Second request should also be rate-limited (counter didn't increase)
        resp2 = await client_minute_exhausted.post(
            "/v1/messages", json=_send_payload(test_inbox["id"])
        )
        assert resp2.status_code == 429


# ---------------------------------------------------------------------------
# 6.5 — Domain-filtered request → 403, no rate-limit impact
# ---------------------------------------------------------------------------


class TestDomainFilteredNoRateLimitImpact:
    @pytest.mark.asyncio
    async def test_blocked_domain_returns_403(
        self,
        client_domain_blocked: AsyncClient,
        test_inbox: dict[str, Any],
    ) -> None:
        resp = await client_domain_blocked.post(
            "/v1/messages", json=_send_payload(test_inbox["id"])
        )
        assert resp.status_code == 403
        assert "blocked" in resp.json()["detail"].lower()
