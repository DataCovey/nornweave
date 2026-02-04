"""Tests for exception handling."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from nornweave_client import (
    ApiError,
    NornWeave,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from nornweave_client._exceptions import raise_for_status


class TestExceptions:
    """Test exception classes."""

    def test_api_error_attributes(self) -> None:
        """Test ApiError has correct attributes."""
        error = ApiError("Test error", status_code=400, body={"detail": "Bad request"})

        assert error.status_code == 400
        assert error.body == {"detail": "Bad request"}
        assert error.message == "Test error"
        assert str(error) == "400: Test error"

    def test_not_found_error(self) -> None:
        """Test NotFoundError."""
        error = NotFoundError("Resource not found")

        assert error.status_code == 404
        assert isinstance(error, ApiError)

    def test_validation_error(self) -> None:
        """Test ValidationError."""
        error = ValidationError("Invalid data", body={"detail": [{"loc": ["body", "name"]}]})

        assert error.status_code == 422
        assert isinstance(error, ApiError)

    def test_rate_limit_error(self) -> None:
        """Test RateLimitError."""
        error = RateLimitError("Too many requests")

        assert error.status_code == 429
        assert isinstance(error, ApiError)

    def test_server_error(self) -> None:
        """Test ServerError."""
        error = ServerError("Internal server error", status_code=503)

        assert error.status_code == 503
        assert isinstance(error, ApiError)

    def test_error_repr(self) -> None:
        """Test error repr."""
        error = ApiError("Test", status_code=400)
        assert "ApiError" in repr(error)
        assert "400" in repr(error)


class TestRaiseForStatus:
    """Test raise_for_status function."""

    def test_success_codes_no_raise(self) -> None:
        """Test success codes don't raise."""
        for code in [200, 201, 204, 301, 302]:
            raise_for_status(code)  # Should not raise

    def test_404_raises_not_found(self) -> None:
        """Test 404 raises NotFoundError."""
        with pytest.raises(NotFoundError) as exc_info:
            raise_for_status(404, {"detail": "Inbox not found"})

        assert exc_info.value.status_code == 404
        assert "Inbox not found" in str(exc_info.value)

    def test_422_raises_validation_error(self) -> None:
        """Test 422 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            raise_for_status(422, {"detail": "Validation failed"})

        assert exc_info.value.status_code == 422

    def test_429_raises_rate_limit_error(self) -> None:
        """Test 429 raises RateLimitError."""
        with pytest.raises(RateLimitError) as exc_info:
            raise_for_status(429, {"detail": "Rate limit exceeded"})

        assert exc_info.value.status_code == 429

    def test_500_raises_server_error(self) -> None:
        """Test 5xx raises ServerError."""
        with pytest.raises(ServerError) as exc_info:
            raise_for_status(500, {"detail": "Internal error"})

        assert exc_info.value.status_code == 500

    def test_503_raises_server_error(self) -> None:
        """Test 503 raises ServerError with correct code."""
        with pytest.raises(ServerError) as exc_info:
            raise_for_status(503, {"detail": "Service unavailable"})

        assert exc_info.value.status_code == 503

    def test_other_4xx_raises_api_error(self) -> None:
        """Test other 4xx raises generic ApiError."""
        with pytest.raises(ApiError) as exc_info:
            raise_for_status(403, {"detail": "Forbidden"})

        assert exc_info.value.status_code == 403
        assert not isinstance(exc_info.value, NotFoundError)


class TestClientExceptionHandling:
    """Test client properly handles exceptions."""

    def test_client_raises_not_found(self) -> None:
        """Test client raises NotFoundError for 404."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Inbox not found"}

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")

            with pytest.raises(NotFoundError) as exc_info:
                client.inboxes.get("nonexistent")

            assert exc_info.value.status_code == 404

    def test_client_raises_validation_error(self) -> None:
        """Test client raises ValidationError for 422."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "detail": [{"loc": ["body", "name"], "msg": "field required"}]
        }

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")

            with pytest.raises(ValidationError):
                client.inboxes.create(name="", email_username="test")

    def test_client_raises_server_error(self) -> None:
        """Test client raises ServerError for 5xx."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal server error"}

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")

            with pytest.raises(ServerError) as exc_info:
                _ = client.inboxes.list().items

            assert exc_info.value.status_code == 500

    def test_exception_preserves_body(self) -> None:
        """Test exception preserves response body."""
        error_body = {
            "detail": [
                {"loc": ["body", "name"], "msg": "field required", "type": "missing"}
            ]
        }

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 422
        mock_response.json.return_value = error_body

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")

            with pytest.raises(ValidationError) as exc_info:
                client.inboxes.create(name="", email_username="test")

            assert exc_info.value.body == error_body
