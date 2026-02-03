"""Unit tests for NornWeave HTTP client."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nornweave.huginn.client import NornWeaveClient
from nornweave.huginn.config import MCPSettings, get_mcp_settings

if TYPE_CHECKING:
    import pytest


class TestMCPSettings:
    """Tests for MCP configuration."""

    def test_default_settings(self) -> None:
        """Test default MCP settings."""
        settings = MCPSettings()
        assert settings.api_url == "http://localhost:8000"
        assert settings.api_key == ""
        assert settings.mcp_host == "0.0.0.0"
        assert settings.mcp_port == 3000

    def test_settings_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading settings from environment variables."""
        monkeypatch.setenv("NORNWEAVE_API_URL", "http://api.example.com:9000")
        monkeypatch.setenv("NORNWEAVE_API_KEY", "test-key-123")
        monkeypatch.setenv("NORNWEAVE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("NORNWEAVE_MCP_PORT", "8080")

        # Clear the cache to pick up new env vars
        get_mcp_settings.cache_clear()

        settings = MCPSettings()
        assert settings.api_url == "http://api.example.com:9000"
        assert settings.api_key == "test-key-123"
        assert settings.mcp_host == "127.0.0.1"
        assert settings.mcp_port == 8080

    def test_get_mcp_settings_cached(self) -> None:
        """Test that get_mcp_settings returns cached instance."""
        get_mcp_settings.cache_clear()
        settings1 = get_mcp_settings()
        settings2 = get_mcp_settings()
        assert settings1 is settings2


class TestNornWeaveClient:
    """Tests for NornWeave HTTP client."""

    def test_client_init_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test client initialization with defaults."""
        monkeypatch.setenv("NORNWEAVE_API_URL", "http://localhost:8000")
        monkeypatch.setenv("NORNWEAVE_API_KEY", "")
        get_mcp_settings.cache_clear()

        client = NornWeaveClient()
        assert client.api_url == "http://localhost:8000"
        assert client.api_key == ""

    def test_client_init_custom_url(self) -> None:
        """Test client initialization with custom URL."""
        client = NornWeaveClient(api_url="http://custom:9000")
        assert client.api_url == "http://custom:9000"

    def test_client_init_strips_trailing_slash(self) -> None:
        """Test that client strips trailing slash from URL."""
        client = NornWeaveClient(api_url="http://example.com/")
        assert client.api_url == "http://example.com"

    def test_client_init_custom_api_key(self) -> None:
        """Test client initialization with custom API key."""
        client = NornWeaveClient(api_url="http://test", api_key="my-key")
        assert client.api_key == "my-key"

    async def test_client_context_manager(self) -> None:
        """Test client as async context manager."""
        async with NornWeaveClient(api_url="http://test") as client:
            assert client._client is None  # Not created until first use
        # Client should be closed after exiting context

    async def test_client_close_idempotent(self) -> None:
        """Test that close can be called multiple times."""
        client = NornWeaveClient(api_url="http://test")
        await client.close()
        await client.close()  # Should not raise
