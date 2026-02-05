"""Unit tests for messages route."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from nornweave.models.message import Message, MessageDirection
from nornweave.yggdrasil.routes.v1.messages import (
    MessageListResponse,
    MessageResponse,
    _message_to_response,
)


class TestMessageResponse:
    """Tests for MessageResponse model."""

    def test_message_response_minimal_fields(self) -> None:
        """Test MessageResponse with minimal required fields."""
        response = MessageResponse(
            id="msg_123",
            thread_id="th_456",
            inbox_id="ibx_789",
            direction="inbound",
            provider_message_id=None,
        )

        assert response.id == "msg_123"
        assert response.thread_id == "th_456"
        assert response.inbox_id == "ibx_789"
        assert response.direction == "inbound"
        assert response.provider_message_id is None
        # Default values
        assert response.to_addresses == []
        assert response.labels == []
        assert response.size == 0
        assert response.content_clean == ""
        assert response.metadata == {}

    def test_message_response_all_fields(self) -> None:
        """Test MessageResponse with all fields populated."""
        now = datetime.now(UTC)
        response = MessageResponse(
            id="msg_123",
            thread_id="th_456",
            inbox_id="ibx_789",
            direction="inbound",
            provider_message_id="<abc@mail.example.com>",
            subject="Test Subject",
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
            cc_addresses=["cc@example.com"],
            bcc_addresses=["bcc@example.com"],
            reply_to_addresses=["reply@example.com"],
            text="Plain text body",
            html="<p>HTML body</p>",
            content_clean="Plain text body",
            timestamp=now,
            labels=["important", "inbox"],
            preview="Plain text...",
            size=1234,
            in_reply_to="<parent@mail.example.com>",
            references=["<ref1@mail.example.com>", "<ref2@mail.example.com>"],
            metadata={"custom": "header"},
            created_at=now,
        )

        assert response.subject == "Test Subject"
        assert response.from_address == "sender@example.com"
        assert response.to_addresses == ["recipient@example.com"]
        assert response.cc_addresses == ["cc@example.com"]
        assert response.bcc_addresses == ["bcc@example.com"]
        assert response.reply_to_addresses == ["reply@example.com"]
        assert response.text == "Plain text body"
        assert response.html == "<p>HTML body</p>"
        assert response.content_clean == "Plain text body"
        assert response.timestamp == now
        assert response.labels == ["important", "inbox"]
        assert response.preview == "Plain text..."
        assert response.size == 1234
        assert response.in_reply_to == "<parent@mail.example.com>"
        assert response.references == ["<ref1@mail.example.com>", "<ref2@mail.example.com>"]
        assert response.metadata == {"custom": "header"}
        assert response.created_at == now

    def test_message_response_null_optional_fields(self) -> None:
        """Test MessageResponse with null optional fields."""
        response = MessageResponse(
            id="msg_123",
            thread_id="th_456",
            inbox_id="ibx_789",
            direction="outbound",
            provider_message_id=None,
            subject=None,
            from_address=None,
            cc_addresses=None,
            bcc_addresses=None,
            reply_to_addresses=None,
            text=None,
            html=None,
            timestamp=None,
            preview=None,
            in_reply_to=None,
            references=None,
            created_at=None,
        )

        assert response.subject is None
        assert response.from_address is None
        assert response.cc_addresses is None
        assert response.text is None
        assert response.html is None


class TestMessageToResponse:
    """Tests for _message_to_response conversion function."""

    def test_converts_all_fields(self) -> None:
        """Test that _message_to_response maps all fields correctly."""
        now = datetime.now(UTC)
        message = Message(
            message_id="msg_123",
            thread_id="th_456",
            inbox_id="ibx_789",
            direction=MessageDirection.INBOUND,
            provider_message_id="<abc@mail.example.com>",
            subject="Test Subject",
            from_address="sender@example.com",
            to=["recipient@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            reply_to=["reply@example.com"],
            text="Plain text body",
            html="<p>HTML body</p>",
            extracted_text="Plain text body",
            timestamp=now,
            labels=["important"],
            preview="Plain text...",
            size=1234,
            in_reply_to="<parent@mail.example.com>",
            references=["<ref1@mail.example.com>"],
            headers={"X-Custom": "value"},
            created_at=now,
        )

        response = _message_to_response(message)

        assert response.id == "msg_123"
        assert response.thread_id == "th_456"
        assert response.inbox_id == "ibx_789"
        assert response.direction == "inbound"
        assert response.provider_message_id == "<abc@mail.example.com>"
        assert response.subject == "Test Subject"
        assert response.from_address == "sender@example.com"
        assert response.to_addresses == ["recipient@example.com"]
        assert response.cc_addresses == ["cc@example.com"]
        assert response.bcc_addresses == ["bcc@example.com"]
        assert response.reply_to_addresses == ["reply@example.com"]
        assert response.text == "Plain text body"
        assert response.html == "<p>HTML body</p>"
        assert response.content_clean == "Plain text body"
        assert response.timestamp == now
        assert response.labels == ["important"]
        assert response.preview == "Plain text..."
        assert response.size == 1234
        assert response.in_reply_to == "<parent@mail.example.com>"
        assert response.references == ["<ref1@mail.example.com>"]
        assert response.metadata == {"X-Custom": "value"}
        assert response.created_at == now

    def test_handles_empty_lists(self) -> None:
        """Test that empty lists are handled correctly."""
        message = Message(
            message_id="msg_123",
            thread_id="th_456",
            inbox_id="ibx_789",
            direction=MessageDirection.OUTBOUND,
            to=[],
            labels=[],
        )

        response = _message_to_response(message)

        assert response.to_addresses == []
        assert response.labels == []

    def test_handles_none_values(self) -> None:
        """Test that None values are handled correctly."""
        message = Message(
            message_id="msg_123",
            thread_id="th_456",
            inbox_id="ibx_789",
            direction=MessageDirection.INBOUND,
            subject=None,
            from_address=None,
            cc=None,
            bcc=None,
            reply_to=None,
            text=None,
            html=None,
            extracted_text=None,
            timestamp=None,
            headers=None,
            created_at=None,
        )

        response = _message_to_response(message)

        assert response.subject is None
        assert response.from_address is None
        assert response.cc_addresses is None
        assert response.bcc_addresses is None
        assert response.reply_to_addresses is None
        assert response.text is None
        assert response.html is None
        assert response.content_clean == ""
        assert response.timestamp is None
        assert response.metadata == {}
        assert response.created_at is None


class TestMessageListResponse:
    """Tests for MessageListResponse model."""

    def test_list_response_with_items(self) -> None:
        """Test MessageListResponse with items."""
        response = MessageListResponse(
            items=[
                MessageResponse(
                    id="msg_1",
                    thread_id="th_1",
                    inbox_id="ibx_1",
                    direction="inbound",
                    provider_message_id=None,
                ),
                MessageResponse(
                    id="msg_2",
                    thread_id="th_1",
                    inbox_id="ibx_1",
                    direction="outbound",
                    provider_message_id=None,
                ),
            ],
            count=2,
            total=10,
        )

        assert len(response.items) == 2
        assert response.count == 2
        assert response.total == 10

    def test_list_response_empty(self) -> None:
        """Test MessageListResponse with no items."""
        response = MessageListResponse(
            items=[],
            count=0,
            total=0,
        )

        assert response.items == []
        assert response.count == 0
        assert response.total == 0

    def test_list_response_requires_total(self) -> None:
        """Test that MessageListResponse requires total field."""
        with pytest.raises(ValidationError):
            MessageListResponse(
                items=[],
                count=0,
                # missing total
            )
