"""FastAPI application factory (Yggdrasil)."""

import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nornweave import __version__
from nornweave.core.config import get_settings
from nornweave.yggdrasil.dependencies import close_database, init_database

# Configure nornweave loggers to output to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
# Ensure nornweave namespace logs at DEBUG in development
logging.getLogger("nornweave").setLevel(logging.DEBUG)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from nornweave.verdandi.imap_poller import ImapPoller

# Module-level reference to the IMAP poller for use by the sync endpoint
_imap_poller: ImapPoller | None = None


def get_imap_poller() -> ImapPoller | None:
    """Get the running IMAP poller instance (or None if not using imap-smtp)."""
    return _imap_poller


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan: initialize DB and optionally start IMAP poller."""
    global _imap_poller

    settings = get_settings()
    await init_database(settings)

    poller_task: asyncio.Task[None] | None = None

    if settings.email_provider == "imap-smtp":
        from nornweave.verdandi.imap_poller import ImapPoller

        _imap_poller = ImapPoller(settings)
        poller_task = asyncio.create_task(_imap_poller.run())

    yield

    if poller_task:
        poller_task.cancel()
        with suppress(asyncio.CancelledError):
            await poller_task
        _imap_poller = None

    await close_database()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="NornWeave",
        description="Open-source Inbox-as-a-Service API for AI Agents",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # Include API routers
    from nornweave.yggdrasil.routes.v1 import attachments, inboxes, messages, search, threads

    app.include_router(inboxes.router, prefix="/v1", tags=["inboxes"])
    app.include_router(threads.router, prefix="/v1", tags=["threads"])
    app.include_router(messages.router, prefix="/v1", tags=["messages"])
    app.include_router(search.router, prefix="/v1", tags=["search"])
    app.include_router(attachments.router, prefix="/v1", tags=["attachments"])

    # Include webhook routers
    from nornweave.yggdrasil.routes.webhooks import mailgun, resend, sendgrid, ses

    app.include_router(mailgun.router, prefix="/webhooks", tags=["webhooks"])
    app.include_router(sendgrid.router, prefix="/webhooks", tags=["webhooks"])
    app.include_router(ses.router, prefix="/webhooks", tags=["webhooks"])
    app.include_router(resend.router, prefix="/webhooks", tags=["webhooks"])

    return app


app = create_app()


def main() -> None:
    """CLI entry point: run uvicorn."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "nornweave.yggdrasil.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
    )
