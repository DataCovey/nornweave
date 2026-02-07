"""Event models for webhooks.

Event models for webhook notifications and internal event tracking.
"""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from nornweave.models.message import Message
    from nornweave.models.thread import ThreadItem


class EventType(StrEnum):
    """
    Event types for webhooks.

    Supported event types for webhooks and notifications.
    """

    MESSAGE_RECEIVED = "message.received"
    MESSAGE_SENT = "message.sent"
    MESSAGE_DELIVERED = "message.delivered"
    MESSAGE_BOUNCED = "message.bounced"
    MESSAGE_COMPLAINED = "message.complained"
    MESSAGE_REJECTED = "message.rejected"
    DOMAIN_VERIFIED = "domain.verified"
    # Legacy event types for backwards compatibility
    THREAD_NEW_MESSAGE = "thread.new_message"
    INBOX_CREATED = "inbox.created"
    INBOX_DELETED = "inbox.deleted"


class Recipient(BaseModel):
    """
    Recipient with delivery status.

    Recipient with delivery status information.
    """

    address: str = Field(..., description="Recipient address")
    status: str = Field(..., description="Recipient status")

    model_config = {"extra": "forbid"}


class SendEvent(BaseModel):
    """
    Event data for message sent.

    Send event payload with recipient list.
    """

    inbox_id: str
    thread_id: str
    message_id: str
    timestamp: datetime
    recipients: list[str] = Field(..., description="Sent recipients")

    model_config = {"extra": "forbid"}


class DeliveryEvent(BaseModel):
    """
    Event data for message delivered.

    Delivery confirmation event payload.
    """

    inbox_id: str
    thread_id: str
    message_id: str
    timestamp: datetime
    recipients: list[str] = Field(..., description="Delivered recipients")

    model_config = {"extra": "forbid"}


class BounceEvent(BaseModel):
    """
    Event data for message bounced.

    Bounce event payload with type and affected recipients.
    """

    inbox_id: str
    thread_id: str
    message_id: str
    timestamp: datetime
    type: str = Field(..., description="Bounce type (hard/soft)")
    sub_type: str = Field(..., description="Bounce sub-type")
    recipients: list[Recipient] = Field(..., description="Bounced recipients with status")

    model_config = {"extra": "forbid"}


class ComplaintEvent(BaseModel):
    """
    Event data for spam complaint.

    Spam complaint event payload.
    """

    inbox_id: str
    thread_id: str
    message_id: str
    timestamp: datetime
    type: str = Field(..., description="Complaint type")
    sub_type: str = Field(..., description="Complaint sub-type")
    recipients: list[str] = Field(..., description="Complained recipients")

    model_config = {"extra": "forbid"}


class RejectEvent(BaseModel):
    """
    Event data for message rejected.

    Rejection event payload with reason.
    """

    inbox_id: str
    thread_id: str
    message_id: str
    timestamp: datetime
    reason: str = Field(..., description="Reject reason")

    model_config = {"extra": "forbid"}


class MessageReceivedEvent(BaseModel):
    """
    Webhook event for message received.

    Webhook payload for inbound message received.
    """

    type: Literal["event"] = "event"
    event_type: Literal["message.received"] = "message.received"
    event_id: str
    message: Message
    thread: ThreadItem

    model_config = {"extra": "forbid"}


class MessageSentEvent(BaseModel):
    """
    Webhook event for message sent.

    Webhook payload for message sent.
    """

    type: Literal["event"] = "event"
    event_type: Literal["message.sent"] = "message.sent"
    event_id: str
    send: SendEvent

    model_config = {"extra": "forbid"}


class MessageDeliveredEvent(BaseModel):
    """
    Webhook event for message delivered.

    Webhook payload for message delivered.
    """

    type: Literal["event"] = "event"
    event_type: Literal["message.delivered"] = "message.delivered"
    event_id: str
    delivery: DeliveryEvent

    model_config = {"extra": "forbid"}


class MessageBouncedEvent(BaseModel):
    """
    Webhook event for message bounced.

    Webhook payload for message bounced.
    """

    type: Literal["event"] = "event"
    event_type: Literal["message.bounced"] = "message.bounced"
    event_id: str
    bounce: BounceEvent

    model_config = {"extra": "forbid"}


class MessageComplainedEvent(BaseModel):
    """
    Webhook event for spam complaint.

    Webhook payload for spam complaint.
    """

    type: Literal["event"] = "event"
    event_type: Literal["message.complained"] = "message.complained"
    event_id: str
    complaint: ComplaintEvent

    model_config = {"extra": "forbid"}


class MessageRejectedEvent(BaseModel):
    """
    Webhook event for message rejected.

    Webhook payload for message rejected.
    """

    type: Literal["event"] = "event"
    event_type: Literal["message.rejected"] = "message.rejected"
    event_id: str
    reject: RejectEvent

    model_config = {"extra": "forbid"}


# Type alias for all webhook events
WebhookEvent = (
    MessageReceivedEvent
    | MessageSentEvent
    | MessageDeliveredEvent
    | MessageBouncedEvent
    | MessageComplainedEvent
    | MessageRejectedEvent
)


# Legacy models for backwards compatibility
class EventCreate(BaseModel):
    """Payload to create an event (id and created_at set by storage)."""

    type: EventType = Field(..., description="Event type")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Event payload",
    )

    model_config = {"extra": "forbid"}


class Event(BaseModel):
    """Event entity with id and timestamp."""

    id: str = Field(..., description="Event id")
    type: EventType = Field(..., description="Event type")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Event payload",
    )
    # Additional fields for structured events
    inbox_id: str | None = Field(None, description="Associated inbox ID")
    thread_id: str | None = Field(None, description="Associated thread ID")
    message_id: str | None = Field(None, description="Associated message ID")

    model_config = {"extra": "forbid"}


class ListEventsResponse(BaseModel):
    """Response for listing events."""

    count: int = Field(..., description="Total count of events")
    limit: int | None = Field(None, description="Limit applied to results")
    next_page_token: str | None = Field(None, description="Token for next page")
    events: list[Event] = Field(..., description="Events ordered by timestamp descending")

    model_config = {"extra": "forbid"}
