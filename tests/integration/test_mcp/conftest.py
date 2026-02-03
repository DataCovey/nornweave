"""Pytest fixtures for MCP integration tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest
from starlette.testclient import TestClient

from tests.integration.test_mcp.mock_api import mock_app, seed_mock_data

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(scope="module")
def mock_api_server() -> Generator[str]:
    """Start a mock NornWeave API server for tests.

    Uses ASGI transport for fast, reliable testing without network.
    Returns the base URL of the mock server.
    """
    # Seed mock data before tests
    seed_mock_data()

    # Use httpx ASGI transport - no real server needed
    yield "http://testserver"


@pytest.fixture
def mock_transport() -> httpx.ASGITransport:
    """Get ASGI transport for the mock app."""
    return httpx.ASGITransport(app=mock_app)  # type: ignore[arg-type]


@pytest.fixture
def test_client() -> TestClient:
    """Get a test client for the mock app."""
    return TestClient(mock_app)


@pytest.fixture(autouse=True)
def reset_mock_data_between_tests() -> Generator[None]:
    """Reset mock data between tests for isolation."""
    seed_mock_data()
    yield
