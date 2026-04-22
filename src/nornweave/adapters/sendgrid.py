"""SendGrid email provider adapter."""

import base64
import contextlib
import json
import logging
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import httpx
import markdown  # type: ignore[import-untyped]
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from nornweave.core.interfaces import (
    EmailProvider,
    InboundAttachment,
    InboundMessage,
)
from nornweave.models.attachment import AttachmentDisposition

if TYPE_CHECKING:
    from nornweave.models.attachment import SendAttachment

logger = logging.getLogger(__name__)

# SendGrid API base URL
SENDGRID_API_URL = "https://api.sendgrid.com"

# Webhook signature headers
SIGNATURE_HEADER = "X-Twilio-Email-Event-Webhook-Signature"
TIMESTAMP_HEADER = "X-Twilio-Email-Event-Webhook-Timestamp"

# Timestamp tolerance for webhook verification (5 minutes)
TIMESTAMP_TOLERANCE_SECONDS = 300


class SendGridWebhookError(Exception):
    """Raised when webhook verification or parsing fails."""

    pass


class SendGridAdapter(EmailProvider):
    """SendGrid implementation of EmailProvider.

    Supports:
    - Sending emails via SendGrid v3 Mail Send API
    - Parsing inbound webhook payloads (Inbound Parse)
    - Webhook signature verification using ECDSA
    """

    def __init__(self, api_key: str, webhook_public_key: str = "") -> None:
        """Initialize SendGrid adapter.

        Args:
            api_key: SendGrid API key (starts with 'SG.')
            webhook_public_key: ECDSA public key for webhook signature verification
                               (base64-encoded, from SendGrid security policy)
        """
        self._api_key = api_key
        self._webhook_public_key = webhook_public_key
        self._api_url = SENDGRID_API_URL

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
        """Send email via SendGrid v3 Mail Send API.

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
            SendGrid message ID from X-Message-Id header
        """
        url = f"{self._api_url}/v3/mail/send"

        # Convert Markdown body to HTML if html_body not provided
        html_content = html_body or markdown.markdown(body)

        # Build personalizations array with recipients
        personalizations: dict[str, Any] = {
            "to": [{"email": email} for email in to],
        }

        if cc:
            personalizations["cc"] = [{"email": email} for email in cc]

        if bcc:
            personalizations["bcc"] = [{"email": email} for email in bcc]

        # Build content array
        content = [
            {"type": "text/plain", "value": body},
            {"type": "text/html", "value": html_content},
        ]

        # Build request payload
        data: dict[str, Any] = {
            "personalizations": [personalizations],
            "from": {"email": from_address},
            "subject": subject,
            "content": content,
        }

        # Add reply_to
        if reply_to:
            data["reply_to"] = {"email": reply_to}

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
                # SendAttachment.content is already base64-encoded string
                # If raw bytes are provided via get_content_bytes(), encode them
                content_bytes = att.get_content_bytes()
                if content_bytes:
                    content_b64 = base64.b64encode(content_bytes).decode("utf-8")
                elif att.content:
                    content_b64 = att.content  # Already base64 string
                else:
                    continue  # Skip attachments without content

                attachment_data: dict[str, Any] = {
                    "content": content_b64,
                    "filename": att.filename,
                }
                if att.content_type:
                    attachment_data["type"] = att.content_type

                # Handle disposition (inline vs attachment)
                if hasattr(att, "disposition") and att.disposition:
                    attachment_data["disposition"] = att.disposition.value
                    if att.disposition == AttachmentDisposition.INLINE and hasattr(
                        att, "content_id"
                    ):
                        attachment_data["content_id"] = att.content_id

                attachment_list.append(attachment_data)
            data["attachments"] = attachment_list

        logger.debug("Sending email via SendGrid to %s", to)

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

            if response.status_code not in (200, 201, 202):
                logger.error(
                    "SendGrid API error: %s - %s",
                    response.status_code,
                    response.text,
                )
                response.raise_for_status()

            # Extract message ID from X-Message-Id header
            message_id_header: str = response.headers.get("X-Message-Id", "")
            logger.info("Email sent via SendGrid: %s", message_id_header)
            return message_id_header

    def parse_inbound_webhook(self, payload: dict[str, Any]) -> InboundMessage:
        """Parse SendGrid Inbound Parse webhook payload into standardized InboundMessage.

        SendGrid Inbound Parse sends data as multipart/form-data with fields:
        - from, to, subject, text, html
        - headers (newline-separated string)
        - envelope (JSON string)
        - charsets (JSON string)
        - SPF, dkim, spam_score
        - attachments (count)
        - attachment-info (JSON with attachment metadata)
        - content-ids (JSON mapping Content-ID to attachment field name)

        Args:
            payload: Parsed form data from webhook (dict of field values)

        Returns:
            InboundMessage with parsed email data
        """
        # Parse sender - extract email from "Name <email>" format
        from_field = payload.get("from", "")
        from_address = from_field
        if "<" in from_field and ">" in from_field:
            from_address = from_field.split("<")[1].split(">")[0]

        # Parse recipient
        to_address = payload.get("to", "")

        # Parse headers string into dictionary
        headers: dict[str, str] = {}
        headers_raw = payload.get("headers", "")
        if headers_raw:
            headers = self._parse_headers_string(headers_raw)

        # Extract threading headers from parsed headers
        message_id = headers.get("Message-ID") or headers.get("Message-Id")
        in_reply_to = headers.get("In-Reply-To")
        references_str = headers.get("References", "")
        references = [ref.strip() for ref in references_str.split() if ref.strip()]

        # Parse timestamp from headers or use current time
        timestamp = datetime.now(UTC)
        date_header = headers.get("Date")
        if date_header:
            try:
                from email.utils import parsedate_to_datetime

                timestamp = parsedate_to_datetime(date_header)
            except (ValueError, TypeError):
                pass

        # Parse attachments from attachment-info JSON
        attachments_meta: list[InboundAttachment] = []
        content_id_map: dict[str, str] = {}

        attachment_info_raw = payload.get("attachment-info", "")
        content_ids_raw = payload.get("content-ids", "")

        # Parse content-ids mapping (Content-ID -> attachment field name)
        content_ids_mapping: dict[str, str] = {}
        if content_ids_raw:
            with contextlib.suppress(json.JSONDecodeError):
                content_ids_mapping = json.loads(content_ids_raw)

        # Reverse mapping: attachment field name -> Content-ID
        field_to_content_id = {v: k for k, v in content_ids_mapping.items()}

        if attachment_info_raw:
            try:
                attachment_info = json.loads(attachment_info_raw)
                for field_name, att_data in attachment_info.items():
                    # Determine disposition
                    content_id = field_to_content_id.get(field_name)
                    disposition = AttachmentDisposition.ATTACHMENT
                    if content_id:
                        disposition = AttachmentDisposition.INLINE

                    attachments_meta.append(
                        InboundAttachment(
                            filename=att_data.get("filename") or att_data.get("name", "unknown"),
                            content_type=att_data.get("type", "application/octet-stream"),
                            content=b"",  # Content comes as separate form fields
                            size_bytes=0,
                            disposition=disposition,
                            content_id=content_id,
                            provider_id=field_name,
                        )
                    )

                    # Build content_id_map for inline images
                    if content_id:
                        content_id_map[content_id] = field_name

            except json.JSONDecodeError:
                logger.warning("Failed to parse attachment-info JSON")

        # Parse CC from headers
        cc_header = headers.get("Cc", "")
        cc_addresses = (
            [addr.strip() for addr in cc_header.split(",") if addr.strip()] if cc_header else []
        )

        # Parse SPF and DKIM results
        spf_result = payload.get("SPF")
        dkim_result = payload.get("dkim")

        return InboundMessage(
            from_address=from_address,
            to_address=to_address,
            subject=payload.get("subject", ""),
            body_plain=payload.get("text", ""),
            body_html=payload.get("html"),
            stripped_text=payload.get("stripped-text"),
            stripped_html=payload.get("stripped-html"),
            message_id=message_id,
            in_reply_to=in_reply_to,
            references=references,
            headers=headers,
            timestamp=timestamp,
            attachments=attachments_meta,
            content_id_map=content_id_map,
            spf_result=spf_result,
            dkim_result=dkim_result,
            dmarc_result=None,  # Not provided by SendGrid Inbound Parse
            cc_addresses=cc_addresses,
            bcc_addresses=[],  # BCC not visible in received emails
        )

    def _parse_headers_string(self, headers_raw: str) -> dict[str, str]:
        """Parse newline-separated headers string into dictionary.

        Args:
            headers_raw: Raw headers string from SendGrid webhook

        Returns:
            Dictionary of header name -> value
        """
        headers: dict[str, str] = {}
        current_header = ""
        current_value = ""

        for line in headers_raw.split("\n"):
            if not line:
                continue

            # Check if this is a continuation line (starts with whitespace)
            if line[0] in (" ", "\t"):
                current_value += " " + line.strip()
            else:
                # Save previous header if exists
                if current_header:
                    headers[current_header] = current_value

                # Parse new header
                if ":" in line:
                    parts = line.split(":", 1)
                    current_header = parts[0].strip()
                    current_value = parts[1].strip() if len(parts) > 1 else ""
                else:
                    current_header = ""
                    current_value = ""

        # Save last header
        if current_header:
            headers[current_header] = current_value

        return headers

    def verify_webhook_signature(
        self,
        payload: bytes,
        headers: dict[str, str],
    ) -> None:
        """Verify SendGrid Inbound Parse webhook signature using ECDSA.

        Args:
            payload: Raw request body (must be exact bytes received)
            headers: Request headers containing signature and timestamp

        Raises:
            SendGridWebhookError: If verification fails or public key not configured
        """
        if not self._webhook_public_key:
            raise SendGridWebhookError("Webhook public key not configured")

        # Extract signature headers (case-insensitive)
        signature = None
        timestamp = None
        for key, value in headers.items():
            lower_key = key.lower()
            if lower_key == SIGNATURE_HEADER.lower():
                signature = value
            elif lower_key == TIMESTAMP_HEADER.lower():
                timestamp = value

        if not signature:
            raise SendGridWebhookError(f"Missing required header: {SIGNATURE_HEADER}")

        if not timestamp:
            raise SendGridWebhookError(f"Missing required header: {TIMESTAMP_HEADER}")

        # Validate timestamp is within tolerance
        try:
            timestamp_int = int(timestamp)
            current_time = int(time.time())
            if abs(current_time - timestamp_int) > TIMESTAMP_TOLERANCE_SECONDS:
                raise SendGridWebhookError(
                    f"Timestamp validation failed: timestamp {timestamp} is outside "
                    f"acceptable tolerance of {TIMESTAMP_TOLERANCE_SECONDS} seconds"
                )
        except ValueError:
            raise SendGridWebhookError(f"Invalid timestamp format: {timestamp}")

        # Build signed payload: timestamp + payload
        signed_payload = timestamp.encode("utf-8") + payload

        # Decode signature from base64
        try:
            signature_bytes = base64.b64decode(signature)
        except Exception as e:
            raise SendGridWebhookError(f"Invalid signature encoding: {e}")

        # Load public key
        try:
            # The public key from SendGrid is base64-encoded DER format
            public_key_bytes = base64.b64decode(self._webhook_public_key)

            # Try loading as raw public key bytes (EC point)
            # SendGrid provides the key in SubjectPublicKeyInfo DER format
            from cryptography.hazmat.primitives.serialization import load_der_public_key

            public_key = load_der_public_key(public_key_bytes)
        except Exception as e:
            raise SendGridWebhookError(f"Invalid public key: {e}")

        # Verify signature
        try:
            if not isinstance(public_key, ec.EllipticCurvePublicKey):
                raise SendGridWebhookError("Public key is not an ECDSA key")

            public_key.verify(
                signature_bytes,
                signed_payload,
                ec.ECDSA(hashes.SHA256()),
            )
        except InvalidSignature:
            raise SendGridWebhookError("Signature verification failed")
        except Exception as e:
            raise SendGridWebhookError(f"Signature verification error: {e}")

    @staticmethod
    def get_event_type(payload: dict[str, Any]) -> str:  # noqa: ARG004
        """Get event type for Inbound Parse webhook.

        SendGrid Inbound Parse doesn't have event types like Event Webhooks.
        All Inbound Parse webhooks are inbound email events.

        Args:
            payload: Webhook payload

        Returns:
            Event type string ("inbound")
        """
        return "inbound"

    @staticmethod
    def is_inbound_event(payload: dict[str, Any]) -> bool:
        """Check if webhook is an inbound email event.

        For SendGrid Inbound Parse, this always returns True as all
        webhooks to the Inbound Parse endpoint are inbound emails.

        Args:
            payload: Webhook payload

        Returns:
            True (Inbound Parse webhooks are always inbound events)
        """
        # Check for typical Inbound Parse fields to verify it's a valid payload
        return "from" in payload or "to" in payload or "subject" in payload
