"""FastAPI application factory (Yggdrasil)."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nornweave import __version__
from nornweave.core.config import get_settings
from nornweave.yggdrasil.dependencies import close_database, init_database


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: initialize and close database connections."""
    settings = get_settings()
    await init_database(settings)
    yield
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
    from nornweave.yggdrasil.routes.v1 import inboxes, messages, search, threads

    app.include_router(inboxes.router, prefix="/v1", tags=["inboxes"])
    app.include_router(threads.router, prefix="/v1", tags=["threads"])
    app.include_router(messages.router, prefix="/v1", tags=["messages"])
    app.include_router(search.router, prefix="/v1", tags=["search"])

    # Include webhook routers
    from nornweave.yggdrasil.routes.webhooks import mailgun, sendgrid, ses

    app.include_router(mailgun.router, prefix="/webhooks", tags=["webhooks"])
    app.include_router(sendgrid.router, prefix="/webhooks", tags=["webhooks"])
    app.include_router(ses.router, prefix="/webhooks", tags=["webhooks"])

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
