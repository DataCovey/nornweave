"""Unit tests for event models."""

from datetime import datetime

from nornweave.models.event import (
    BounceEvent,
    ComplaintEvent,
    DeliveryEvent,
    Event,
    EventCreate,
    EventType,
    MessageBouncedEvent,
    MessageComplainedEvent,
    MessageDeliveredEvent,
    MessageRejectedEvent,
    MessageSentEvent,
    Recipient,
    RejectEvent,
    SendEvent,
)


class TestEventType:
    """Tests for EventType enum."""

    def test_all_message_events(self) -> None:
        """Test all message-related event types exist."""
        assert EventType.MESSAGE_RECEIVED == "message.received"
        assert EventType.MESSAGE_SENT == "message.sent"
        assert EventType.MESSAGE_DELIVERED == "message.delivered"
        assert EventType.MESSAGE_BOUNCED == "message.bounced"
        assert EventType.MESSAGE_COMPLAINED == "message.complained"
        assert EventType.MESSAGE_REJECTED == "message.rejected"

    def test_legacy_event_types(self) -> None:
        """Test legacy event types for backwards compatibility."""
        assert EventType.THREAD_NEW_MESSAGE == "thread.new_message"
        assert EventType.INBOX_CREATED == "inbox.created"
        assert EventType.INBOX_DELETED == "inbox.deleted"


class TestRecipient:
    """Tests for Recipient model."""

    def test_creation(self) -> None:
        """Test Recipient creation."""
        recipient = Recipient(address="test@example.com", status="delivered")
        assert recipient.address == "test@example.com"
        assert recipient.status == "delivered"

    def test_serialization(self) -> None:
        """Test Recipient serialization."""
        recipient = Recipient(address="test@example.com", status="bounced")
        data = recipient.model_dump()
        assert data["address"] == "test@example.com"
        assert data["status"] == "bounced"


class TestSendEvent:
    """Tests for SendEvent model."""

    def test_creation(self) -> None:
        """Test SendEvent creation."""
        event = SendEvent(
            inbox_id="inbox1",
            thread_id="thread1",
            message_id="msg1",
            timestamp=datetime(2026, 1, 31, 12, 0, 0),
            recipients=["alice@example.com", "bob@example.com"],
        )
        assert event.inbox_id == "inbox1"
        assert len(event.recipients) == 2


class TestDeliveryEvent:
    """Tests for DeliveryEvent model."""

    def test_creation(self) -> None:
        """Test DeliveryEvent creation."""
        event = DeliveryEvent(
            inbox_id="inbox1",
            thread_id="thread1",
            message_id="msg1",
            timestamp=datetime(2026, 1, 31, 12, 0, 0),
            recipients=["alice@example.com"],
        )
        assert event.recipients == ["alice@example.com"]


class TestBounceEvent:
    """Tests for BounceEvent model."""

    def test_hard_bounce(self) -> None:
        """Test hard bounce event."""
        event = BounceEvent(
            inbox_id="inbox1",
            thread_id="thread1",
            message_id="msg1",
            timestamp=datetime(2026, 1, 31, 12, 0, 0),
            type="hard",
            sub_type="general",
            recipients=[Recipient(address="invalid@example.com", status="bounced")],
        )
        assert event.type == "hard"
        assert len(event.recipients) == 1

    def test_soft_bounce(self) -> None:
        """Test soft bounce event."""
        event = BounceEvent(
            inbox_id="inbox1",
            thread_id="thread1",
            message_id="msg1",
            timestamp=datetime(2026, 1, 31, 12, 0, 0),
            type="soft",
            sub_type="mailbox_full",
            recipients=[Recipient(address="full@example.com", status="deferred")],
        )
        assert event.type == "soft"
        assert event.sub_type == "mailbox_full"


class TestComplaintEvent:
    """Tests for ComplaintEvent model."""

    def test_creation(self) -> None:
        """Test ComplaintEvent creation."""
        event = ComplaintEvent(
            inbox_id="inbox1",
            thread_id="thread1",
            message_id="msg1",
            timestamp=datetime(2026, 1, 31, 12, 0, 0),
            type="abuse",
            sub_type="spam_button",
            recipients=["complainer@example.com"],
        )
        assert event.type == "abuse"
        assert "complainer@example.com" in event.recipients


class TestRejectEvent:
    """Tests for RejectEvent model."""

    def test_creation(self) -> None:
        """Test RejectEvent creation."""
        event = RejectEvent(
            inbox_id="inbox1",
            thread_id="thread1",
            message_id="msg1",
            timestamp=datetime(2026, 1, 31, 12, 0, 0),
            reason="Policy violation: attachment blocked",
        )
        assert "Policy violation" in event.reason


class TestMessageSentEvent:
    """Tests for MessageSentEvent webhook."""

    def test_creation(self) -> None:
        """Test MessageSentEvent creation."""
        send = SendEvent(
            inbox_id="inbox1",
            thread_id="thread1",
            message_id="msg1",
            timestamp=datetime(2026, 1, 31, 12, 0, 0),
            recipients=["alice@example.com"],
        )
        event = MessageSentEvent(
            event_id="evt_123",
            send=send,
        )
        assert event.type == "event"
        assert event.event_type == "message.sent"
        assert event.send.message_id == "msg1"


class TestMessageDeliveredEvent:
    """Tests for MessageDeliveredEvent webhook."""

    def test_creation(self) -> None:
        """Test MessageDeliveredEvent creation."""
        delivery = DeliveryEvent(
            inbox_id="inbox1",
            thread_id="thread1",
            message_id="msg1",
            timestamp=datetime(2026, 1, 31, 12, 0, 0),
            recipients=["alice@example.com"],
        )
        event = MessageDeliveredEvent(
            event_id="evt_123",
            delivery=delivery,
        )
        assert event.event_type == "message.delivered"


class TestMessageBouncedEvent:
    """Tests for MessageBouncedEvent webhook."""

    def test_creation(self) -> None:
        """Test MessageBouncedEvent creation."""
        bounce = BounceEvent(
            inbox_id="inbox1",
            thread_id="thread1",
            message_id="msg1",
            timestamp=datetime(2026, 1, 31, 12, 0, 0),
            type="hard",
            sub_type="no_such_user",
            recipients=[Recipient(address="bad@example.com", status="failed")],
        )
        event = MessageBouncedEvent(
            event_id="evt_123",
            bounce=bounce,
        )
        assert event.event_type == "message.bounced"


class TestMessageComplainedEvent:
    """Tests for MessageComplainedEvent webhook."""

    def test_creation(self) -> None:
        """Test MessageComplainedEvent creation."""
        complaint = ComplaintEvent(
            inbox_id="inbox1",
            thread_id="thread1",
            message_id="msg1",
            timestamp=datetime(2026, 1, 31, 12, 0, 0),
            type="abuse",
            sub_type="spam",
            recipients=["user@example.com"],
        )
        event = MessageComplainedEvent(
            event_id="evt_123",
            complaint=complaint,
        )
        assert event.event_type == "message.complained"


class TestMessageRejectedEvent:
    """Tests for MessageRejectedEvent webhook."""

    def test_creation(self) -> None:
        """Test MessageRejectedEvent creation."""
        reject = RejectEvent(
            inbox_id="inbox1",
            thread_id="thread1",
            message_id="msg1",
            timestamp=datetime(2026, 1, 31, 12, 0, 0),
            reason="Content filtering",
        )
        event = MessageRejectedEvent(
            event_id="evt_123",
            reject=reject,
        )
        assert event.event_type == "message.rejected"


class TestEvent:
    """Tests for Event model."""

    def test_creation(self) -> None:
        """Test Event creation."""
        event = Event(
            id="evt_123",
            type=EventType.MESSAGE_RECEIVED,
            created_at=datetime(2026, 1, 31, 12, 0, 0),
            payload={"message_id": "msg1"},
        )
        assert event.id == "evt_123"
        assert event.type == EventType.MESSAGE_RECEIVED

    def test_with_references(self) -> None:
        """Test Event with inbox/thread/message references."""
        event = Event(
            id="evt_123",
            type=EventType.MESSAGE_SENT,
            inbox_id="inbox1",
            thread_id="thread1",
            message_id="msg1",
        )
        assert event.inbox_id == "inbox1"
        assert event.thread_id == "thread1"
        assert event.message_id == "msg1"


class TestEventCreate:
    """Tests for EventCreate model."""

    def test_creation(self) -> None:
        """Test EventCreate creation."""
        event = EventCreate(
            type=EventType.INBOX_CREATED,
            payload={"inbox_id": "inbox1", "email": "test@example.com"},
        )
        assert event.type == EventType.INBOX_CREATED
        assert event.payload["inbox_id"] == "inbox1"

    def test_default_payload(self) -> None:
        """Test EventCreate with default empty payload."""
        event = EventCreate(type=EventType.INBOX_DELETED)
        assert event.payload == {}
