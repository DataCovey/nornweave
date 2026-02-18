"""Demo/sandbox email provider.

Local-only mock provider for trying NornWeave without a real domain or
credentials. No email is sent; parse_inbound_webhook accepts a generic
JSON format for simulating inbound mail (e.g. POST /v1/demo/inbound).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from nornweave.core.interfaces import EmailProvider, InboundAttachment, InboundMessage
from nornweave.models.attachment import AttachmentDisposition, SendAttachment


class DemoAdapter(EmailProvider):
    """
    Demo email provider: records sent emails and returns synthetic message IDs.

    Used when EMAIL_PROVIDER=demo or when running `nornweave api --demo`.
    No real email is delivered. For inbound simulation, use POST /v1/demo/inbound
    with a payload that parse_inbound_webhook accepts (generic format).
    """

    def __init__(self, domain: str = "demo.nornweave.local") -> None:
        """Initialize demo adapter.

        Args:
            domain: Domain for generating Message-IDs and inbox addresses.
        """
        self.domain = domain
        self._message_counter = 0

    def _generate_message_id(self) -> str:
        """Generate a synthetic Message-ID."""
        self._message_counter += 1
        return f"<demo-{self._message_counter}-{uuid.uuid4().hex[:8]}@{self.domain}>"

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
        """Record the send and return a synthetic provider message ID."""
        _ = to, subject, body, from_address, reply_to, headers, in_reply_to, references, cc, bcc, attachments, html_body
        return message_id or self._generate_message_id()

    def parse_inbound_webhook(self, payload: dict[str, Any]) -> InboundMessage:
        """Parse a generic JSON payload into an InboundMessage.

        Expected keys: from_address (or from), to_address (or to), subject,
        body_plain (or body). Optional: body_html, message_id, in_reply_to,
        references (list or space-separated string), timestamp, attachments,
        cc_addresses, bcc_addresses, headers.
        """
        refs = payload.get("references", [])
        if isinstance(refs, str):
            refs = [r.strip() for r in refs.split() if r.strip()]
        ts = payload.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                ts = datetime.now(UTC)
        elif ts is None:
            ts = datetime.now(UTC)
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
            references=refs,
            timestamp=ts,
            attachments=attachments,
            cc_addresses=payload.get("cc_addresses", []),
            bcc_addresses=payload.get("bcc_addresses", []),
            headers=payload.get("headers", {}),
        )

    def _parse_attachments(self, attachments_data: list[dict[str, Any]]) -> list[InboundAttachment]:
        """Parse attachments from webhook payload."""
        result: list[InboundAttachment] = []
        for att in attachments_data:
            content = att.get("content", b"")
            if isinstance(content, str):
                import base64

                try:
                    content = base64.b64decode(content)
                except (ValueError, TypeError):
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

    async def setup_inbound_route(self, inbox_address: str) -> None:
        """No-op for demo provider."""
        _ = inbox_address
