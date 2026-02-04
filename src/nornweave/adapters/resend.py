"""Resend email provider adapter."""

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import httpx
import markdown  # type: ignore[import-untyped]
from svix.webhooks import Webhook, WebhookVerificationError

from nornweave.core.interfaces import (
    EmailProvider,
    InboundAttachment,
    InboundMessage,
)
from nornweave.models.attachment import AttachmentDisposition

if TYPE_CHECKING:
    from nornweave.models.attachment import SendAttachment

logger = logging.getLogger(__name__)

# Resend API base URL
RESEND_API_URL = "https://api.resend.com"


class ResendWebhookError(Exception):
    """Raised when webhook verification or parsing fails."""

    pass


class ResendAdapter(EmailProvider):
    """Resend implementation of EmailProvider.

    Supports:
    - Sending emails via Resend API
    - Parsing inbound webhook payloads (email.received events)
    - Fetching full email content from Resend API (webhooks only include metadata)
    - Webhook signature verification using Svix
    """

    def __init__(self, api_key: str, webhook_secret: str = "") -> None:
        """Initialize Resend adapter.

        Args:
            api_key: Resend API key (starts with 're_')
            webhook_secret: Webhook signing secret for signature verification
        """
        self._api_key = api_key
        self._webhook_secret = webhook_secret
        self._api_url = RESEND_API_URL

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
        """Send email via Resend API.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body in Markdown/plain text format
            from_address: Sender email address
            reply_to: Optional reply-to address
            headers: Optional custom headers
            message_id: Optional custom Message-ID
            in_reply_to: Optional In-Reply-To header for threading
            references: Optional References header for threading
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            attachments: Optional list of attachments
            html_body: Optional pre-rendered HTML body

        Returns:
            Resend email ID
        """
        url = f"{self._api_url}/emails"

        # Convert Markdown body to HTML if html_body not provided
        html_content = html_body or markdown.markdown(body)

        # Build request payload
        # See: https://resend.com/docs/api-reference/emails/send-email
        data: dict[str, Any] = {
            "from": from_address,
            "to": to,
            "subject": subject,
            "text": body,
            "html": html_content,
        }

        if reply_to:
            data["reply_to"] = [reply_to]

        if cc:
            data["cc"] = cc

        if bcc:
            data["bcc"] = bcc

        # Build custom headers
        custom_headers: dict[str, str] = {}
        if headers:
            custom_headers.update(headers)

        if message_id:
            custom_headers["Message-ID"] = message_id

        if in_reply_to:
            custom_headers["In-Reply-To"] = in_reply_to

        if references:
            custom_headers["References"] = " ".join(references)

        if custom_headers:
            data["headers"] = custom_headers

        # Process attachments
        if attachments:
            attachment_list: list[dict[str, Any]] = []
            for att in attachments:
                # SendAttachment.content is already base64-encoded
                if att.content is None:
                    continue
                attachment_data: dict[str, Any] = {
                    "filename": att.filename,
                    "content": att.content,
                }
                if att.content_type:
                    attachment_data["content_type"] = att.content_type
                attachment_list.append(attachment_data)
            data["attachments"] = attachment_list

        logger.debug("Sending email via Resend to %s", to)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=data,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )

            if response.status_code not in (200, 201):
                logger.error(
                    "Resend API error: %s - %s",
                    response.status_code,
                    response.text,
                )
                response.raise_for_status()

            result = response.json()
            email_id: str = result.get("id", "")
            logger.info("Email sent via Resend: %s", email_id)
            return email_id

    def verify_webhook_signature(
        self,
        payload: str | bytes,
        headers: dict[str, str],
    ) -> dict[str, Any]:
        """Verify Resend webhook signature using Svix.

        Args:
            payload: Raw request body (must be the exact bytes/string received)
            headers: Request headers containing svix-id, svix-timestamp, svix-signature

        Returns:
            Parsed and verified webhook payload

        Raises:
            ResendWebhookError: If verification fails or secret not configured
        """
        if not self._webhook_secret:
            raise ResendWebhookError("Webhook secret not configured")

        # Normalize payload to string
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")

        # Extract Svix headers (case-insensitive)
        svix_headers: dict[str, str] = {}
        for key, value in headers.items():
            lower_key = key.lower()
            if lower_key in ("svix-id", "svix-timestamp", "svix-signature"):
                svix_headers[lower_key] = value

        if not all(k in svix_headers for k in ("svix-id", "svix-timestamp", "svix-signature")):
            raise ResendWebhookError("Missing required Svix headers")

        try:
            wh = Webhook(self._webhook_secret)
            verified_payload: dict[str, Any] = wh.verify(payload, svix_headers)
            return verified_payload
        except WebhookVerificationError as e:
            logger.warning("Webhook signature verification failed: %s", e)
            raise ResendWebhookError(f"Signature verification failed: {e}") from e

    async def fetch_email_content(self, email_id: str) -> dict[str, Any]:
        """Fetch full email content from Resend API.

        Resend webhooks only include metadata (no body/attachments).
        Use this method to fetch the complete email content.

        Args:
            email_id: Resend email ID from webhook

        Returns:
            Full email data including html, text, headers, attachments

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        url = f"{self._api_url}/emails/receiving/{email_id}"

        logger.debug("Fetching email content from Resend: %s", email_id)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                },
                timeout=30.0,
            )

            if response.status_code != 200:
                logger.error(
                    "Resend API error fetching email %s: %s - %s",
                    email_id,
                    response.status_code,
                    response.text,
                )
                response.raise_for_status()

            result: dict[str, Any] = response.json()
            return result

    async def fetch_attachment_content(self, email_id: str, attachment_id: str) -> bytes:
        """Fetch attachment content from Resend API.

        Args:
            email_id: Resend email ID
            attachment_id: Attachment ID from webhook/email data

        Returns:
            Attachment binary content
        """
        url = f"{self._api_url}/emails/receiving/{email_id}/attachments/{attachment_id}"

        logger.debug("Fetching attachment %s from email %s", attachment_id, email_id)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                },
                timeout=60.0,
            )

            if response.status_code != 200:
                logger.error(
                    "Resend API error fetching attachment: %s - %s",
                    response.status_code,
                    response.text,
                )
                response.raise_for_status()

            return response.content

    def parse_inbound_webhook(self, payload: dict[str, Any]) -> InboundMessage:
        """Parse Resend inbound webhook payload into standardized InboundMessage.

        Note: This parses the webhook metadata. For full email content (body, attachments),
        use fetch_email_content() with the email_id from the webhook data.

        Resend webhook payload structure for email.received:
        {
            "type": "email.received",
            "created_at": "2024-02-22T23:41:12.126Z",
            "data": {
                "email_id": "...",
                "created_at": "...",
                "from": "Name <email@example.com>",
                "to": ["recipient@example.com"],
                "cc": [],
                "bcc": [],
                "message_id": "<...>",
                "subject": "...",
                "attachments": [{"id": "...", "filename": "...", "content_type": "..."}]
            }
        }

        Args:
            payload: Webhook payload (can be full webhook or just data object)

        Returns:
            InboundMessage with parsed metadata (body fields will be empty)
        """
        # Handle both full webhook payload and just the data object
        if "type" in payload and "data" in payload:
            data = payload["data"]
            webhook_timestamp = payload.get("created_at")
        else:
            data = payload
            webhook_timestamp = data.get("created_at")

        # Parse sender - extract email from "Name <email>" format
        from_field = data.get("from", "")
        from_address = from_field
        if "<" in from_field and ">" in from_field:
            from_address = from_field.split("<")[1].split(">")[0]

        # Parse recipients
        to_list = data.get("to", [])
        to_address = to_list[0] if to_list else ""

        # Parse CC/BCC
        cc_addresses = data.get("cc", []) or []
        bcc_addresses = data.get("bcc", []) or []

        # Parse timestamp
        timestamp = datetime.now(UTC)
        if webhook_timestamp:
            try:
                # Handle ISO 8601 format
                timestamp_str = webhook_timestamp.replace("Z", "+00:00")
                timestamp = datetime.fromisoformat(timestamp_str)
            except (ValueError, AttributeError):
                pass

        # Parse attachments metadata (content must be fetched separately)
        attachments_meta: list[InboundAttachment] = []
        for att in data.get("attachments", []) or []:
            disposition = AttachmentDisposition.ATTACHMENT
            if att.get("content_disposition") == "inline":
                disposition = AttachmentDisposition.INLINE

            attachments_meta.append(
                InboundAttachment(
                    filename=att.get("filename", "unknown"),
                    content_type=att.get("content_type", "application/octet-stream"),
                    content=b"",  # Content must be fetched via API
                    size_bytes=0,  # Size not provided in webhook
                    disposition=disposition,
                    content_id=att.get("content_id"),
                    provider_id=att.get("id"),
                )
            )

        # Build content_id_map for inline attachments
        content_id_map: dict[str, str] = {}
        for att in attachments_meta:
            if att.content_id and att.provider_id:
                content_id_map[att.content_id] = att.provider_id

        return InboundMessage(
            from_address=from_address,
            to_address=to_address,
            subject=data.get("subject", ""),
            # Body content not included in webhook - must fetch via API
            body_plain=data.get("text", ""),
            body_html=data.get("html"),
            stripped_text=None,
            stripped_html=None,
            # Threading headers
            message_id=data.get("message_id"),
            in_reply_to=None,  # Not provided in webhook
            references=[],  # Not provided in webhook
            # Metadata
            headers=data.get("headers", {}),
            timestamp=timestamp,
            # Attachments (metadata only)
            attachments=attachments_meta,
            content_id_map=content_id_map,
            # Verification (not provided by Resend)
            spf_result=None,
            dkim_result=None,
            dmarc_result=None,
            # CC/BCC
            cc_addresses=cc_addresses,
            bcc_addresses=bcc_addresses,
        )

    async def parse_inbound_webhook_with_content(
        self,
        payload: dict[str, Any],
        *,
        fetch_attachments: bool = True,
    ) -> InboundMessage:
        """Parse webhook and fetch full email content from Resend API.

        This is the recommended method for processing email.received webhooks
        as it fetches the complete email body and attachment content.

        Args:
            payload: Webhook payload
            fetch_attachments: Whether to fetch attachment content (default True)

        Returns:
            InboundMessage with full content
        """
        # First parse the webhook metadata
        inbound = self.parse_inbound_webhook(payload)

        # Get email_id from payload
        data = payload.get("data", payload)
        email_id = data.get("email_id")

        if not email_id:
            logger.warning("No email_id in webhook, returning metadata only")
            return inbound

        # Fetch full email content
        try:
            full_email = await self.fetch_email_content(email_id)

            # Update body content
            inbound.body_plain = full_email.get("text") or ""
            inbound.body_html = full_email.get("html")

            # Update headers
            if full_email.get("headers"):
                inbound.headers = full_email["headers"]

            # Parse In-Reply-To and References from headers
            headers = full_email.get("headers", {})
            if "in-reply-to" in headers:
                inbound.in_reply_to = headers["in-reply-to"]
            if "references" in headers:
                inbound.references = inbound.parse_references_string(headers["references"])

            # Fetch attachment content if requested
            if fetch_attachments and inbound.attachments:
                for att in inbound.attachments:
                    if att.provider_id:
                        try:
                            content = await self.fetch_attachment_content(email_id, att.provider_id)
                            att.content = content
                            att.size_bytes = len(content)
                        except httpx.HTTPStatusError as e:
                            logger.warning(
                                "Failed to fetch attachment %s: %s",
                                att.provider_id,
                                e,
                            )

        except httpx.HTTPStatusError as e:
            # Log specific error details for common issues
            if e.response.status_code == 401:
                logger.error(
                    "Failed to fetch email content: API key lacks permission. "
                    "Ensure your Resend API key has 'Full access' permission, not 'Sending access' only. "
                    "Create a new key at https://resend.com/api-keys"
                )
            elif e.response.status_code == 404:
                logger.error(
                    "Failed to fetch email content: Email %s not found in Resend. "
                    "The email may have been deleted or the ID is incorrect.",
                    email_id,
                )
            else:
                logger.error("Failed to fetch email content: %s", e)
            # Re-raise the error so the webhook handler knows the fetch failed
            raise

        return inbound

    @staticmethod
    def get_event_type(payload: dict[str, Any]) -> str:
        """Extract event type from webhook payload.

        Args:
            payload: Webhook payload

        Returns:
            Event type string (e.g., 'email.received', 'email.bounced')
        """
        event_type: str = payload.get("type", "unknown")
        return event_type

    @staticmethod
    def is_inbound_event(payload: dict[str, Any]) -> bool:
        """Check if webhook is an inbound email event.

        Args:
            payload: Webhook payload

        Returns:
            True if this is an email.received event
        """
        return payload.get("type") == "email.received"
