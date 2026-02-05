"""IMAP/SMTP email provider adapter.

Composes SmtpSender (outbound via aiosmtplib) and ImapReceiver (inbound via
aioimaplib) behind a SmtpImapAdapter facade that implements the EmailProvider ABC.
"""

import base64
import logging
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from typing import TYPE_CHECKING, Any

import markdown  # type: ignore[import-untyped]

from nornweave.core.interfaces import (
    EmailProvider,
    InboundMessage,
)
from nornweave.verdandi.email_parser import parse_raw_email

if TYPE_CHECKING:
    from nornweave.core.config import Settings
    from nornweave.models.attachment import SendAttachment

logger = logging.getLogger(__name__)


# =============================================================================
# SmtpSender — outbound email via aiosmtplib
# =============================================================================
class SmtpSender:
    """Send emails via SMTP using aiosmtplib.

    Supports STARTTLS (port 587) and implicit TLS (port 465), authentication,
    threading headers, CC/BCC, attachments, and Markdown→HTML conversion.
    """

    def __init__(
        self,
        host: str,
        port: int = 587,
        username: str = "",
        password: str = "",
        use_tls: bool = True,
    ) -> None:
        """Initialize SMTP sender.

        Args:
            host: SMTP server hostname.
            port: SMTP server port (587 for STARTTLS, 465 for implicit TLS).
            username: SMTP username for authentication.
            password: SMTP password for authentication.
            use_tls: Whether to use TLS (STARTTLS or implicit).
        """
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_tls = use_tls

    async def send_email(
        self,
        to: list[str],
        subject: str,
        body: str,
        *,
        from_address: str,
        reply_to: str | None = None,
        headers: dict[str, str] | None = None,
        message_id: str | None = None,
        in_reply_to: str | None = None,
        references: list[str] | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[SendAttachment] | None = None,
        html_body: str | None = None,
    ) -> str:
        """Send an email via SMTP.

        Returns:
            Generated Message-ID as the provider message ID.
        """
        import aiosmtplib

        # Generate Message-ID if not provided
        msg_id = message_id or make_msgid(domain=from_address.split("@")[-1])

        # Build the message
        msg = self._build_message(
            to=to,
            subject=subject,
            body=body,
            from_address=from_address,
            reply_to=reply_to,
            headers=headers,
            message_id=msg_id,
            in_reply_to=in_reply_to,
            references=references,
            cc=cc,
            attachments=attachments,
            html_body=html_body,
        )

        # Collect all recipients for SMTP envelope
        all_recipients = list(to)
        if cc:
            all_recipients.extend(cc)
        if bcc:
            all_recipients.extend(bcc)

        # Send via SMTP
        logger.debug("Sending email via SMTP to %s via %s:%s", to, self._host, self._port)

        # Determine TLS mode
        use_tls_kwarg = self._use_tls and self._port == 465  # Implicit TLS
        start_tls_kwarg = self._use_tls and self._port != 465  # STARTTLS

        try:
            await aiosmtplib.send(
                msg,
                hostname=self._host,
                port=self._port,
                username=self._username or None,
                password=self._password or None,
                use_tls=use_tls_kwarg,
                start_tls=start_tls_kwarg,
                recipients=all_recipients,
            )
        except aiosmtplib.SMTPException as e:
            logger.error(
                "SMTP send failed to %s via %s:%s: %s",
                to,
                self._host,
                self._port,
                e,
            )
            raise

        logger.info("Email sent via SMTP: %s", msg_id)
        return msg_id

    def _build_message(
        self,
        to: list[str],
        subject: str,
        body: str,
        *,
        from_address: str,
        reply_to: str | None,
        headers: dict[str, str] | None,
        message_id: str,
        in_reply_to: str | None,
        references: list[str] | None,
        cc: list[str] | None,
        attachments: list[SendAttachment] | None,
        html_body: str | None,
    ) -> EmailMessage:
        """Build an EmailMessage with all headers, body, and attachments."""
        msg = EmailMessage()

        # Core headers
        msg["From"] = from_address
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = message_id

        if cc:
            msg["Cc"] = ", ".join(cc)
        if reply_to:
            msg["Reply-To"] = reply_to
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
        if references:
            msg["References"] = " ".join(references)

        # Custom headers
        if headers:
            for key, value in headers.items():
                if key.lower() not in (
                    "from",
                    "to",
                    "subject",
                    "date",
                    "message-id",
                    "cc",
                    "reply-to",
                    "in-reply-to",
                    "references",
                ):
                    msg[key] = value

        # Convert Markdown to HTML if html_body not provided
        html_content = html_body or markdown.markdown(body)

        if attachments:
            # multipart/mixed with alternative body + attachments
            msg.set_content(body)
            msg.add_alternative(html_content, subtype="html")

            for att in attachments:
                if att.content is None:
                    continue
                # Decode base64 content from SendAttachment
                try:
                    content_bytes = base64.b64decode(att.content)
                except Exception:
                    content_bytes = (
                        att.content.encode("utf-8") if isinstance(att.content, str) else att.content
                    )

                maintype, _, subtype = (att.content_type or "application/octet-stream").partition(
                    "/"
                )

                disposition = (
                    "inline"
                    if (att.content_disposition and att.content_disposition.lower() == "inline")
                    else "attachment"
                )

                extra_kwargs: dict[str, Any] = {}
                if disposition == "inline" and att.content_id:
                    extra_kwargs["cid"] = att.content_id.strip("<>")

                msg.add_attachment(
                    content_bytes,
                    maintype=maintype,
                    subtype=subtype or "octet-stream",
                    filename=att.filename,
                    disposition=disposition,
                    **extra_kwargs,
                )
        else:
            # multipart/alternative with text + html
            msg.set_content(body)
            msg.add_alternative(html_content, subtype="html")

        return msg


# =============================================================================
# ImapReceiver — inbound email via aioimaplib
# =============================================================================
class ImapReceiver:
    """Receive emails via IMAP polling using aioimaplib.

    Handles connection management, UID-based message fetching, UIDVALIDITY
    tracking, and post-fetch flag management (mark-as-read, delete).
    """

    def __init__(
        self,
        host: str,
        port: int = 993,
        username: str = "",
        password: str = "",
        use_ssl: bool = True,
        mailbox: str = "INBOX",
        mark_as_read: bool = True,
        delete_after_fetch: bool = False,
    ) -> None:
        """Initialize IMAP receiver."""
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_ssl = use_ssl
        self._mailbox = mailbox
        self._mark_as_read = mark_as_read
        self._delete_after_fetch = delete_after_fetch
        self._client: Any = None

    async def connect(self) -> None:
        """Connect to IMAP server, authenticate, and select mailbox."""
        import aioimaplib

        logger.info("Connecting to IMAP server %s:%s", self._host, self._port)

        if self._use_ssl:
            self._client = aioimaplib.IMAP4_SSL(
                host=self._host,
                port=self._port,
            )
        else:
            self._client = aioimaplib.IMAP4(
                host=self._host,
                port=self._port,
            )

        await self._client.wait_hello_from_server()
        await self._client.login(self._username, self._password)
        await self._client.select(self._mailbox)
        logger.info("Connected to IMAP: %s/%s", self._host, self._mailbox)

    async def disconnect(self) -> None:
        """Disconnect from IMAP server."""
        if self._client:
            try:
                await self._client.logout()
            except Exception:
                logger.debug("IMAP logout failed (connection may already be closed)")
            self._client = None

    async def get_uid_validity(self) -> int:
        """Get UIDVALIDITY for the selected mailbox."""
        if not self._client:
            raise RuntimeError("Not connected to IMAP server")

        # UIDVALIDITY is returned in the SELECT response
        # aioimaplib stores it in the protocol state
        response = await self._client.select(self._mailbox)
        # Parse UIDVALIDITY from response data
        for line in response.lines:
            line_str = str(line)
            if "UIDVALIDITY" in line_str:
                # Extract number from e.g. "OK [UIDVALIDITY 12345]"
                import re

                match = re.search(r"UIDVALIDITY\s+(\d+)", line_str)
                if match:
                    return int(match.group(1))
        return 0

    async def fetch_new_messages(self, last_uid: int) -> list[tuple[int, bytes]]:
        """Fetch messages with UID greater than last_uid.

        Args:
            last_uid: The last processed UID. Use 0 to fetch all.

        Returns:
            List of (uid, raw_bytes) tuples for each new message.
        """
        if not self._client:
            raise RuntimeError("Not connected to IMAP server")

        # Always search ALL and filter by UID client-side for maximum
        # IMAP server compatibility (some servers don't support UID range criteria)
        search_criteria = "ALL"
        response = await self._client.uid_search(search_criteria)

        if response.result != "OK":
            logger.warning("IMAP UID SEARCH failed: %s", response.lines)
            return []

        # Parse UIDs from response
        raw_line = response.lines[0] if response.lines else b""
        uid_line = raw_line.decode() if isinstance(raw_line, bytes) else str(raw_line)
        uid_strings = uid_line.split()
        uids = [int(u) for u in uid_strings if u.isdigit() and int(u) > last_uid]

        if not uids:
            return []

        logger.info("Found %d new messages (UIDs %d-%d)", len(uids), uids[0], uids[-1])

        # Fetch each message
        messages: list[tuple[int, bytes]] = []
        for uid in uids:
            try:
                response = await self._client.uid("fetch", str(uid), "(RFC822)")
                if response.result == "OK" and response.lines:
                    # aioimaplib returns lines like:
                    #   [0] b'1 FETCH (RFC822 {315})'  — envelope/header
                    #   [1] bytearray(b'From: ...\r\n...')  — the actual RFC822 body
                    #   [2] b')'  — closing paren
                    #   [3] b'FETCH completed...'
                    # The email body is typically a bytearray; fall back to
                    # the largest bytes-like object if not found.
                    raw_bytes: bytes | None = None
                    for line in response.lines:
                        if isinstance(line, bytearray):
                            raw_bytes = bytes(line)
                            break
                    if raw_bytes is None:
                        # Fallback: look for the largest bytes line (skip envelope)
                        candidates = [
                            bytes(line) if isinstance(line, bytearray) else line
                            for line in response.lines
                            if isinstance(line, (bytes, bytearray)) and len(line) > 50
                        ]
                        if candidates:
                            raw_bytes = max(candidates, key=len)
                    if raw_bytes is not None:
                        messages.append((uid, raw_bytes))
                    else:
                        logger.warning(
                            "No RFC822 body in fetch response for UID %d: %r",
                            uid,
                            [(type(line).__name__, len(line)) for line in response.lines],
                        )
            except Exception:
                logger.warning("Failed to fetch UID %d", uid, exc_info=True)

        return messages

    async def mark_as_read(self, uid: int) -> None:
        """Set \\Seen flag on a message."""
        if not self._client or not self._mark_as_read:
            return
        try:
            await self._client.uid("store", str(uid), "+FLAGS", "(\\Seen)")
        except Exception:
            logger.warning("Failed to mark UID %d as read", uid, exc_info=True)

    async def delete_message(self, uid: int) -> None:
        """Flag message as \\Deleted and expunge."""
        if not self._client or not self._delete_after_fetch:
            return
        try:
            await self._client.uid("store", str(uid), "+FLAGS", "(\\Deleted)")
            await self._client.expunge()
        except Exception:
            logger.warning("Failed to delete UID %d", uid, exc_info=True)

    def parse_message(self, raw_bytes: bytes) -> InboundMessage:
        """Parse raw email bytes into InboundMessage using the email parser."""
        return parse_raw_email(raw_bytes)


# =============================================================================
# SmtpImapAdapter — EmailProvider facade
# =============================================================================
class SmtpImapAdapter(EmailProvider):
    """IMAP/SMTP implementation of EmailProvider.

    Composes SmtpSender for outbound email and ImapReceiver for inbound.
    The parse_inbound_webhook() method raises NotImplementedError since
    IMAP doesn't use webhooks — the ImapPoller feeds messages directly
    into the ingestion pipeline.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize from application settings."""
        self.sender = SmtpSender(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            use_tls=settings.smtp_use_tls,
        )
        self.receiver = ImapReceiver(
            host=settings.imap_host,
            port=settings.imap_port,
            username=settings.imap_username,
            password=settings.imap_password,
            use_ssl=settings.imap_use_ssl,
            mailbox=settings.imap_mailbox,
            mark_as_read=settings.imap_mark_as_read,
            delete_after_fetch=settings.imap_delete_after_fetch,
        )

    async def send_email(
        self,
        to: list[str],
        subject: str,
        body: str,
        *,
        from_address: str,
        reply_to: str | None = None,
        headers: dict[str, str] | None = None,
        message_id: str | None = None,
        in_reply_to: str | None = None,
        references: list[str] | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[SendAttachment] | None = None,
        html_body: str | None = None,
    ) -> str:
        """Send email via SMTP, delegating to SmtpSender."""
        return await self.sender.send_email(
            to=to,
            subject=subject,
            body=body,
            from_address=from_address,
            reply_to=reply_to,
            headers=headers,
            message_id=message_id,
            in_reply_to=in_reply_to,
            references=references,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            html_body=html_body,
        )

    def parse_inbound_webhook(self, payload: dict[str, Any]) -> InboundMessage:
        """Not supported — IMAP does not use webhooks.

        Raises:
            NotImplementedError: Always. Use ImapPoller for inbound email.
        """
        raise NotImplementedError(
            "IMAP/SMTP adapter does not support webhooks. Use the IMAP poller for inbound email."
        )
