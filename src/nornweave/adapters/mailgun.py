"""Mailgun email provider adapter."""

import logging
from typing import TYPE_CHECKING, Any

import httpx
import markdown

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
                files.append(("attachment", (att.filename, att.content, att.content_type)))

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
            provider_message_id = result.get("id", "")
            logger.info("Email sent via Mailgun: %s", provider_message_id)
            return provider_message_id

    def parse_inbound_webhook(self, payload: dict[str, Any]) -> InboundMessage:
        """Parse Mailgun inbound webhook payload.

        TODO: Implement Mailgun webhook payload parsing.
        """
        raise NotImplementedError("MailgunAdapter.parse_inbound_webhook")
