"""Core abstractions: storage and email provider interfaces."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from nornweave.models.attachment import AttachmentDisposition, SendAttachment

if TYPE_CHECKING:
    from nornweave.models.event import Event, EventType
    from nornweave.models.inbox import Inbox
    from nornweave.models.message import Message
    from nornweave.models.thread import Thread


@dataclass
class InboundAttachment:
    """
    Attachment parsed from inbound email webhook.

    Contains full content for storage and processing.
    """

    filename: str
    content_type: str
    content: bytes
    size_bytes: int
    disposition: AttachmentDisposition = AttachmentDisposition.ATTACHMENT
    content_id: str | None = None
    provider_id: str | None = None
    provider_url: str | None = None

    @classmethod
    def from_base64(
        cls,
        filename: str,
        content_type: str,
        content_base64: str,
        *,
        disposition: AttachmentDisposition = AttachmentDisposition.ATTACHMENT,
        content_id: str | None = None,
    ) -> InboundAttachment:
        """Create attachment from base64-encoded content."""
        import base64

        content = base64.b64decode(content_base64)
        return cls(
            filename=filename,
            content_type=content_type,
            content=content,
            size_bytes=len(content),
            disposition=disposition,
            content_id=content_id,
        )


@dataclass
class InboundMessage:
    """
    Standardized representation of an inbound email from a provider webhook.

    Enhanced with full attachment support, threading headers, and verification results.
    """

    # Envelope data
    from_address: str
    to_address: str
    subject: str

    # Body content
    body_plain: str
    body_html: str | None = None
    stripped_text: str | None = None
    stripped_html: str | None = None

    # Threading headers (RFC 5322)
    message_id: str | None = None
    in_reply_to: str | None = None
    references: list[str] = field(default_factory=list)

    # Metadata
    headers: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Full attachment support
    attachments: list[InboundAttachment] = field(default_factory=list)
    content_id_map: dict[str, str] = field(default_factory=dict)

    # Provider verification (for audit/spam detection)
    spf_result: str | None = None
    dkim_result: str | None = None
    dmarc_result: str | None = None

    # CC/BCC support
    cc_addresses: list[str] = field(default_factory=list)
    bcc_addresses: list[str] = field(default_factory=list)

    @property
    def attachment_count(self) -> int:
        """Get total number of attachments."""
        return len(self.attachments)

    @property
    def inline_attachments(self) -> list[InboundAttachment]:
        """Get only inline attachments (embedded images, etc.)."""
        return [a for a in self.attachments if a.disposition == AttachmentDisposition.INLINE]

    @property
    def regular_attachments(self) -> list[InboundAttachment]:
        """Get only regular file attachments."""
        return [a for a in self.attachments if a.disposition == AttachmentDisposition.ATTACHMENT]

    def get_attachment_by_content_id(self, content_id: str) -> InboundAttachment | None:
        """Find attachment by Content-ID (for cid: URL resolution)."""
        cid = content_id.strip("<>")
        for attachment in self.attachments:
            if attachment.content_id and attachment.content_id.strip("<>") == cid:
                return attachment
        return None

    @property
    def total_attachment_size(self) -> int:
        """Get total size of all attachments in bytes."""
        return sum(a.size_bytes for a in self.attachments)

    def parse_references_string(self, references_str: str | None) -> list[str]:
        """Parse space-separated References header into list."""
        if not references_str:
            return []
        return [ref.strip() for ref in references_str.split() if ref.strip()]


class StorageInterface(ABC):
    """Abstract storage layer (Urdr - The Well). Implementations: Postgres, SQLite."""

    # -------------------------------------------------------------------------
    # Inbox methods
    # -------------------------------------------------------------------------
    @abstractmethod
    async def create_inbox(self, inbox: Inbox) -> Inbox:
        """Create an inbox. Returns the created inbox with id set."""
        ...

    @abstractmethod
    async def get_inbox(self, inbox_id: str) -> Inbox | None:
        """Get an inbox by id."""
        ...

    @abstractmethod
    async def get_inbox_by_email(self, email_address: str) -> Inbox | None:
        """Get an inbox by email address."""
        ...

    @abstractmethod
    async def delete_inbox(self, inbox_id: str) -> bool:
        """Delete an inbox. Returns True if deleted."""
        ...

    @abstractmethod
    async def list_inboxes(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Inbox]:
        """List all inboxes."""
        ...

    # -------------------------------------------------------------------------
    # Thread methods
    # -------------------------------------------------------------------------
    @abstractmethod
    async def create_thread(self, thread: Thread) -> Thread:
        """Create a thread."""
        ...

    @abstractmethod
    async def get_thread(self, thread_id: str) -> Thread | None:
        """Get a thread by id."""
        ...

    @abstractmethod
    async def get_thread_by_participant_hash(
        self,
        inbox_id: str,
        participant_hash: str,
    ) -> Thread | None:
        """Get a thread by inbox and participant hash (Phase 2 threading)."""
        ...

    @abstractmethod
    async def update_thread(self, thread: Thread) -> Thread:
        """Update a thread (e.g. last_message_at)."""
        ...

    @abstractmethod
    async def list_threads_for_inbox(
        self,
        inbox_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Thread]:
        """List threads for an inbox, ordered by last_message_at DESC."""
        ...

    # -------------------------------------------------------------------------
    # Message methods
    # -------------------------------------------------------------------------
    @abstractmethod
    async def create_message(self, message: Message) -> Message:
        """Create a message."""
        ...

    @abstractmethod
    async def get_message(self, message_id: str) -> Message | None:
        """Get a message by id."""
        ...

    @abstractmethod
    async def list_messages_for_inbox(
        self,
        inbox_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        """List messages for an inbox, ordered by created_at."""
        ...

    @abstractmethod
    async def list_messages_for_thread(
        self,
        thread_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Message]:
        """List messages for a thread, ordered by created_at (conversation order)."""
        ...

    @abstractmethod
    async def search_messages(
        self,
        inbox_id: str,
        query: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        """Search messages by content (ILIKE/LIKE on content_clean and content_raw)."""
        ...

    # -------------------------------------------------------------------------
    # Event methods (Phase 3 webhooks)
    # -------------------------------------------------------------------------
    @abstractmethod
    async def create_event(self, event: Event) -> Event:
        """Create an event. Returns the created event with id set."""
        ...

    @abstractmethod
    async def get_event(self, event_id: str) -> Event | None:
        """Get an event by id."""
        ...

    @abstractmethod
    async def list_events(
        self,
        *,
        event_type: EventType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Event]:
        """List events, optionally filtered by type, ordered by created_at DESC."""
        ...

    # -------------------------------------------------------------------------
    # Attachment methods
    # -------------------------------------------------------------------------
    @abstractmethod
    async def create_attachment(
        self,
        message_id: str,
        filename: str,
        content_type: str,
        size_bytes: int,
        *,
        disposition: str = "attachment",
        content_id: str | None = None,
        storage_path: str | None = None,
        storage_backend: str | None = None,
    ) -> str:
        """Create attachment record. Returns attachment ID."""
        ...

    @abstractmethod
    async def get_attachment(self, attachment_id: str) -> dict[str, Any] | None:
        """Get attachment metadata by ID."""
        ...

    @abstractmethod
    async def list_attachments_for_message(self, message_id: str) -> list[dict[str, Any]]:
        """List attachments for a message."""
        ...

    @abstractmethod
    async def delete_attachment(self, attachment_id: str) -> bool:
        """Delete attachment. Returns True if deleted."""
        ...

    # -------------------------------------------------------------------------
    # Thread lookup methods (for threading algorithm)
    # -------------------------------------------------------------------------
    @abstractmethod
    async def get_message_by_provider_id(
        self, inbox_id: str, provider_message_id: str
    ) -> Message | None:
        """Get message by provider Message-ID header for threading lookups."""
        ...

    @abstractmethod
    async def get_thread_by_subject(
        self,
        inbox_id: str,
        normalized_subject: str,
        *,
        since: datetime | None = None,
    ) -> Thread | None:
        """Get thread by normalized subject within time window (for subject-based threading)."""
        ...


class EmailProvider(ABC):
    """Abstract email provider (BYOP). Implementations: Mailgun, SES, SendGrid, Resend."""

    @abstractmethod
    async def send_email(
        self,
        to: list[str],
        subject: str,
        body: str,
        *,
        from_address: str,
        reply_to: str | None = None,
        headers: dict[str, str] | None = None,
        # Threading headers for proper reply threading
        message_id: str | None = None,
        in_reply_to: str | None = None,
        references: list[str] | None = None,
        # CC/BCC support
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        # Attachment support
        attachments: list[SendAttachment] | None = None,
        # HTML body (alternative to plain text)
        html_body: str | None = None,
    ) -> str:
        """
        Send an email with threading and attachment support.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Plain text body
            from_address: Sender email address
            reply_to: Reply-to address (optional)
            headers: Custom headers (optional)
            message_id: RFC 5322 Message-ID (generated if None)
            in_reply_to: Parent Message-ID for replies
            references: Chain of ancestor Message-IDs for threading
            cc: Carbon copy recipients
            bcc: Blind carbon copy recipients
            attachments: List of attachments to include
            html_body: HTML body (optional, alternative to plain text)

        Returns:
            Provider message ID
        """
        ...

    @abstractmethod
    def parse_inbound_webhook(self, payload: dict[str, Any]) -> InboundMessage:
        """Parse provider webhook payload into a standardized InboundMessage."""
        ...

    async def setup_inbound_route(self, inbox_address: str) -> None:  # noqa: B027
        """Optional: configure provider to route inbound mail to our webhook."""
        pass
