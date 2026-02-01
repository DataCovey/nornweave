"""SQLAlchemy ORM models for Urðr storage layer."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from nornweave.models.attachment import (
    Attachment as PydanticAttachment,
    AttachmentDisposition,
    AttachmentMeta,
)
from nornweave.models.event import Event as PydanticEvent
from nornweave.models.event import EventType
from nornweave.models.inbox import Inbox as PydanticInbox
from nornweave.models.message import Message as PydanticMessage
from nornweave.models.message import MessageDirection
from nornweave.models.thread import Thread as PydanticThread

if TYPE_CHECKING:
    pass


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    pass


class InboxORM(Base):
    """Inbox table."""

    __tablename__ = "inboxes"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    email_address: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_config: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Relationships
    threads: Mapped[list["ThreadORM"]] = relationship(
        "ThreadORM",
        back_populates="inbox",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list["MessageORM"]] = relationship(
        "MessageORM",
        back_populates="inbox",
        cascade="all, delete-orphan",
    )

    def to_pydantic(self) -> PydanticInbox:
        """Convert ORM model to Pydantic model."""
        return PydanticInbox(
            id=self.id,
            email_address=self.email_address,
            name=self.name,
            provider_config=self.provider_config or {},
        )

    @classmethod
    def from_pydantic(cls, inbox: PydanticInbox) -> "InboxORM":
        """Create ORM model from Pydantic model."""
        return cls(
            id=inbox.id,
            email_address=inbox.email_address,
            name=inbox.name,
            provider_config=inbox.provider_config,
        )


class ThreadORM(Base):
    """Thread table for email conversation grouping."""

    __tablename__ = "threads"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    inbox_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("inboxes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Labels
    labels: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    received_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    sent_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Participants
    senders: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    recipients: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    participant_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    # Content
    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_subject: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        index=True,
    )
    preview: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Stats
    last_message_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Legacy compatibility
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    inbox: Mapped["InboxORM"] = relationship("InboxORM", back_populates="threads")
    messages: Mapped[list["MessageORM"]] = relationship(
        "MessageORM",
        back_populates="thread",
        cascade="all, delete-orphan",
    )

    # Indexes for performance
    __table_args__ = (
        Index("ix_threads_inbox_last_message", "inbox_id", timestamp.desc()),
        Index("ix_threads_inbox_participant_hash", "inbox_id", "participant_hash"),
        Index("ix_threads_inbox_normalized_subject", "inbox_id", "normalized_subject"),
    )

    def to_pydantic(self) -> PydanticThread:
        """Convert ORM model to Pydantic model."""
        return PydanticThread(
            inbox_id=self.inbox_id,
            thread_id=self.id,
            labels=self.labels or [],
            timestamp=self.timestamp or self.last_message_at,  # Can be None
            received_timestamp=self.received_timestamp,
            sent_timestamp=self.sent_timestamp,
            senders=self.senders or [],
            recipients=self.recipients or [],
            subject=self.subject,
            preview=self.preview,
            attachments=None,  # Load separately if needed
            last_message_id=self.last_message_id,
            message_count=self.message_count,
            size=self.size,
            updated_at=self.updated_at,
            created_at=self.created_at,
            participant_hash=self.participant_hash,
            normalized_subject=self.normalized_subject,
        )

    @classmethod
    def from_pydantic(cls, thread: PydanticThread) -> "ThreadORM":
        """Create ORM model from Pydantic model."""
        return cls(
            id=thread.thread_id,
            inbox_id=thread.inbox_id,
            labels=thread.labels,
            timestamp=thread.timestamp,
            received_timestamp=thread.received_timestamp,
            sent_timestamp=thread.sent_timestamp,
            senders=thread.senders,
            recipients=thread.recipients,
            subject=thread.subject,
            normalized_subject=thread.normalized_subject,
            preview=thread.preview,
            last_message_id=thread.last_message_id,
            message_count=thread.message_count,
            size=thread.size,
            participant_hash=thread.participant_hash,
            last_message_at=thread.timestamp,  # Legacy compatibility
        )


class MessageORM(Base):
    """Message table for email content and metadata."""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    thread_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False,
    )
    inbox_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("inboxes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Labels
    labels: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Addresses
    from_address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    reply_to_addresses: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    to_addresses: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    cc_addresses: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    bcc_addresses: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Content
    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    preview: Mapped[str | None] = mapped_column(String(255), nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    html: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_html: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Threading headers
    in_reply_to: Mapped[str | None] = mapped_column(String(512), nullable=True)
    references: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    headers: Mapped[dict[str, str] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Metadata
    size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    direction: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    provider_message_id: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        index=True,
    )

    # Legacy fields for backwards compatibility
    content_raw: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_clean: Mapped[str] = mapped_column(Text, nullable=False, default="")
    message_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )

    # Relationships
    thread: Mapped["ThreadORM"] = relationship("ThreadORM", back_populates="messages")
    inbox: Mapped["InboxORM"] = relationship("InboxORM", back_populates="messages")
    attachments: Mapped[list["AttachmentORM"]] = relationship(
        "AttachmentORM",
        back_populates="message",
        cascade="all, delete-orphan",
    )

    # Indexes for performance
    __table_args__ = (
        Index("ix_messages_thread_created", "thread_id", "created_at"),
        Index("ix_messages_inbox_created", "inbox_id", "created_at"),
        Index("ix_messages_inbox_id", "inbox_id"),
        Index(
            "ix_messages_inbox_provider_msg",
            "inbox_id",
            "provider_message_id",
            unique=True,
            postgresql_where=("provider_message_id IS NOT NULL"),
        ),
        Index("ix_messages_timestamp", "timestamp"),
    )

    def to_pydantic(self) -> PydanticMessage:
        """Convert ORM model to Pydantic model.
        
        Note: Attachments are not loaded by default to avoid lazy loading issues.
        Use explicit queries or eager loading if attachments are needed.
        """
        return PydanticMessage(
            inbox_id=self.inbox_id,
            thread_id=self.thread_id,
            message_id=self.id,
            labels=self.labels or [],
            timestamp=self.timestamp,
            from_address=self.from_address,
            reply_to=self.reply_to_addresses,
            to=self.to_addresses or [],
            cc=self.cc_addresses,
            bcc=self.bcc_addresses,
            subject=self.subject,
            preview=self.preview,
            text=self.text or self.content_raw,
            html=self.html,
            extracted_text=self.extracted_text or self.content_clean,
            extracted_html=self.extracted_html,
            attachments=None,  # Loaded separately to avoid lazy loading
            in_reply_to=self.in_reply_to,
            references=self.references,
            headers=self.headers or self.message_metadata,
            size=self.size,
            direction=MessageDirection(self.direction),
            provider_message_id=self.provider_message_id,
            updated_at=self.updated_at,
            created_at=self.created_at,
        )

    @classmethod
    def from_pydantic(cls, message: PydanticMessage) -> "MessageORM":
        """Create ORM model from Pydantic model."""
        return cls(
            id=message.message_id,
            thread_id=message.thread_id,
            inbox_id=message.inbox_id,
            labels=message.labels,
            timestamp=message.timestamp,
            from_address=message.from_address,
            reply_to_addresses=message.reply_to,
            to_addresses=message.to,
            cc_addresses=message.cc,
            bcc_addresses=message.bcc,
            subject=message.subject,
            preview=message.preview,
            text=message.text,
            html=message.html,
            extracted_text=message.extracted_text,
            extracted_html=message.extracted_html,
            in_reply_to=message.in_reply_to,
            references=message.references,
            headers=message.headers,
            size=message.size,
            direction=message.direction.value,
            provider_message_id=message.provider_message_id,
            # Legacy fields
            content_raw=message.text or "",
            content_clean=message.extracted_text or "",
            message_metadata=message.headers or {},
        )


class AttachmentORM(Base):
    """Attachment storage model."""

    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    message_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )

    # File metadata
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Disposition
    disposition: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="attachment",
    )
    content_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Storage options
    # Option 1: Store content in database (for small files or simple deployments)
    content: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    # Option 2: Store in external storage (filesystem/S3/GCS)
    storage_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    storage_backend: Mapped[str | None] = mapped_column(String(50), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    message: Mapped["MessageORM"] = relationship("MessageORM", back_populates="attachments")

    __table_args__ = (
        Index("ix_attachments_message_id", "message_id"),
        Index("ix_attachments_content_id", "content_id"),
    )

    def to_pydantic(self) -> PydanticAttachment:
        """Convert ORM model to Pydantic Attachment."""
        return PydanticAttachment(
            attachment_id=self.id,
            filename=self.filename,
            size=self.size_bytes,
            content_type=self.content_type,
            content_disposition=AttachmentDisposition(self.disposition),
            content_id=self.content_id,
        )

    def to_meta(self) -> AttachmentMeta:
        """Convert ORM model to AttachmentMeta (lightweight)."""
        return AttachmentMeta(
            attachment_id=self.id,
            filename=self.filename,
            content_type=self.content_type,
            size=self.size_bytes,
            disposition=AttachmentDisposition(self.disposition),
            content_id=self.content_id,
        )

    @classmethod
    def from_pydantic(
        cls,
        attachment: PydanticAttachment,
        message_id: str,
        *,
        content: bytes | None = None,
        storage_path: str | None = None,
        storage_backend: str | None = None,
    ) -> "AttachmentORM":
        """Create ORM model from Pydantic model."""
        return cls(
            id=attachment.attachment_id,
            message_id=message_id,
            filename=attachment.filename or "unnamed",
            content_type=attachment.content_type or "application/octet-stream",
            size_bytes=attachment.size,
            disposition=attachment.content_disposition.value
            if attachment.content_disposition
            else "attachment",
            content_id=attachment.content_id,
            content=content,
            storage_path=storage_path,
            storage_backend=storage_backend,
        )


class EventORM(Base):
    """Event table for webhook notifications and tracking."""

    __tablename__ = "events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # References
    inbox_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("inboxes.id", ondelete="SET NULL"),
        nullable=True,
    )
    thread_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("threads.id", ondelete="SET NULL"),
        nullable=True,
    )
    message_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Event-specific data
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Legacy field name mapping
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="",
    )

    # Indexes
    __table_args__ = (
        Index("ix_events_event_type", "event_type"),
        Index("ix_events_inbox_id", "inbox_id"),
        Index("ix_events_timestamp", timestamp.desc()),
        Index("ix_events_created_at", created_at.desc()),
        Index("ix_events_type_created", "event_type", created_at.desc()),
    )

    def to_pydantic(self) -> PydanticEvent:
        """Convert ORM model to Pydantic model."""
        # Use event_type if available, fall back to type for legacy
        event_type_value = self.event_type or self.type
        return PydanticEvent(
            id=self.id,
            type=EventType(event_type_value),
            created_at=self.created_at,
            payload=self.payload or {},
            inbox_id=self.inbox_id,
            thread_id=self.thread_id,
            message_id=self.message_id,
        )

    @classmethod
    def from_pydantic(cls, event: PydanticEvent) -> "EventORM":
        """Create ORM model from Pydantic model."""
        return cls(
            id=event.id,
            event_type=event.type.value,
            type=event.type.value,  # Legacy compatibility
            timestamp=event.created_at,
            created_at=event.created_at,
            payload=event.payload,
            inbox_id=event.inbox_id,
            thread_id=event.thread_id,
            message_id=event.message_id,
        )
