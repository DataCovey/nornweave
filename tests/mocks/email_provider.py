"""Mock email provider for E2E testing.

Implements the full EmailProvider interface, recording all sent emails
for assertion and providing predictable message IDs.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from nornweave.core.interfaces import EmailProvider, InboundAttachment, InboundMessage
from nornweave.models.attachment import AttachmentDisposition, SendAttachment


@dataclass
class SentEmail:
    """Record of a sent email for test assertions."""

    to: list[str]
    subject: str
    body: str
    from_address: str
    reply_to: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    message_id: str | None = None
    in_reply_to: str | None = None
    references: list[str] = field(default_factory=list)
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    attachments: list[SendAttachment] = field(default_factory=list)
    html_body: str | None = None
    provider_message_id: str = ""
    sent_at: datetime = field(default_factory=datetime.utcnow)


class MockEmailProvider(EmailProvider):
    """
    Mock email provider that records all sent emails.

    Usage:
        provider = MockEmailProvider()
        await provider.send_email(...)
        assert len(provider.sent_emails) == 1
        assert provider.sent_emails[0].to == ["alice@example.com"]
    """

    def __init__(self, domain: str = "test.nornweave.local") -> None:
        """Initialize mock provider.

        Args:
            domain: Domain for generating Message-IDs.
        """
        self.domain = domain
        self.sent_emails: list[SentEmail] = []
        self._message_counter = 0

    def clear(self) -> None:
        """Clear all recorded emails."""
        self.sent_emails.clear()
        self._message_counter = 0

    def _generate_message_id(self) -> str:
        """Generate a predictable Message-ID."""
        self._message_counter += 1
        return f"<mock-{self._message_counter}-{uuid.uuid4().hex[:8]}@{self.domain}>"

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
        """
        Record a sent email and return a mock provider message ID.

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
            html_body: HTML body (optional)

        Returns:
            Mock provider message ID
        """
        # Generate message ID if not provided
        provider_message_id = message_id or self._generate_message_id()

        # Record the sent email
        sent = SentEmail(
            to=list(to),
            subject=subject,
            body=body,
            from_address=from_address,
            reply_to=reply_to,
            headers=dict(headers) if headers else {},
            message_id=message_id,
            in_reply_to=in_reply_to,
            references=list(references) if references else [],
            cc=list(cc) if cc else [],
            bcc=list(bcc) if bcc else [],
            attachments=list(attachments) if attachments else [],
            html_body=html_body,
            provider_message_id=provider_message_id,
        )
        self.sent_emails.append(sent)

        return provider_message_id

    def parse_inbound_webhook(self, payload: dict[str, Any]) -> InboundMessage:
        """
        Parse a mock webhook payload into an InboundMessage.

        Supports multiple formats:
        - Simple dict with standard fields
        - Mailgun-style payload (detected by 'sender' or 'body-plain' keys)
        - SendGrid-style payload (detected by 'envelope' key)
        - Generic format for testing

        Args:
            payload: Webhook payload dict

        Returns:
            Standardized InboundMessage
        """
        # Detect format and parse accordingly
        if "sender" in payload or "body-plain" in payload:
            return self._parse_mailgun_format(payload)
        elif "envelope" in payload:
            return self._parse_sendgrid_format(payload)
        else:
            return self._parse_generic_format(payload)

    def _parse_mailgun_format(self, payload: dict[str, Any]) -> InboundMessage:
        """Parse Mailgun-style webhook payload."""
        # Parse attachments if present
        attachments = self._parse_attachments(payload.get("attachments", []))

        # Parse references header
        references_str = payload.get("References", "")
        references = (
            [ref.strip() for ref in references_str.split() if ref.strip()] if references_str else []
        )

        return InboundMessage(
            from_address=payload.get("sender") or payload.get("from", ""),
            to_address=payload.get("recipient", ""),
            subject=payload.get("subject", ""),
            body_plain=payload.get("body-plain", ""),
            body_html=payload.get("body-html"),
            stripped_text=payload.get("stripped-text"),
            stripped_html=payload.get("stripped-html"),
            message_id=payload.get("Message-Id"),
            in_reply_to=payload.get("In-Reply-To"),
            references=references,
            timestamp=datetime.utcnow(),
            attachments=attachments,
            cc_addresses=self._parse_address_list(payload.get("Cc", "")),
        )

    def _parse_sendgrid_format(self, payload: dict[str, Any]) -> InboundMessage:
        """Parse SendGrid-style webhook payload."""
        envelope = payload.get("envelope", {})
        headers = payload.get("headers", "")

        # Parse headers string to dict (SendGrid sends as newline-separated)
        header_dict: dict[str, str] = {}
        if isinstance(headers, str):
            for line in headers.split("\n"):
                if ": " in line:
                    key, value = line.split(": ", 1)
                    header_dict[key.strip()] = value.strip()

        # Parse attachments
        attachments = self._parse_attachments(payload.get("attachments", []))

        return InboundMessage(
            from_address=payload.get("from", envelope.get("from", "")),
            to_address=envelope.get("to", [""])[0] if envelope.get("to") else "",
            subject=payload.get("subject", ""),
            body_plain=payload.get("text", ""),
            body_html=payload.get("html"),
            message_id=header_dict.get("Message-ID") or header_dict.get("Message-Id"),
            in_reply_to=header_dict.get("In-Reply-To"),
            references=header_dict.get("References", "").split()
            if header_dict.get("References")
            else [],
            timestamp=datetime.utcnow(),
            attachments=attachments,
            spf_result=payload.get("SPF"),
            dkim_result=payload.get("dkim"),
            headers=header_dict,
        )

    def _parse_generic_format(self, payload: dict[str, Any]) -> InboundMessage:
        """Parse generic/test webhook payload format."""
        attachments = self._parse_attachments(payload.get("attachments", []))

        return InboundMessage(
            from_address=payload.get("from_address", payload.get("from", "")),
            to_address=payload.get("to_address", payload.get("to", "")),
            subject=payload.get("subject", ""),
            body_plain=payload.get("body_plain", payload.get("body", "")),
            body_html=payload.get("body_html"),
            stripped_text=payload.get("stripped_text"),
            stripped_html=payload.get("stripped_html"),
            message_id=payload.get("message_id"),
            in_reply_to=payload.get("in_reply_to"),
            references=payload.get("references", []),
            timestamp=payload.get("timestamp", datetime.utcnow()),
            attachments=attachments,
            cc_addresses=payload.get("cc_addresses", []),
            bcc_addresses=payload.get("bcc_addresses", []),
            headers=payload.get("headers", {}),
        )

    def _parse_attachments(self, attachments_data: list[dict[str, Any]]) -> list[InboundAttachment]:
        """Parse attachments from webhook payload."""
        result: list[InboundAttachment] = []

        for att in attachments_data:
            # Handle base64 content
            content = att.get("content", b"")
            if isinstance(content, str):
                import base64

                try:
                    content = base64.b64decode(content)
                except ValueError, TypeError:
                    content = content.encode("utf-8")

            disposition_str = att.get("disposition", "attachment")
            disposition = (
                AttachmentDisposition.INLINE
                if disposition_str == "inline"
                else AttachmentDisposition.ATTACHMENT
            )

            result.append(
                InboundAttachment(
                    filename=att.get("filename", "unknown"),
                    content_type=att.get(
                        "content_type", att.get("content-type", "application/octet-stream")
                    ),
                    content=content,
                    size_bytes=att.get("size_bytes", att.get("size", len(content))),
                    disposition=disposition,
                    content_id=att.get("content_id", att.get("content-id")),
                )
            )

        return result

    def _parse_address_list(self, addresses: str | list[str]) -> list[str]:
        """Parse comma-separated address string or list into list."""
        if isinstance(addresses, list):
            return addresses
        if not addresses:
            return []
        return [addr.strip() for addr in addresses.split(",") if addr.strip()]

    async def setup_inbound_route(self, inbox_address: str) -> None:
        """No-op for mock provider."""
        _ = inbox_address  # Intentionally unused

    # -------------------------------------------------------------------------
    # Helper methods for test assertions
    # -------------------------------------------------------------------------

    def get_last_sent(self) -> SentEmail | None:
        """Get the most recently sent email, or None if no emails sent."""
        return self.sent_emails[-1] if self.sent_emails else None

    def get_sent_to(self, recipient: str) -> list[SentEmail]:
        """Get all emails sent to a specific recipient."""
        return [
            email
            for email in self.sent_emails
            if recipient in email.to or recipient in email.cc or recipient in email.bcc
        ]

    def get_sent_with_subject(self, subject: str) -> list[SentEmail]:
        """Get all emails with a specific subject (case-insensitive)."""
        subject_lower = subject.lower()
        return [email for email in self.sent_emails if subject_lower in email.subject.lower()]

    def assert_sent_count(self, expected: int) -> None:
        """Assert the number of emails sent."""
        actual = len(self.sent_emails)
        if actual != expected:
            raise AssertionError(
                f"Expected {expected} emails sent, but got {actual}. "
                f"Subjects: {[e.subject for e in self.sent_emails]}"
            )

    def assert_last_sent_to(self, expected_recipients: list[str]) -> None:
        """Assert the recipients of the last sent email."""
        last = self.get_last_sent()
        if last is None:
            raise AssertionError("No emails have been sent")
        if sorted(last.to) != sorted(expected_recipients):
            raise AssertionError(f"Expected recipients {expected_recipients}, but got {last.to}")
