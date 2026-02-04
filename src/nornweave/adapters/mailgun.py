"""Mailgun email provider adapter."""

import logging
from typing import TYPE_CHECKING, Any

import httpx
import markdown  # type: ignore[import-untyped]

from nornweave.core.interfaces import EmailProvider, InboundMessage

if TYPE_CHECKING:
    from nornweave.models.attachment import SendAttachment

logger = logging.getLogger(__name__)


class MailgunAdapter(EmailProvider):
    """Mailgun implementation of EmailProvider."""

    def __init__(self, api_key: str, domain: str, api_url: str = "https://api.mailgun.net") -> None:
        """Initialize Mailgun adapter.

        Args:
            api_key: Mailgun API key
            domain: Mailgun domain (e.g., mail.example.com)
            api_url: Mailgun API URL (default: https://api.mailgun.net)
        """
        self._api_key = api_key
        self._domain = domain
        self._api_url = api_url.rstrip("/")

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
        """Send email via Mailgun API.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body in Markdown format
            from_address: Sender email address
            reply_to: Optional reply-to address
            headers: Optional custom headers
            message_id: Optional custom Message-ID
            in_reply_to: Optional In-Reply-To header for threading
            references: Optional References header for threading
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            attachments: Optional list of attachments
            html_body: Optional pre-rendered HTML body (if not provided, body is converted from Markdown)

        Returns:
            Provider message ID from Mailgun
        """
        url = f"{self._api_url}/v3/{self._domain}/messages"

        # Convert Markdown body to HTML if html_body not provided
        html_content = html_body or markdown.markdown(body)

        # Build form data
        data: dict[str, Any] = {
            "from": from_address,
            "to": to,
            "subject": subject,
            "text": body,
            "html": html_content,
        }

        if reply_to:
            data["h:Reply-To"] = reply_to

        if cc:
            data["cc"] = cc

        if bcc:
            data["bcc"] = bcc

        if message_id:
            data["h:Message-Id"] = message_id

        if in_reply_to:
            data["h:In-Reply-To"] = in_reply_to

        if references:
            data["h:References"] = " ".join(references)

        # Add custom headers
        if headers:
            for key, value in headers.items():
                data[f"h:{key}"] = value

        # Prepare files for attachments
        files: list[tuple[str, tuple[str, bytes, str]]] = []
        if attachments:
            for att in attachments:
                content_bytes = att.get_content_bytes()
                if att.filename and content_bytes and att.content_type:
                    files.append(("attachment", (att.filename, content_bytes, att.content_type)))

        logger.debug("Sending email via Mailgun to %s", to)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                auth=("api", self._api_key),
                data=data,
                files=files if files else None,
                timeout=30.0,
            )

            if response.status_code != 200:
                logger.error(
                    "Mailgun API error: %s - %s",
                    response.status_code,
                    response.text,
                )
                response.raise_for_status()

            result = response.json()
            provider_message_id: str = result.get("id", "")
            logger.info("Email sent via Mailgun: %s", provider_message_id)
            return provider_message_id

    def parse_inbound_webhook(self, payload: dict[str, Any]) -> InboundMessage:
        """Parse Mailgun inbound webhook payload into standardized InboundMessage.

        Mailgun sends inbound emails as multipart/form-data with fields like:
        - sender, from, recipient, subject
        - body-plain, body-html, stripped-text, stripped-html
        - Message-Id, In-Reply-To, References
        - message-headers (JSON array of [name, value] pairs)
        - timestamp, signature, token
        - attachment-count, attachment-1, attachment-2, etc.
        """
        from datetime import UTC, datetime

        # Parse sender - extract email from "Name <email>" format
        from_field = payload.get("from", payload.get("sender", ""))
        from_address = from_field
        if "<" in from_field and ">" in from_field:
            from_address = from_field.split("<")[1].split(">")[0]

        # Parse recipient
        to_address = payload.get("recipient", "")

        # Parse headers from JSON array if present
        headers: dict[str, str] = {}
        headers_raw = payload.get("message-headers", "")
        if headers_raw:
            try:
                import json

                headers_list = json.loads(headers_raw)
                headers = {h[0]: h[1] for h in headers_list if len(h) >= 2}
            except (json.JSONDecodeError, TypeError):
                pass

        # Parse references into list
        references_str = payload.get("References", "") or ""
        references = [ref.strip() for ref in references_str.split() if ref.strip()]

        # Parse timestamp
        timestamp_unix = payload.get("timestamp")
        if timestamp_unix:
            timestamp = datetime.fromtimestamp(int(timestamp_unix), tz=UTC)
        else:
            timestamp = datetime.now(UTC)

        return InboundMessage(
            from_address=from_address,
            to_address=to_address,
            subject=payload.get("subject", ""),
            body_plain=payload.get("body-plain", ""),
            body_html=payload.get("body-html"),
            stripped_text=payload.get("stripped-text"),
            stripped_html=payload.get("stripped-html"),
            message_id=payload.get("Message-Id"),
            in_reply_to=payload.get("In-Reply-To") or None,
            references=references,
            headers=headers,
            timestamp=timestamp,
        )
