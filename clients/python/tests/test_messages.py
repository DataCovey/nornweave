"""Tests for messages resource."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from nornweave_client import NornWeave
from nornweave_client._types import Message, SendMessageResponse


class TestMessagesResource:
    """Test synchronous message operations."""

    def test_send_message(self, sample_send_response: dict[str, Any]) -> None:
        """Test sending a message."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.json.return_value = sample_send_response

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            result = client.messages.send(
                inbox_id="inbox-123",
                to=["recipient@example.com"],
                subject="Hello",
                body="Test message in **Markdown**.",
            )

            assert isinstance(result, SendMessageResponse)
            assert result.id == "msg-789"
            assert result.thread_id == "thread-456"
            assert result.status == "sent"

            # Verify request body
            call_args = mock_httpx.request.call_args
            assert call_args.kwargs["json"]["inbox_id"] == "inbox-123"
            assert call_args.kwargs["json"]["to"] == ["recipient@example.com"]
            assert call_args.kwargs["json"]["subject"] == "Hello"

    def test_send_message_reply(self, sample_send_response: dict[str, Any]) -> None:
        """Test sending a reply to a thread."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.json.return_value = sample_send_response

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            result = client.messages.send(
                inbox_id="inbox-123",
                to=["recipient@example.com"],
                subject="Re: Hello",
                body="Reply message",
                reply_to_thread_id="thread-456",
            )

            assert result.thread_id == "thread-456"

            # Verify reply_to_thread_id was included
            call_args = mock_httpx.request.call_args
            assert call_args.kwargs["json"]["reply_to_thread_id"] == "thread-456"

    def test_get_message(self, sample_message: dict[str, Any]) -> None:
        """Test getting a message by ID."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_message

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            message = client.messages.get("msg-123")

            assert isinstance(message, Message)
            assert message.id == "msg-123"
            assert message.thread_id == "thread-456"
            assert message.direction == "inbound"
            assert message.content_clean == "Hello"

    def test_list_messages(self, sample_message_list: dict[str, Any]) -> None:
        """Test listing messages for an inbox."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_message_list

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            pager = client.messages.list(inbox_id="inbox-123")

            messages = list(pager)
            assert len(messages) == 1
            assert messages[0].id == "msg-123"

            # Verify inbox_id was passed
            call_args = mock_httpx.request.call_args
            assert call_args.kwargs["params"]["inbox_id"] == "inbox-123"

    def test_send_message_with_raw_response(
        self, sample_send_response: dict[str, Any]
    ) -> None:
        """Test sending message with raw response access."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.json.return_value = sample_send_response
        mock_response.headers = httpx.Headers({"content-type": "application/json"})

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            raw_response = client.messages.with_raw_response.send(
                inbox_id="inbox-123",
                to=["recipient@example.com"],
                subject="Hello",
                body="Test",
            )

            assert raw_response.status_code == 201
            assert raw_response.data.id == "msg-789"


class TestAsyncMessagesResource:
    """Test asynchronous message operations."""

    @pytest.mark.asyncio
    async def test_async_send_message(self, sample_send_response: dict[str, Any]) -> None:
        """Test async message sending."""
        from nornweave_client import AsyncNornWeave

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.json.return_value = sample_send_response

        mock_httpx = MagicMock(spec=httpx.AsyncClient)
        mock_httpx.request = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_httpx):
            client = AsyncNornWeave(base_url="http://localhost:8000")
            result = await client.messages.send(
                inbox_id="inbox-123",
                to=["recipient@example.com"],
                subject="Hello",
                body="Test",
            )

            assert isinstance(result, SendMessageResponse)
            assert result.id == "msg-789"

    @pytest.mark.asyncio
    async def test_async_list_messages(self, sample_message_list: dict[str, Any]) -> None:
        """Test async message listing."""
        from nornweave_client import AsyncNornWeave

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_message_list

        mock_httpx = MagicMock(spec=httpx.AsyncClient)
        mock_httpx.request = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_httpx):
            client = AsyncNornWeave(base_url="http://localhost:8000")
            pager = client.messages.list(inbox_id="inbox-123")

            messages = await pager.to_list()
            assert len(messages) == 1
            assert messages[0].id == "msg-123"
