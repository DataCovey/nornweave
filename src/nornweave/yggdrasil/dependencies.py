"""Dependency injection (storage, provider)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator  # noqa: TC003 - needed at runtime
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from nornweave.skuld.rate_limiter import GlobalRateLimiter

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from nornweave.core.config import Settings, get_settings
from nornweave.core.interfaces import (  # noqa: TC001 - needed at runtime for FastAPI
    EmailProvider,
    StorageInterface,
)

# -----------------------------------------------------------------------------
# Database engine management
# -----------------------------------------------------------------------------
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_database_url(settings: Settings) -> str:
    """Get database URL from settings with validation."""
    url = settings.database_url

    if not url:
        if settings.db_driver == "sqlite":
            # Default SQLite path for local development
            url = "sqlite+aiosqlite:///./nornweave.db"
        else:
            raise ValueError("DATABASE_URL must be set for PostgreSQL")

    # Validate URL matches driver
    if settings.db_driver == "postgres":
        if not url.startswith("postgresql"):
            raise ValueError(
                f"DATABASE_URL must start with 'postgresql' for postgres driver, got: {url}"
            )
        # Ensure async driver
        if "asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://")
    elif settings.db_driver == "sqlite":
        if not url.startswith("sqlite"):
            raise ValueError(f"DATABASE_URL must start with 'sqlite' for sqlite driver, got: {url}")
        # Ensure async driver
        if "aiosqlite" not in url:
            url = url.replace("sqlite://", "sqlite+aiosqlite://")

    return url


async def init_database(settings: Settings | None = None) -> None:
    """Initialize database engine and session factory.

    For SQLite, tables are auto-created if they don't exist so that
    ``nornweave api`` works out of the box with zero configuration.
    PostgreSQL users should run Alembic migrations instead.
    """
    global _engine, _session_factory

    if settings is None:
        settings = get_settings()

    url = get_database_url(settings)

    # Engine configuration
    engine_kwargs: dict[str, Any] = {
        "echo": settings.environment == "development" and settings.log_level == "DEBUG",
    }

    # SQLite-specific settings
    if settings.db_driver == "sqlite":
        engine_kwargs["connect_args"] = {"check_same_thread": False}

    _engine = create_async_engine(url, **engine_kwargs)
    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # SQLite-specific setup
    if settings.db_driver == "sqlite":
        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_conn: Any, _connection_record: Any) -> None:
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        # Auto-create tables for SQLite so `nornweave api` works without
        # a separate migration step.  create_all is idempotent — existing
        # tables are left untouched.
        from nornweave.urdr.orm import Base

        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


async def close_database() -> None:
    """Close database engine."""
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession]:
    """Get a database session (context manager)."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def _storage_for_session(session: AsyncSession, settings: Settings) -> StorageInterface:
    """Build the storage adapter for a given session and settings (for use outside request context)."""
    if settings.db_driver == "postgres":
        try:
            from nornweave.urdr.adapters.postgres import PostgresAdapter
        except ImportError as e:
            raise ImportError(
                "PostgreSQL support requires additional dependencies. "
                "Install with: pip install nornweave[postgres]"
            ) from e
        return PostgresAdapter(session)
    if settings.db_driver == "sqlite":
        from nornweave.urdr.adapters.sqlite import SQLiteAdapter

        return SQLiteAdapter(session)
    raise ValueError(f"Unknown db_driver: {settings.db_driver}")


async def ensure_demo_inbox(settings: Settings) -> None:
    """Ensure the demo inbox (demo@demo.nornweave.local) exists. Idempotent; call when provider is demo."""
    from nornweave.models.inbox import Inbox

    async with get_session() as session:
        storage = _storage_for_session(session, settings)
        existing = await storage.get_inbox_by_email("demo@demo.nornweave.local")
        if existing:
            return
        inbox = Inbox(
            id=str(uuid.uuid4()),
            email_address="demo@demo.nornweave.local",
            name="Demo Inbox",
            provider_config={},
        )
        await storage.create_inbox(inbox)


# -----------------------------------------------------------------------------
# FastAPI Dependencies
# -----------------------------------------------------------------------------
async def get_db_session(_request: Request) -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency to get a database session."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized")

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_storage(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> StorageInterface:
    """FastAPI dependency to get the configured storage adapter."""
    return _storage_for_session(session, settings)


_rate_limiter: GlobalRateLimiter | None = None


def get_rate_limiter(
    settings: Settings = Depends(get_settings),
) -> GlobalRateLimiter:
    """FastAPI dependency returning a singleton GlobalRateLimiter."""
    global _rate_limiter

    if _rate_limiter is None:
        from nornweave.skuld.rate_limiter import GlobalRateLimiter

        _rate_limiter = GlobalRateLimiter(
            per_minute_limit=settings.global_send_rate_limit_per_minute,
            per_hour_limit=settings.global_send_rate_limit_per_hour,
        )
    return _rate_limiter


def _check_provider_credentials(settings: Settings) -> None:
    """Validate that required credentials are set for the configured email provider.

    Raises ``HTTPException(422)`` with actionable detail if credentials are missing.
    """
    provider = settings.email_provider
    if provider == "demo":
        return
    missing: list[str] = []

    if provider == "mailgun":
        if not settings.mailgun_api_key:
            missing.append("MAILGUN_API_KEY")
        if not settings.mailgun_domain:
            missing.append("MAILGUN_DOMAIN")
    elif provider == "ses":
        if not settings.aws_access_key_id:
            missing.append("AWS_ACCESS_KEY_ID")
        if not settings.aws_secret_access_key:
            missing.append("AWS_SECRET_ACCESS_KEY")
    elif provider == "sendgrid":
        if not settings.sendgrid_api_key:
            missing.append("SENDGRID_API_KEY")
    elif provider == "resend":
        if not settings.resend_api_key:
            missing.append("RESEND_API_KEY")
    elif provider == "imap-smtp":
        if not settings.smtp_host:
            missing.append("SMTP_HOST")
        if not settings.imap_host:
            missing.append("IMAP_HOST")

    if missing:
        raise HTTPException(
            status_code=422,
            detail=(
                f"EMAIL_PROVIDER is set to '{provider}' but required credentials are missing: "
                f"{', '.join(missing)}. "
                f"Set them in your .env file. See the Configuration docs for details."
            ),
        )


async def get_email_provider(
    settings: Settings = Depends(get_settings),
) -> EmailProvider:
    """FastAPI dependency to get the configured email provider.

    Validates that required credentials are present before constructing the
    adapter.  This turns silent send-time failures into clear HTTP 422
    errors.
    """
    # Lazy-import only the adapter for the configured provider so optional
    # dependencies (e.g. cryptography for SendGrid) are not required when
    # using other providers.
    _check_provider_credentials(settings)

    provider = settings.email_provider

    if provider == "mailgun":
        from nornweave.adapters.mailgun import MailgunAdapter

        return MailgunAdapter(
            api_key=settings.mailgun_api_key,
            domain=settings.mailgun_domain,
        )
    elif provider == "sendgrid":
        from nornweave.adapters.sendgrid import SendGridAdapter

        return SendGridAdapter(api_key=settings.sendgrid_api_key)
    elif provider == "ses":
        from nornweave.adapters.ses import SESAdapter

        return SESAdapter(
            access_key_id=settings.aws_access_key_id,
            secret_access_key=settings.aws_secret_access_key,
            region=settings.aws_region,
        )
    elif provider == "resend":
        from nornweave.adapters.resend import ResendAdapter

        return ResendAdapter(
            api_key=settings.resend_api_key,
            webhook_secret=settings.resend_webhook_secret,
        )
    elif provider == "imap-smtp":
        from nornweave.adapters.smtp_imap import SmtpImapAdapter

        return SmtpImapAdapter(settings=settings)
    elif provider == "demo":
        from nornweave.adapters.demo import DemoAdapter

        return DemoAdapter(domain=settings.email_domain or "demo.nornweave.local")
    else:
        raise ValueError(f"Unknown email_provider: {provider}")
