"""NornWeave CLI.

Provides commands for running the API server and MCP server.
"""

import os
import sys
from typing import Literal

import click


@click.group()
@click.version_option()
def cli() -> None:
    """NornWeave - Inbox-as-a-Service API for AI Agents.

    Run the API server or MCP server for AI agent integration.
    """


@cli.command("api")
@click.option(
    "--host",
    default="0.0.0.0",
    help="Host to bind to",
    show_default=True,
)
@click.option(
    "--port",
    default=8000,
    type=int,
    help="Port to listen on",
    show_default=True,
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload for development",
)
@click.option(
    "--demo",
    is_flag=True,
    help="Run in demo/sandbox mode: mock mailbox, no .env or real email provider required (local use only).",
)
def api_cmd(host: str, port: int, reload: bool, demo: bool) -> None:
    """Run the NornWeave REST API server.

    This starts the FastAPI server that handles webhooks, REST API requests,
    and serves as the backend for the MCP server.

    Examples:

        nornweave api

        nornweave api --demo

        nornweave api --port 9000

        nornweave api --reload
    """
    if demo:
        os.environ["EMAIL_PROVIDER"] = "demo"
        os.environ["EMAIL_DOMAIN"] = "demo.nornweave.local"
    import uvicorn

    uvicorn.run(
        "nornweave.yggdrasil.app:app",
        host=host,
        port=port,
        reload=reload,
    )


@cli.command("mcp")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "http"]),
    default="stdio",
    help="MCP transport type",
    show_default=True,
)
@click.option(
    "--host",
    default="0.0.0.0",
    help="Host to bind to (SSE/HTTP only)",
    show_default=True,
)
@click.option(
    "--port",
    default=3000,
    type=int,
    help="Port to listen on (SSE/HTTP only)",
    show_default=True,
)
@click.option(
    "--api-url",
    envvar="NORNWEAVE_API_URL",
    default="http://localhost:8000",
    help="NornWeave API URL",
    show_default=True,
)
def mcp_cmd(
    transport: Literal["stdio", "sse", "http"],
    host: str,
    port: int,
    api_url: str,
) -> None:
    """Run the NornWeave MCP server.

    This starts the Model Context Protocol server that allows AI agents
    (Claude, Cursor, LangChain) to interact with email.

    Transports:

        stdio   - Standard input/output (default). For Claude Desktop, Cursor.

        sse     - Server-Sent Events. For web-based MCP clients.

        http    - Streamable HTTP. For cloud deployments, LangChain.

    Environment Variables:

        NORNWEAVE_API_URL   - NornWeave API base URL (default: http://localhost:8000)

        NORNWEAVE_API_KEY   - API key for authentication (optional)

    Examples:

        nornweave mcp

        nornweave mcp --transport sse --port 3000

        nornweave mcp --transport http --host 127.0.0.1 --port 8080

        nornweave mcp --api-url http://api.example.com:8000

    Claude Desktop / Cursor Configuration:

        {
          "mcpServers": {
            "nornweave": {
              "command": "nornweave",
              "args": ["mcp"]
            }
          }
        }
    """
    # Set API URL in environment for the MCP server to pick up
    import os

    os.environ["NORNWEAVE_API_URL"] = api_url

    try:
        from nornweave.huginn.server import serve
    except ImportError as e:
        click.echo(
            "Error: MCP dependencies not installed. Install with: pip install nornweave[mcp]",
            err=True,
        )
        click.echo(f"Details: {e}", err=True)
        sys.exit(1)

    if transport == "stdio":
        click.echo("Starting MCP server (stdio transport)...", err=True)
        click.echo(f"API URL: {api_url}", err=True)
    else:
        click.echo(f"Starting MCP server ({transport} transport)...", err=True)
        click.echo(f"Listening on {host}:{port}", err=True)
        click.echo(f"API URL: {api_url}", err=True)

    serve(transport=transport, host=host, port=port)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


# Legacy entry point for backwards compatibility
def run_api() -> None:
    """Run the API server (legacy entry point)."""
    import uvicorn

    from nornweave.core.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "nornweave.yggdrasil.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
    )


if __name__ == "__main__":
    main()
