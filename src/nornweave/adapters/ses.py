"""AWS SES email provider adapter."""

import base64
import hashlib
import hmac
import json
import logging
import re
import urllib.request
from datetime import UTC, datetime
from email import message_from_bytes
from email.utils import parsedate_to_datetime
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import httpx
import markdown
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from nornweave.core.interfaces import (
    EmailProvider,
    InboundAttachment,
    InboundMessage,
)
from nornweave.models.attachment import AttachmentDisposition

if TYPE_CHECKING:
    from nornweave.models.attachment import SendAttachment

logger = logging.getLogger(__name__)

# SES API service name for signing
SES_SERVICE = "ses"

# SNS message types
SNS_TYPE_NOTIFICATION = "Notification"
SNS_TYPE_SUBSCRIPTION_CONFIRMATION = "SubscriptionConfirmation"
SNS_TYPE_UNSUBSCRIBE_CONFIRMATION = "UnsubscribeConfirmation"

# SNS SigningCertURL validation pattern
SNS_CERT_URL_PATTERN = re.compile(
    r"^https://sns\.[a-z0-9-]+\.amazonaws\.com(\.cn)?/"
)


class SESWebhookError(Exception):
    """Raised when webhook verification or parsing fails."""


class SESAdapter(EmailProvider):
    """AWS SES implementation of EmailProvider.

    Supports:
    - Sending emails via SES v2 API with Content.Simple
    - Parsing inbound webhooks via SNS notifications
    - SNS signature verification using X.509 certificates
    - Automatic SNS subscription confirmation
    """

    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        region: str = "us-east-1",
        configuration_set: str | None = None,
    ) -> None:
        """Initialize AWS SES adapter.

        Args:
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key
            region: AWS region (default: us-east-1)
            configuration_set: Optional SES configuration set name for tracking
        """
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._region = region
        self._configuration_set = configuration_set
        self._api_host = f"email.{region}.amazonaws.com"
        self._api_url = f"https://{self._api_host}"

    # -------------------------------------------------------------------------
    # AWS Signature Version 4 Implementation
    # -------------------------------------------------------------------------

    def _sign(self, key: bytes, msg: str) -> bytes:
        """HMAC-SHA256 sign a message."""
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def _get_signature_key(
        self, date_stamp: str, region: str, service: str
    ) -> bytes:
        """Derive the signing key for AWS SigV4."""
        k_date = self._sign(f"AWS4{self._secret_access_key}".encode("utf-8"), date_stamp)
        k_region = self._sign(k_date, region)
        k_service = self._sign(k_region, service)
        k_signing = self._sign(k_service, "aws4_request")
        return k_signing

    def _sign_request(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        payload: bytes,
    ) -> dict[str, str]:
        """Sign an HTTP request using AWS Signature Version 4.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path (e.g., /v2/email/outbound-emails)
            headers: Request headers (will be modified with auth headers)
            payload: Request body bytes

        Returns:
            Headers dict with Authorization and X-Amz-Date added
        """
        # Get current time
        t = datetime.now(UTC)
        amz_date = t.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = t.strftime("%Y%m%d")

        # Add required headers
        headers = dict(headers)
        headers["Host"] = self._api_host
        headers["X-Amz-Date"] = amz_date

        # Create canonical request
        canonical_uri = path
        canonical_querystring = ""

        # Create signed headers list
        signed_headers_list = sorted(headers.keys(), key=str.lower)
        signed_headers = ";".join(h.lower() for h in signed_headers_list)

        # Create canonical headers
        canonical_headers = ""
        for header in signed_headers_list:
            canonical_headers += f"{header.lower()}:{headers[header].strip()}\n"

        # Hash the payload
        payload_hash = hashlib.sha256(payload).hexdigest()

        # Create canonical request
        canonical_request = "\n".join([
            method,
            canonical_uri,
            canonical_querystring,
            canonical_headers,
            signed_headers,
            payload_hash,
        ])

        # Create string to sign
        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{self._region}/{SES_SERVICE}/aws4_request"
        string_to_sign = "\n".join([
            algorithm,
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ])

        # Calculate signature
        signing_key = self._get_signature_key(date_stamp, self._region, SES_SERVICE)
        signature = hmac.new(
            signing_key, string_to_sign.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        # Create authorization header
        authorization_header = (
            f"{algorithm} "
            f"Credential={self._access_key_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )

        headers["Authorization"] = authorization_header
        return headers

    # -------------------------------------------------------------------------
    # Send Email Implementation
    # -------------------------------------------------------------------------

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
        """Send email via AWS SES v2 API.

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
            SES message ID from response
        """
        path = "/v2/email/outbound-emails"

        # Convert Markdown body to HTML if html_body not provided
        html_content = html_body or markdown.markdown(body)

        # Build destination object
        destination: dict[str, Any] = {
            "ToAddresses": to,
        }
        if cc:
            destination["CcAddresses"] = cc
        if bcc:
            destination["BccAddresses"] = bcc

        # Build body object
        body_obj: dict[str, Any] = {
            "Text": {"Data": body, "Charset": "UTF-8"},
            "Html": {"Data": html_content, "Charset": "UTF-8"},
        }

        # Build headers array for threading
        headers_array: list[dict[str, str]] = []
        if message_id:
            headers_array.append({"Name": "Message-ID", "Value": message_id})
        if in_reply_to:
            headers_array.append({"Name": "In-Reply-To", "Value": in_reply_to})
        if references:
            headers_array.append({"Name": "References", "Value": " ".join(references)})

        # Add custom headers
        if headers:
            for name, value in headers.items():
                headers_array.append({"Name": name, "Value": value})

        # Build simple content
        simple_content: dict[str, Any] = {
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": body_obj,
        }

        if headers_array:
            simple_content["Headers"] = headers_array

        # Build attachments array
        if attachments:
            attachments_array: list[dict[str, Any]] = []
            for att in attachments:
                # Get content bytes
                content_bytes = att.get_content_bytes()
                if content_bytes:
                    content_b64 = base64.b64encode(content_bytes).decode("utf-8")
                elif att.content:
                    content_b64 = att.content  # Already base64 string
                else:
                    continue  # Skip attachments without content

                attachment_data: dict[str, Any] = {
                    "RawContent": content_b64,
                    "FileName": att.filename,
                }

                if att.content_type:
                    attachment_data["ContentType"] = att.content_type

                # Handle disposition
                if hasattr(att, "disposition") and att.disposition:
                    if att.disposition == AttachmentDisposition.INLINE:
                        attachment_data["ContentDisposition"] = "inline"
                        if hasattr(att, "content_id") and att.content_id:
                            attachment_data["ContentId"] = att.content_id
                    else:
                        attachment_data["ContentDisposition"] = "attachment"

                attachments_array.append(attachment_data)

            if attachments_array:
                simple_content["Attachments"] = attachments_array

        # Build request payload
        data: dict[str, Any] = {
            "FromEmailAddress": from_address,
            "Destination": destination,
            "Content": {"Simple": simple_content},
        }

        if reply_to:
            data["ReplyToAddresses"] = [reply_to]

        if self._configuration_set:
            data["ConfigurationSetName"] = self._configuration_set

        # Serialize payload
        payload = json.dumps(data).encode("utf-8")

        # Sign request
        request_headers = {
            "Content-Type": "application/json",
        }
        signed_headers = self._sign_request("POST", path, request_headers, payload)

        logger.debug("Sending email via SES to %s", to)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._api_url}{path}",
                content=payload,
                headers=signed_headers,
                timeout=30.0,
            )

            if response.status_code not in (200, 201, 202):
                logger.error(
                    "SES API error: %s - %s",
                    response.status_code,
                    response.text,
                )
                response.raise_for_status()

            # Extract message ID from response
            result = response.json()
            ses_message_id: str = result.get("MessageId", "")
            logger.info("Email sent via SES: %s", ses_message_id)
            return ses_message_id

    # -------------------------------------------------------------------------
    # SNS Webhook Infrastructure
    # -------------------------------------------------------------------------

    @staticmethod
    def get_sns_message_type(payload: dict[str, Any]) -> str | None:
        """Get the SNS message type from payload.

        Args:
            payload: SNS notification payload

        Returns:
            Message type string or None if not an SNS message
        """
        return payload.get("Type")

    @staticmethod
    def is_inbound_event(payload: dict[str, Any]) -> bool:
        """Check if webhook is an inbound email event.

        Args:
            payload: Webhook payload (SNS notification)

        Returns:
            True if this is an inbound email notification
        """
        # Must be a Notification type
        if payload.get("Type") != SNS_TYPE_NOTIFICATION:
            return False

        # Parse the Message field to check notificationType
        message_str = payload.get("Message", "")
        if not message_str:
            return False

        try:
            message = json.loads(message_str)
            notification_type = message.get("notificationType")
            return notification_type == "Received"
        except json.JSONDecodeError:
            return False

    @staticmethod
    def get_event_type(payload: dict[str, Any]) -> str:
        """Get event type from SES notification.

        Args:
            payload: Webhook payload (SNS notification with SES data)

        Returns:
            Event type string ("inbound" for received emails)
        """
        # Parse the Message field
        message_str = payload.get("Message", "")
        if message_str:
            try:
                message = json.loads(message_str)
                notification_type: str = message.get("notificationType", "")
                if notification_type == "Received":
                    return "inbound"
                return notification_type.lower() if notification_type else "unknown"
            except json.JSONDecodeError:
                pass
        return "unknown"

    async def handle_subscription_confirmation(
        self, payload: dict[str, Any]
    ) -> bool:
        """Handle SNS subscription confirmation by fetching SubscribeURL.

        Args:
            payload: SNS SubscriptionConfirmation payload

        Returns:
            True if subscription was confirmed successfully
        """
        subscribe_url = payload.get("SubscribeURL")
        if not subscribe_url:
            logger.warning("SubscriptionConfirmation missing SubscribeURL")
            return False

        logger.info("Confirming SNS subscription: %s", payload.get("TopicArn"))

        async with httpx.AsyncClient() as client:
            response = await client.get(subscribe_url, timeout=30.0)
            if response.status_code == 200:
                logger.info("SNS subscription confirmed successfully")
                return True
            else:
                logger.error(
                    "Failed to confirm SNS subscription: %s",
                    response.status_code,
                )
                return False

    # -------------------------------------------------------------------------
    # SNS Signature Verification
    # -------------------------------------------------------------------------

    def _validate_signing_cert_url(self, url: str) -> bool:
        """Validate that SigningCertURL is from AWS SNS.

        Args:
            url: The SigningCertURL from SNS message

        Returns:
            True if URL is valid AWS SNS certificate URL
        """
        match = SNS_CERT_URL_PATTERN.match(url)
        return match is not None

    @staticmethod
    @lru_cache(maxsize=10)
    def _fetch_certificate_sync(url: str) -> x509.Certificate:
        """Fetch and cache SNS signing certificate (sync for caching).

        Args:
            url: Certificate URL

        Returns:
            X.509 certificate object

        Raises:
            SESWebhookError: If certificate cannot be fetched or parsed
        """
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                cert_pem = response.read()
            return x509.load_pem_x509_certificate(cert_pem)
        except Exception as e:
            raise SESWebhookError(f"Failed to fetch signing certificate: {e}") from e

    def _build_sns_string_to_sign(
        self, payload: dict[str, Any], message_type: str
    ) -> str:
        """Build the canonical string to sign for SNS message verification.

        Args:
            payload: SNS message payload
            message_type: SNS message type

        Returns:
            Canonical string to sign
        """
        # Fields to include depend on message type
        if message_type == SNS_TYPE_NOTIFICATION:
            fields = ["Message", "MessageId", "Subject", "Timestamp", "TopicArn", "Type"]
        else:
            # SubscriptionConfirmation and UnsubscribeConfirmation
            fields = [
                "Message",
                "MessageId",
                "SubscribeURL",
                "Timestamp",
                "Token",
                "TopicArn",
                "Type",
            ]

        # Build string to sign
        parts = []
        for field in fields:
            if field in payload:
                parts.append(field)
                parts.append(str(payload[field]))

        return "\n".join(parts) + "\n"

    def verify_webhook_signature(self, payload: dict[str, Any]) -> None:
        """Verify SNS message signature using X.509 certificate.

        Args:
            payload: SNS message payload with Signature and SigningCertURL

        Raises:
            SESWebhookError: If verification fails
        """
        # Get required fields
        signature_b64 = payload.get("Signature")
        signing_cert_url = payload.get("SigningCertURL")
        message_type = payload.get("Type")

        if not signature_b64:
            raise SESWebhookError("Missing Signature field")
        if not signing_cert_url:
            raise SESWebhookError("Missing SigningCertURL field")
        if not message_type:
            raise SESWebhookError("Missing Type field")

        # Validate SigningCertURL is from AWS
        if not self._validate_signing_cert_url(signing_cert_url):
            raise SESWebhookError(
                "Invalid SigningCertURL: must be from sns.*.amazonaws.com"
            )

        # Fetch certificate (cached)
        cert = self._fetch_certificate_sync(signing_cert_url)

        # Build string to sign
        string_to_sign = self._build_sns_string_to_sign(payload, message_type)

        # Decode signature
        try:
            signature = base64.b64decode(signature_b64)
        except ValueError as e:
            raise SESWebhookError(f"Invalid signature encoding: {e}") from e

        # Verify signature
        try:
            public_key = cert.public_key()
            # SNS uses RSA with PKCS1v15 padding and SHA1
            from cryptography.hazmat.primitives.asymmetric import rsa
            if isinstance(public_key, rsa.RSAPublicKey):
                public_key.verify(
                    signature,
                    string_to_sign.encode("utf-8"),
                    padding.PKCS1v15(),
                    hashes.SHA1(),  # SNS uses SHA1
                )
            else:
                raise SESWebhookError("Certificate does not contain RSA public key")
        except SESWebhookError:
            raise
        except Exception as e:
            raise SESWebhookError(f"Signature verification failed: {e}") from e

    # -------------------------------------------------------------------------
    # Inbound Email Parsing
    # -------------------------------------------------------------------------

    def _parse_mime_content(
        self, content: str | bytes
    ) -> tuple[str, str | None, list[InboundAttachment], dict[str, str]]:
        """Parse MIME content to extract body and attachments.

        Args:
            content: Raw MIME email content

        Returns:
            Tuple of (body_plain, body_html, attachments, content_id_map)
        """
        # Parse MIME message
        if isinstance(content, str):
            # Check if it looks like base64 (no whitespace/newlines at start, all valid b64 chars)
            # Real MIME content starts with headers like "Return-Path:" or "Content-Type:"
            if content.startswith(("Return-Path:", "Content-Type:", "MIME-Version:",
                                   "From:", "To:", "Subject:", "Date:", "Message-ID:")):
                # It's plain text MIME, not base64
                content_bytes = content.encode("utf-8")
            else:
                # Try to decode if it might be base64
                try:
                    content_bytes = base64.b64decode(content)
                    # Verify it looks like valid MIME after decode
                    try:
                        content_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        # If decoded content isn't valid UTF-8 and original was,
                        # the original wasn't base64
                        content_bytes = content.encode("utf-8")
                except Exception:
                    content_bytes = content.encode("utf-8")
        else:
            content_bytes = content

        msg = message_from_bytes(content_bytes)

        body_plain = ""
        body_html: str | None = None
        attachments: list[InboundAttachment] = []
        content_id_map: dict[str, str] = {}

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Skip multipart containers
                if part.is_multipart():
                    continue

                # Get content
                try:
                    part_payload = part.get_payload(decode=True)
                    if part_payload is None or not isinstance(part_payload, bytes):
                        continue
                    part_content: bytes = part_payload
                except Exception:
                    continue

                # Handle text parts
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        body_plain = part_content.decode(charset, errors="replace")
                    except (UnicodeDecodeError, LookupError):
                        body_plain = part_content.decode("utf-8", errors="replace")

                elif content_type == "text/html" and "attachment" not in content_disposition:
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        body_html = part_content.decode(charset, errors="replace")
                    except (UnicodeDecodeError, LookupError):
                        body_html = part_content.decode("utf-8", errors="replace")

                # Handle attachments
                elif "attachment" in content_disposition or "inline" in content_disposition:
                    filename = part.get_filename() or "unnamed"
                    content_id_header = part.get("Content-ID", "")
                    content_id = str(content_id_header).strip("<>") if content_id_header else ""

                    disposition = AttachmentDisposition.ATTACHMENT
                    if "inline" in content_disposition or content_id:
                        disposition = AttachmentDisposition.INLINE

                    attachment = InboundAttachment(
                        filename=filename,
                        content_type=content_type,
                        content=part_content,
                        size_bytes=len(part_content),
                        disposition=disposition,
                        content_id=content_id if content_id else None,
                    )
                    attachments.append(attachment)

                    if content_id:
                        content_id_map[content_id] = filename

        else:
            # Simple non-multipart message
            content_type = msg.get_content_type()
            try:
                msg_payload = msg.get_payload(decode=True)
                if msg_payload is not None and isinstance(msg_payload, bytes):
                    charset = msg.get_content_charset() or "utf-8"
                    try:
                        text = msg_payload.decode(charset, errors="replace")
                    except (UnicodeDecodeError, LookupError):
                        text = msg_payload.decode("utf-8", errors="replace")
                    if content_type == "text/html":
                        body_html = text
                    else:
                        body_plain = text
            except Exception:
                pass

        return body_plain, body_html, attachments, content_id_map

    def _extract_email_from_address(self, address: str | list[str]) -> str:
        """Extract email address from various formats.

        Args:
            address: Email address (possibly with display name)

        Returns:
            Clean email address
        """
        if isinstance(address, list):
            address = address[0] if address else ""

        # Extract from "Name <email>" format
        if "<" in address and ">" in address:
            return address.split("<")[1].split(">")[0]
        return address

    def parse_inbound_webhook(self, payload: dict[str, Any]) -> InboundMessage:
        """Parse SNS notification containing SES email data.

        Args:
            payload: SNS notification payload

        Returns:
            InboundMessage with parsed email data
        """
        # Extract the SES notification from SNS Message field
        message_str = payload.get("Message", "")
        if not message_str:
            raise SESWebhookError("Missing Message field in SNS notification")

        try:
            ses_notification = json.loads(message_str)
        except json.JSONDecodeError as e:
            raise SESWebhookError(f"Invalid JSON in Message field: {e}") from e

        # Extract receipt data for verification results
        receipt = ses_notification.get("receipt", {})
        spf_result = receipt.get("spfVerdict", {}).get("status")
        dkim_result = receipt.get("dkimVerdict", {}).get("status")
        dmarc_result = receipt.get("dmarcVerdict", {}).get("status")

        # Extract mail metadata
        mail = ses_notification.get("mail", {})
        common_headers = mail.get("commonHeaders", {})

        # Parse sender
        from_list = common_headers.get("from", [])
        from_address = self._extract_email_from_address(
            from_list[0] if from_list else mail.get("source", "")
        )

        # Parse recipient
        to_list = common_headers.get("to", [])
        to_address = to_list[0] if to_list else ""
        if isinstance(to_address, str):
            to_address = self._extract_email_from_address(to_address)

        # Parse subject
        subject = common_headers.get("subject", "")

        # Parse message ID and threading headers
        message_id = common_headers.get("messageId")
        in_reply_to = common_headers.get("inReplyTo")
        references_raw = common_headers.get("references", "")
        if isinstance(references_raw, str):
            references = [ref.strip() for ref in references_raw.split() if ref.strip()]
        elif isinstance(references_raw, list):
            references = references_raw
        else:
            references = []

        # Parse headers into dictionary
        headers_list = mail.get("headers", [])
        headers: dict[str, str] = {}
        for header in headers_list:
            name = header.get("name", "")
            value = header.get("value", "")
            if name:
                headers[name] = value

        # Parse timestamp
        timestamp = datetime.now(UTC)
        date_str = common_headers.get("date")
        if date_str:
            try:
                timestamp = parsedate_to_datetime(date_str)
            except (ValueError, TypeError):
                pass

        # Parse CC addresses
        cc_list = common_headers.get("cc", [])
        cc_addresses = [self._extract_email_from_address(addr) for addr in cc_list]

        # Parse raw MIME content for body and attachments
        content = ses_notification.get("content", "")
        body_plain = ""
        body_html: str | None = None
        attachments: list[InboundAttachment] = []
        content_id_map: dict[str, str] = {}

        if content:
            body_plain, body_html, attachments, content_id_map = self._parse_mime_content(
                content
            )

        return InboundMessage(
            from_address=from_address,
            to_address=to_address,
            subject=subject,
            body_plain=body_plain,
            body_html=body_html,
            stripped_text=None,  # SES doesn't provide stripped versions
            stripped_html=None,
            message_id=message_id,
            in_reply_to=in_reply_to,
            references=references,
            headers=headers,
            timestamp=timestamp,
            attachments=attachments,
            content_id_map=content_id_map,
            spf_result=spf_result,
            dkim_result=dkim_result,
            dmarc_result=dmarc_result,
            cc_addresses=cc_addresses,
            bcc_addresses=[],  # BCC not visible in received emails
        )
