"""FastAPI application factory (Yggdrasil)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nornweave import __version__


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="NornWeave",
        description="Open-source Inbox-as-a-Service API for AI Agents",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # TODO: include_router for v1 and webhooks
    return app


app = create_app()


def main() -> None:
    """CLI entry point: run uvicorn."""
    import uvicorn
    from nornweave.core.config import get_settings
    settings = get_settings()
    uvicorn.run(
        "nornweave.yggdrasil.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
    )
