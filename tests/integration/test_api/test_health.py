"""Health endpoint integration test."""

import pytest
from fastapi.testclient import TestClient

from nornweave.yggdrasil.app import app


@pytest.mark.integration
def test_health_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.integration
def test_docs_available() -> None:
    client = TestClient(app)
    response = client.get("/docs")
    assert response.status_code == 200
