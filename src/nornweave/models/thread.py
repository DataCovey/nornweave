"""Thread models.

Thread models for email conversation grouping.
"""

from datetime import datetime  # noqa: TC003 - needed at runtime for Pydantic
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from nornweave.models.attachment import AttachmentMeta
    from nornweave.models.message import Message


class ThreadItem(BaseModel):
    """
    Thread summary for list views.

    Summary model for thread list views.
    """

    inbox_id: str = Field(..., description="ID of inbox")
    thread_id: str = Field(..., alias="id", description="ID of thread")
    labels: list[str] = Field(default_factory=list, description="Labels of thread")
    timestamp: datetime | None = Field(
        None, alias="last_message_at", description="Timestamp of last sent or received message"
    )
    received_timestamp: datetime | None = Field(
        None, description="Timestamp of last received message"
    )
    sent_timestamp: datetime | None = Field(None, description="Timestamp of last sent message")
    senders: list[str] = Field(default_factory=list, description="Senders in thread")
    recipients: list[str] = Field(default_factory=list, description="Recipients in thread")
    subject: str | None = Field(None, description="Subject of thread")
    preview: str | None = Field(None, description="Text preview of last message in thread")
    summary: str | None = Field(None, description="LLM-generated thread summary")
    attachments: list[AttachmentMeta] | None = Field(None, description="Attachments in thread")
    last_message_id: str | None = Field(None, description="ID of last message in thread")
    message_count: int = Field(0, description="Number of messages in thread")
    size: int = Field(0, description="Size of thread in bytes")
    updated_at: datetime | None = Field(None, description="Time at which thread was last updated")
    created_at: datetime | None = Field(None, description="Time at which thread was created")

    model_config = {"populate_by_name": True}

    @property
    def id(self) -> str:
        """Alias for thread_id for compatibility."""
        return self.thread_id

    @property
    def last_message_at(self) -> datetime | None:
        """Alias for timestamp for backwards compatibility."""
        return self.timestamp


class Thread(BaseModel):
    """
    Full thread model with messages.

    Complete thread model with optional message list.
    """

    inbox_id: str = Field(..., description="ID of inbox")
    thread_id: str = Field(..., alias="id", description="ID of thread")
    labels: list[str] = Field(default_factory=list, description="Labels of thread")
    timestamp: datetime | None = Field(
        None, alias="last_message_at", description="Timestamp of last sent or received message"
    )
    received_timestamp: datetime | None = Field(
        None, description="Timestamp of last received message"
    )
    sent_timestamp: datetime | None = Field(None, description="Timestamp of last sent message")
    senders: list[str] = Field(default_factory=list, description="Senders in thread")
    recipients: list[str] = Field(default_factory=list, description="Recipients in thread")
    subject: str | None = Field(None, description="Subject of thread")
    preview: str | None = Field(None, description="Text preview of last message in thread")
    summary: str | None = Field(None, description="LLM-generated thread summary")
    attachments: list[AttachmentMeta] | None = Field(None, description="All attachments in thread")
    last_message_id: str | None = Field(None, description="ID of last message in thread")
    message_count: int = Field(0, description="Number of messages in thread")
    size: int = Field(0, description="Size of thread in bytes")
    updated_at: datetime | None = Field(None, description="Time at which thread was last updated")
    created_at: datetime | None = Field(None, description="Time at which thread was created")
    # Optional for full thread response - messages ordered by timestamp ascending
    messages: list[Message] | None = Field(
        None, description="Messages in thread, ordered by timestamp ascending"
    )
    # Internal fields for threading
    participant_hash: str | None = Field(None, description="Hash of participants for grouping")
    normalized_subject: str | None = Field(
        None, description="Normalized subject for subject-based threading"
    )

    model_config = {"populate_by_name": True}

    @property
    def id(self) -> str:
        """Alias for thread_id for compatibility."""
        return self.thread_id

    @property
    def last_message_at(self) -> datetime | None:
        """Alias for timestamp for backwards compatibility."""
        return self.timestamp

    @last_message_at.setter
    def last_message_at(self, value: datetime | None) -> None:
        """Setter for last_message_at (maps to timestamp)."""
        object.__setattr__(self, "timestamp", value)


class ListThreadsResponse(BaseModel):
    """
    Response for listing threads.

    Paginated response for thread listing.
    """

    count: int = Field(..., description="Total count of threads")
    limit: int | None = Field(None, description="Limit applied to results")
    next_page_token: str | None = Field(None, description="Token for next page")
    threads: list[ThreadItem] = Field(..., description="Threads ordered by timestamp descending")

    model_config = {"extra": "forbid"}


class UpdateThreadRequest(BaseModel):
    """Request to update thread labels."""

    add_labels: list[str] | None = Field(None, description="Labels to add to thread")
    remove_labels: list[str] | None = Field(None, description="Labels to remove from thread")

    model_config = {"extra": "forbid"}


# Legacy compatibility models
class ThreadBase(BaseModel):
    """Shared thread fields (legacy compatibility)."""

    inbox_id: str = Field(..., description="Owning inbox id")
    subject: str = Field(..., description="Thread subject")
    last_message_at: datetime | None = Field(None, description="Last message timestamp")
    participant_hash: str | None = Field(None, description="Hash of participants for grouping")


class ThreadCreate(BaseModel):
    """Payload to create a thread (used on ingestion)."""

    inbox_id: str = Field(..., description="Owning inbox id")
    subject: str = Field(..., description="Thread subject")
    last_message_at: datetime | None = Field(None, description="Last message timestamp")
    participant_hash: str | None = Field(None, description="Hash of participants for grouping")
    senders: list[str] = Field(default_factory=list, description="Senders in thread")
    recipients: list[str] = Field(default_factory=list, description="Recipients in thread")
    normalized_subject: str | None = Field(None, description="Normalized subject for threading")

    model_config = {"extra": "forbid"}


class ThreadSummary(BaseModel):
    """Summary for list views (e.g. recent threads). Legacy compatibility."""

    id: str
    subject: str
    last_message_at: datetime | None
    message_count: int = 0

    model_config = {"extra": "forbid"}


# Note: Forward reference resolution (model_rebuild) is done in __init__.py
# after all models are imported to avoid circular import issues.
