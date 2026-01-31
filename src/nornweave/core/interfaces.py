"""Core abstractions: storage and email provider interfaces."""

from abc import ABC, abstractmethod
from typing import Any

from nornweave.models.inbox import Inbox
from nornweave.models.thread import Thread
from nornweave.models.message import Message


class InboundMessage:
    """Standardized representation of an inbound email from a provider webhook."""

    def __init__(
        self,
        *,
        from_address: str,
        to_address: str,
        subject: str,
        body_raw: str,
        body_html: str | None = None,
        message_id: str | None = None,
        references: str | None = None,
        in_reply_to: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.from_address = from_address
        self.to_address = to_address
        self.subject = subject
        self.body_raw = body_raw
        self.body_html = body_html
        self.message_id = message_id
        self.references = references
        self.in_reply_to = in_reply_to
        self.headers = headers or {}


class StorageInterface(ABC):
    """Abstract storage layer (Urdr - The Well). Implementations: Postgres, SQLite."""

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
    async def create_thread(self, thread: Thread) -> Thread:
        """Create a thread."""
        ...

    @abstractmethod
    async def get_thread(self, thread_id: str) -> Thread | None:
        """Get a thread by id."""
        ...

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
        """List messages for an inbox."""
        ...

    @abstractmethod
    async def list_threads_for_inbox(
        self,
        inbox_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Thread]:
        """List threads for an inbox."""
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
    ) -> str:
        """Send an email. Returns provider message id."""
        ...

    @abstractmethod
    def parse_inbound_webhook(self, payload: dict[str, Any]) -> InboundMessage:
        """Parse provider webhook payload into a standardized InboundMessage."""
        ...

    async def setup_inbound_route(self, inbox_address: str) -> None:
        """Optional: configure provider to route inbound mail to our webhook."""
        pass
