"""Alembic migration environment."""

import os
import re
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import ORM models to ensure metadata is populated
from nornweave.urdr.orm import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target_metadata from ORM Base
target_metadata = Base.metadata


def get_url() -> str:
    """Get database URL from environment or config.

    Converts async URLs to sync for Alembic:
    - postgresql+asyncpg:// -> postgresql://
    - sqlite+aiosqlite:// -> sqlite://
    """
    # First try environment variable
    url = os.environ.get("DATABASE_URL", "")

    # Fall back to alembic.ini if not set
    if not url:
        url = config.get_main_option("sqlalchemy.url", "")

    if not url:
        raise ValueError(
            "DATABASE_URL environment variable or sqlalchemy.url in alembic.ini required"
        )

    # Convert async URL to sync for Alembic
    url = re.sub(r"^postgresql\+asyncpg://", "postgresql://", url)
    url = re.sub(r"^sqlite\+aiosqlite://", "sqlite://", url)

    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # Required for SQLite ALTER TABLE support
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a
    connection with the context.
    """
    # Override the URL in config
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # Required for SQLite ALTER TABLE support
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
