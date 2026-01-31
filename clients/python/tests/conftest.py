"""Shared test fixtures for NornWeave client tests."""

from __future__ import annotations

from typing import Any, Generator
from unittest.mock import MagicMock, patch

import httpx
import pytest


@pytest.fixture
def mock_response() -> MagicMock:
    """Create a mock httpx.Response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.headers = httpx.Headers({"content-type": "application/json"})
    return response


@pytest.fixture
def mock_client() -> Generator[MagicMock, None, None]:
    """Create a mock httpx.Client."""
    with patch("httpx.Client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_async_client() -> Generator[MagicMock, None, None]:
    """Create a mock httpx.AsyncClient."""
    with patch("httpx.AsyncClient") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


# Sample data fixtures


@pytest.fixture
def sample_inbox() -> dict[str, Any]:
    """Sample inbox data."""
    return {
        "id": "inbox-123",
        "email_address": "support@example.nornweave.io",
        "name": "Support",
        "provider_config": {"domain": "example.nornweave.io"},
    }


@pytest.fixture
def sample_inbox_list(sample_inbox: dict[str, Any]) -> dict[str, Any]:
    """Sample inbox list response."""
    return {
        "items": [sample_inbox],
        "count": 1,
    }


@pytest.fixture
def sample_message() -> dict[str, Any]:
    """Sample message data."""
    return {
        "id": "msg-123",
        "thread_id": "thread-456",
        "inbox_id": "inbox-123",
        "direction": "inbound",
        "provider_message_id": "<123@mail.example.com>",
        "content_raw": "<p>Hello</p>",
        "content_clean": "Hello",
        "metadata": {"from": "user@example.com"},
        "created_at": "2024-01-15T10:30:00Z",
    }


@pytest.fixture
def sample_message_list(sample_message: dict[str, Any]) -> dict[str, Any]:
    """Sample message list response."""
    return {
        "items": [sample_message],
        "count": 1,
    }


@pytest.fixture
def sample_send_response() -> dict[str, Any]:
    """Sample send message response."""
    return {
        "id": "msg-789",
        "thread_id": "thread-456",
        "provider_message_id": "<789@mail.example.com>",
        "status": "sent",
    }


@pytest.fixture
def sample_thread_summary() -> dict[str, Any]:
    """Sample thread summary data."""
    return {
        "id": "thread-456",
        "inbox_id": "inbox-123",
        "subject": "Test Thread",
        "last_message_at": "2024-01-15T10:30:00Z",
        "participant_hash": "abc123",
        "message_count": 3,
    }


@pytest.fixture
def sample_thread_list(sample_thread_summary: dict[str, Any]) -> dict[str, Any]:
    """Sample thread list response."""
    return {
        "items": [sample_thread_summary],
        "count": 1,
    }


@pytest.fixture
def sample_thread_detail() -> dict[str, Any]:
    """Sample thread detail with messages."""
    return {
        "id": "thread-456",
        "subject": "Test Thread",
        "messages": [
            {
                "role": "user",
                "author": "user@example.com",
                "content": "Hello, I need help.",
                "timestamp": "2024-01-15T10:30:00Z",
            },
            {
                "role": "assistant",
                "author": "support@example.nornweave.io",
                "content": "Hi! How can I help?",
                "timestamp": "2024-01-15T10:35:00Z",
            },
        ],
    }


@pytest.fixture
def sample_search_result() -> dict[str, Any]:
    """Sample search result item."""
    return {
        "id": "msg-123",
        "thread_id": "thread-456",
        "inbox_id": "inbox-123",
        "direction": "inbound",
        "content_clean": "Hello, I need help with my invoice.",
        "created_at": "2024-01-15T10:30:00Z",
        "metadata": {},
    }


@pytest.fixture
def sample_search_response(sample_search_result: dict[str, Any]) -> dict[str, Any]:
    """Sample search response."""
    return {
        "items": [sample_search_result],
        "count": 1,
        "query": "invoice",
    }


@pytest.fixture
def health_response() -> dict[str, Any]:
    """Sample health response."""
    return {"status": "ok"}
