"""MCP server configuration.

Configuration is loaded from environment variables:
- NORNWEAVE_API_URL: Base URL for the NornWeave REST API (default: http://localhost:8000)
- NORNWEAVE_API_KEY: API key for authentication (optional)
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPSettings(BaseSettings):
    """MCP server configuration from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API connection
    api_url: str = Field(
        default="http://localhost:8000",
        alias="NORNWEAVE_API_URL",
        description="Base URL for the NornWeave REST API",
    )
    api_key: str = Field(
        default="",
        alias="NORNWEAVE_API_KEY",
        description="API key for authentication (optional)",
    )

    # MCP server settings
    mcp_host: str = Field(
        default="0.0.0.0",
        alias="NORNWEAVE_MCP_HOST",
        description="Host to bind MCP server (SSE/HTTP transports)",
    )
    mcp_port: int = Field(
        default=3000,
        alias="NORNWEAVE_MCP_PORT",
        description="Port for MCP server (SSE/HTTP transports)",
    )


@lru_cache
def get_mcp_settings() -> MCPSettings:
    """Get cached MCP settings instance."""
    return MCPSettings()
