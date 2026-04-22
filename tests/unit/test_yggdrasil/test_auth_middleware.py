"""Unit tests for API key auth middleware."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from nornweave.core.config import get_settings
from nornweave.yggdrasil.app import create_app
from nornweave.yggdrasil.middleware.auth import APIKeyAuthMiddleware

if TYPE_CHECKING:
    from pytest import MonkeyPatch


def _build_test_app(*, api_key: str) -> FastAPI:
    app = FastAPI()
    app.add_middleware(APIKeyAuthMiddleware, api_key=api_key)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/protected")
    async def protected() -> dict[str, str]:
        return {"status": "protected"}

    @app.post("/webhooks/mailgun")
    async def webhook() -> dict[str, str]:
        return {"status": "webhook"}

    @app.get("/v1/attachments/{attachment_id}/content")
    async def attachment_content(attachment_id: str) -> dict[str, str]:
        return {"attachment_id": attachment_id}

    return app


def test_auth_disabled_when_api_key_not_configured() -> None:
    app = _build_test_app(api_key="")
    client = TestClient(app)

    response = client.get("/v1/protected")
    assert response.status_code == 200
    assert response.json() == {"status": "protected"}


def test_protected_route_requires_api_key() -> None:
    app = _build_test_app(api_key="test-secret")
    client = TestClient(app)

    response = client.get("/v1/protected")
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key"}


def test_bearer_token_allows_protected_route() -> None:
    app = _build_test_app(api_key="test-secret")
    client = TestClient(app)

    response = client.get(
        "/v1/protected",
        headers={"Authorization": "Bearer test-secret"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "protected"}


def test_x_api_key_allows_protected_route() -> None:
    app = _build_test_app(api_key="test-secret")
    client = TestClient(app)

    response = client.get(
        "/v1/protected",
        headers={"X-API-Key": "test-secret"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "protected"}


def test_webhook_path_is_not_api_key_protected() -> None:
    app = _build_test_app(api_key="test-secret")
    client = TestClient(app)

    response = client.post("/webhooks/mailgun")
    assert response.status_code == 200
    assert response.json() == {"status": "webhook"}


def test_signed_attachment_content_path_is_not_api_key_protected() -> None:
    app = _build_test_app(api_key="test-secret")
    client = TestClient(app)

    response = client.get("/v1/attachments/att-123/content")
    assert response.status_code == 200
    assert response.json() == {"attachment_id": "att-123"}


def test_create_app_registers_api_key_middleware(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "test-secret")
    get_settings.cache_clear()
    app = create_app()
    get_settings.cache_clear()

    assert any(m.cls is APIKeyAuthMiddleware for m in app.user_middleware)


def test_create_app_disables_credentials_for_wildcard_cors(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "test-secret")
    monkeypatch.setenv("CORS_ORIGINS", "*")
    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()
    app = create_app()
    get_settings.cache_clear()

    cors = next(m for m in app.user_middleware if m.cls is CORSMiddleware)
    assert cors.kwargs["allow_origins"] == ["*"]
    assert cors.kwargs["allow_credentials"] is False


def test_create_app_enables_credentials_for_explicit_cors_origins(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "test-secret")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()
    app = create_app()
    get_settings.cache_clear()

    cors = next(m for m in app.user_middleware if m.cls is CORSMiddleware)
    assert cors.kwargs["allow_origins"] == ["http://localhost:3000"]
    assert cors.kwargs["allow_credentials"] is True
