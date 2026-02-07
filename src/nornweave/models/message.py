"""Message models.

Message models for email content and metadata.
"""

from datetime import datetime  # noqa: TC003 - needed at runtime for Pydantic
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from nornweave.models.attachment import Attachment, AttachmentMeta, SendAttachment


class MessageDirection(StrEnum):
    """Message direction."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageItem(BaseModel):
    """
    Message summary for list views (without full body content).

    Summary model for message list views.
    """

    inbox_id: str = Field(..., description="ID of inbox")
    thread_id: str = Field(..., description="ID of thread")
    message_id: str = Field(..., description="ID of message")
    labels: list[str] = Field(default_factory=list, description="Labels of message")
    timestamp: datetime = Field(..., description="Time at which message was sent or drafted")
    from_address: str = Field(..., alias="from", description="Sender address")
    to: list[str] = Field(..., description="Recipient addresses")
    cc: list[str] | None = Field(None, description="CC recipient addresses")
    bcc: list[str] | None = Field(None, description="BCC recipient addresses")
    subject: str | None = Field(None, description="Subject of message")
    preview: str | None = Field(None, description="Text preview of message")
    attachments: list[AttachmentMeta] | None = Field(None, description="Attachments in message")
    in_reply_to: str | None = Field(None, description="Message-ID of message being replied to")
    references: list[str] | None = Field(
        None, description="Message-IDs of previous messages in thread"
    )
    headers: dict[str, str] | None = Field(None, description="Headers in message")
    size: int = Field(..., description="Size of message in bytes")
    updated_at: datetime = Field(..., description="Time at which message was last updated")
    created_at: datetime = Field(..., description="Time at which message was created")

    model_config = {"extra": "forbid", "populate_by_name": True}


class Message(BaseModel):
    """
    Full message model with body content.

    Complete message model with body content.
    """

    inbox_id: str = Field(..., description="ID of inbox")
    thread_id: str = Field(..., description="ID of thread")
    message_id: str = Field(..., alias="id", description="ID of message")
    labels: list[str] = Field(default_factory=list, description="Labels of message")
    timestamp: datetime | None = Field(
        None, description="Time at which message was sent or drafted"
    )
    from_address: str | None = Field(None, alias="from", description="Sender address")
    reply_to: list[str] | None = Field(None, description="Reply-to addresses")
    to: list[str] = Field(default_factory=list, description="Recipient addresses")
    cc: list[str] | None = Field(None, description="CC recipient addresses")
    bcc: list[str] | None = Field(None, description="BCC recipient addresses")
    subject: str | None = Field(None, description="Subject of message")
    preview: str | None = Field(None, description="Text preview of message")
    text: str | None = Field(None, alias="content_raw", description="Plain text body of message")
    html: str | None = Field(None, description="HTML body of message")
    extracted_text: str | None = Field(
        None,
        alias="content_clean",
        description="Extracted new text content (without quoted replies)",
    )
    extracted_html: str | None = Field(
        None, description="Extracted new HTML content (without quoted replies)"
    )
    attachments: list[Attachment] | None = Field(None, description="Attachments in message")
    in_reply_to: str | None = Field(None, description="Message-ID of message being replied to")
    references: list[str] | None = Field(
        None, description="Message-IDs of previous messages in thread"
    )
    headers: dict[str, str] | None = Field(
        None, alias="metadata", description="All headers in message"
    )
    size: int = Field(0, description="Size of message in bytes")
    direction: MessageDirection = Field(
        default=MessageDirection.INBOUND, description="Inbound or outbound"
    )
    provider_message_id: str | None = Field(None, description="Provider's Message-ID header")
    updated_at: datetime | None = Field(None, description="Time at which message was last updated")
    created_at: datetime | None = Field(None, description="Time at which message was created")

    model_config = {"populate_by_name": True}

    @property
    def id(self) -> str:
        """Alias for message_id for compatibility."""
        return self.message_id

    @property
    def content_raw(self) -> str | None:
        """Alias for text for backwards compatibility."""
        return self.text

    @property
    def content_clean(self) -> str | None:
        """Alias for extracted_text for backwards compatibility."""
        return self.extracted_text

    @property
    def metadata(self) -> dict[str, str] | None:
        """Alias for headers for backwards compatibility."""
        return self.headers


class ListMessagesResponse(BaseModel):
    """
    Response for listing messages.

    Paginated response for message listing.
    """

    count: int = Field(..., description="Total count of messages")
    limit: int | None = Field(None, description="Limit applied to results")
    next_page_token: str | None = Field(None, description="Token for next page")
    messages: list[MessageItem] = Field(..., description="Messages ordered by timestamp descending")

    model_config = {"extra": "forbid"}


class SendMessageRequest(BaseModel):
    """
    Request to send a new message.

    Request payload for sending a new message.
    """

    labels: list[str] | None = None
    reply_to: str | list[str] | None = Field(None, description="Reply-to address(es)")
    to: str | list[str] | None = Field(None, description="Recipient address(es)")
    cc: str | list[str] | None = Field(None, description="CC address(es)")
    bcc: str | list[str] | None = Field(None, description="BCC address(es)")
    subject: str | None = None
    text: str | None = Field(None, description="Plain text body")
    html: str | None = Field(None, description="HTML body")
    attachments: list[SendAttachment] | None = None
    headers: dict[str, str] | None = None

    model_config = {"extra": "forbid"}

    def get_to_list(self) -> list[str]:
        """Get 'to' as a list."""
        if self.to is None:
            return []
        return [self.to] if isinstance(self.to, str) else list(self.to)

    def get_cc_list(self) -> list[str]:
        """Get 'cc' as a list."""
        if self.cc is None:
            return []
        return [self.cc] if isinstance(self.cc, str) else list(self.cc)

    def get_bcc_list(self) -> list[str]:
        """Get 'bcc' as a list."""
        if self.bcc is None:
            return []
        return [self.bcc] if isinstance(self.bcc, str) else list(self.bcc)

    def get_reply_to_list(self) -> list[str]:
        """Get 'reply_to' as a list."""
        if self.reply_to is None:
            return []
        return [self.reply_to] if isinstance(self.reply_to, str) else list(self.reply_to)


class SendMessageResponse(BaseModel):
    """
    Response after sending a message.

    Response after sending a message.
    """

    message_id: str
    thread_id: str

    model_config = {"extra": "forbid"}


class ReplyToMessageRequest(BaseModel):
    """
    Request to reply to a specific message.

    Request payload for replying to a message.
    """

    labels: list[str] | None = None
    reply_to: str | list[str] | None = None
    to: str | list[str] | None = Field(None, description="Override recipients")
    cc: str | list[str] | None = None
    bcc: str | list[str] | None = None
    reply_all: bool | None = Field(
        None, description="Reply to all recipients of the original message"
    )
    text: str | None = None
    html: str | None = None
    attachments: list[SendAttachment] | None = None
    headers: dict[str, str] | None = None

    model_config = {"extra": "forbid"}

    def get_to_list(self) -> list[str]:
        """Get 'to' as a list."""
        if self.to is None:
            return []
        return [self.to] if isinstance(self.to, str) else list(self.to)


class UpdateMessageRequest(BaseModel):
    """
    Request to update message labels.

    Request payload for updating message labels.
    """

    add_labels: list[str] | None = Field(None, description="Labels to add to message")
    remove_labels: list[str] | None = Field(None, description="Labels to remove from message")

    model_config = {"extra": "forbid"}


# Legacy compatibility models (for existing codebase)
class MessageBase(BaseModel):
    """Shared message fields (legacy compatibility)."""

    thread_id: str = Field(..., description="Thread id")
    inbox_id: str = Field(..., description="Inbox id")
    provider_message_id: str | None = Field(None, description="Provider Message-ID header")
    direction: MessageDirection = Field(..., description="Inbound or outbound")
    content_raw: str = Field("", description="Original HTML/plain text")
    content_clean: str = Field("", description="LLM-ready Markdown")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Headers, token counts, sentiment, etc.",
    )


class MessageCreate(BaseModel):
    """Payload to send a message (outbound via API)."""

    inbox_id: str
    to: list[str] = Field(..., min_length=1)
    subject: str = Field(..., min_length=1)
    body: str = Field(..., description="Markdown body")
    reply_to_thread_id: str | None = None
    cc: list[str] | None = None
    bcc: list[str] | None = None
    attachments: list[SendAttachment] | None = None

    model_config = {"extra": "forbid"}


class MessageInCreate(BaseModel):
    """Payload to create a message on ingestion (inbound webhook)."""

    thread_id: str = Field(..., description="Thread id")
    inbox_id: str = Field(..., description="Inbox id")
    provider_message_id: str | None = Field(None, description="Provider Message-ID header")
    direction: MessageDirection = Field(..., description="Inbound or outbound")
    content_raw: str = Field("", description="Original HTML/plain text")
    content_clean: str = Field("", description="LLM-ready Markdown")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Headers, token counts, sentiment, etc.",
    )

    model_config = {"extra": "forbid"}
