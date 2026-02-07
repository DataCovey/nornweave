"""RFC 822 email parser — converts raw email bytes to InboundMessage.

Uses Python's email.message.EmailMessage with email.policy.default for
proper header decoding (MIME, RFC 2047) and MIME part walking.
"""

import logging
import re
from datetime import UTC, datetime
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr, parsedate_to_datetime
from typing import TYPE_CHECKING

from nornweave.core.interfaces import InboundAttachment, InboundMessage
from nornweave.models.attachment import AttachmentDisposition

if TYPE_CHECKING:
    from email.message import EmailMessage

logger = logging.getLogger(__name__)


def parse_raw_email(raw_bytes: bytes) -> InboundMessage:
    """Parse raw RFC 822 email bytes into an InboundMessage.

    Handles:
    - Plain text and multipart/alternative (text + HTML) bodies
    - multipart/mixed with file attachments
    - Threading headers (Message-ID, In-Reply-To, References)
    - RFC 2047 encoded headers (=?UTF-8?B?...?=)
    - Authentication-Results header for SPF/DKIM/DMARC
    - Inline attachments with Content-ID
    - Malformed emails with sensible defaults

    Args:
        raw_bytes: Raw RFC 822 email content.

    Returns:
        InboundMessage with parsed fields.
    """
    parser = BytesParser(policy=policy.default)
    msg: EmailMessage = parser.parsebytes(raw_bytes)

    # -------------------------------------------------------------------------
    # Headers
    # -------------------------------------------------------------------------
    from_address = _extract_email(msg.get("From", ""))
    to_address = _extract_email(msg.get("To", ""))
    subject = str(msg.get("Subject", ""))

    # CC addresses
    cc_raw = msg.get("Cc", "")
    cc_addresses = _extract_email_list(str(cc_raw)) if cc_raw else []

    # Threading headers
    message_id = _clean_header(msg.get("Message-ID"))
    in_reply_to = _clean_header(msg.get("In-Reply-To"))
    references_raw = _clean_header(msg.get("References"))
    references = references_raw.split() if references_raw else []

    # Timestamp
    timestamp = _parse_date(msg.get("Date"))

    # All headers as dict
    headers: dict[str, str] = {}
    for key in msg:
        headers[key] = str(msg[key])

    # -------------------------------------------------------------------------
    # Body and attachments
    # -------------------------------------------------------------------------
    body_plain = ""
    body_html: str | None = None
    attachments: list[InboundAttachment] = []
    content_id_map: dict[str, str] = {}

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))

            # Skip multipart containers
            if content_type.startswith("multipart/"):
                continue

            # Attachment detection: has explicit disposition or is not text/*
            is_attachment = (
                "attachment" in disposition.lower()
                or (
                    "inline" in disposition.lower()
                    and content_type not in ("text/plain", "text/html")
                )
                or (
                    content_type not in ("text/plain", "text/html")
                    and "inline" not in disposition.lower()
                    and part.get_filename() is not None
                )
            )

            if is_attachment:
                att = _parse_attachment(part)
                if att:
                    attachments.append(att)
                    if att.content_id:
                        content_id_map[att.content_id] = att.filename
            elif content_type == "text/plain" and not body_plain:
                payload = part.get_content()
                body_plain = str(payload) if payload else ""
            elif content_type == "text/html" and body_html is None:
                payload = part.get_content()
                body_html = str(payload) if payload else None
    else:
        # Single-part message
        content_type = msg.get_content_type()
        payload = msg.get_content()
        if content_type == "text/html":
            body_html = str(payload) if payload else None
            body_plain = ""
        else:
            body_plain = str(payload) if payload else ""

    # -------------------------------------------------------------------------
    # Authentication results (SPF, DKIM, DMARC)
    # -------------------------------------------------------------------------
    spf_result, dkim_result, dmarc_result = _parse_authentication_results(
        msg.get("Authentication-Results", "")
    )

    return InboundMessage(
        from_address=from_address,
        to_address=to_address,
        subject=subject,
        body_plain=body_plain,
        body_html=body_html,
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
    )


def _extract_email(header_value: str) -> str:
    """Extract email address from a header value like 'Name <email@example.com>'."""
    if not header_value:
        return ""
    _, addr = parseaddr(str(header_value))
    return addr


def _extract_email_list(header_value: str) -> list[str]:
    """Extract multiple email addresses from a comma-separated header."""
    if not header_value:
        return []
    addresses = []
    for part in str(header_value).split(","):
        addr = _extract_email(part.strip())
        if addr:
            addresses.append(addr)
    return addresses


def _clean_header(value: str | None) -> str | None:
    """Clean a header value, stripping whitespace."""
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned if cleaned else None


def _parse_date(date_str: str | None) -> datetime:
    """Parse email Date header into datetime, with fallback to now."""
    if not date_str:
        return datetime.now(UTC)
    try:
        return parsedate_to_datetime(str(date_str))
    except ValueError, TypeError:
        logger.debug("Failed to parse date header: %s", date_str)
        return datetime.now(UTC)


def _parse_attachment(part: EmailMessage) -> InboundAttachment | None:
    """Parse a MIME part into an InboundAttachment."""
    try:
        filename = part.get_filename() or "untitled"
        content_type = part.get_content_type()
        content = part.get_content()

        # get_content() may return str for text types
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        elif isinstance(content, bytes):
            content_bytes = content
        else:
            logger.warning("Unexpected attachment content type: %s", type(content))
            return None

        # Determine disposition
        disposition_header = str(part.get("Content-Disposition", ""))
        if "inline" in disposition_header.lower():
            disposition = AttachmentDisposition.INLINE
        else:
            disposition = AttachmentDisposition.ATTACHMENT

        # Content-ID for inline images
        content_id = _clean_header(part.get("Content-ID"))
        if content_id:
            content_id = content_id.strip("<>")

        return InboundAttachment(
            filename=filename,
            content_type=content_type,
            content=content_bytes,
            size_bytes=len(content_bytes),
            disposition=disposition,
            content_id=content_id,
        )
    except Exception:
        logger.warning("Failed to parse attachment: %s", part.get_filename(), exc_info=True)
        return None


def _parse_authentication_results(header_value: str) -> tuple[str | None, str | None, str | None]:
    """Parse Authentication-Results header for SPF, DKIM, DMARC verdicts.

    Example header:
        mx.example.com; spf=pass; dkim=pass; dmarc=pass

    Returns:
        Tuple of (spf_result, dkim_result, dmarc_result), each None if not found.
    """
    if not header_value:
        return None, None, None

    value = str(header_value).lower()

    spf = _extract_auth_result(value, "spf")
    dkim = _extract_auth_result(value, "dkim")
    dmarc = _extract_auth_result(value, "dmarc")

    return spf, dkim, dmarc


def _extract_auth_result(header: str, mechanism: str) -> str | None:
    """Extract a specific authentication result (e.g., spf=pass)."""
    pattern = rf"{mechanism}\s*=\s*(\w+)"
    match = re.search(pattern, header)
    return match.group(1).upper() if match else None
