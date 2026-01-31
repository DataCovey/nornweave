"""Pytest fixtures for NornWeave tests."""

import pytest
from fastapi.testclient import TestClient

from nornweave.yggdrasil.app import app


@pytest.fixture
def client() -> TestClient:
    """Return a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def api_headers(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Return headers with a test API key. Sets API_KEY for the test."""
    monkeypatch.setenv("API_KEY", "test-api-key")
    return {"Authorization": "Bearer test-api-key", "Content-Type": "application/json"}
