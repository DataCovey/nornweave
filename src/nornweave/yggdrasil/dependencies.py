"""Dependency injection (storage, provider)."""

from collections.abc import AsyncGenerator  # noqa: TC003 - needed at runtime
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, Request
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
from nornweave.urdr.adapters.postgres import PostgresAdapter
from nornweave.urdr.adapters.sqlite import SQLiteAdapter

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
    """Initialize database engine and session factory."""
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

    # Enable foreign keys for SQLite
    if settings.db_driver == "sqlite":
        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_conn: Any, _connection_record: Any) -> None:
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()


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
    if settings.db_driver == "postgres":
        return PostgresAdapter(session)
    elif settings.db_driver == "sqlite":
        return SQLiteAdapter(session)
    else:
        raise ValueError(f"Unknown db_driver: {settings.db_driver}")


async def get_email_provider(
    settings: Settings = Depends(get_settings),
) -> EmailProvider:
    """FastAPI dependency to get the configured email provider."""
    # Import here to avoid circular imports
    from nornweave.adapters.mailgun import MailgunAdapter
    from nornweave.adapters.resend import ResendAdapter
    from nornweave.adapters.sendgrid import SendGridAdapter
    from nornweave.adapters.ses import SESAdapter

    provider = settings.email_provider

    if provider == "mailgun":
        return MailgunAdapter(
            api_key=settings.mailgun_api_key,
            domain=settings.mailgun_domain,
        )
    elif provider == "sendgrid":
        return SendGridAdapter(api_key=settings.sendgrid_api_key)
    elif provider == "ses":
        return SESAdapter(
            access_key_id=settings.aws_access_key_id,
            secret_access_key=settings.aws_secret_access_key,
            region=settings.aws_region,
        )
    elif provider == "resend":
        return ResendAdapter(
            api_key=settings.resend_api_key,
            webhook_secret=settings.resend_webhook_secret,
        )
    else:
        raise ValueError(f"Unknown email_provider: {provider}")
