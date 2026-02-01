"""Attachment handling: MIME parsing, Content-ID mapping, validation.

Provides utilities for:
- Parsing MIME attachments from raw email content
- Extracting attachments from multipart form data
- Content-ID handling for inline images
- File type validation and security checks
- Text extraction from attachments (PDF, CSV, etc.)
"""

import email
import mimetypes
import re
from dataclasses import dataclass, field
from email import policy
from typing import TYPE_CHECKING, Any

from nornweave.core.interfaces import InboundAttachment
from nornweave.models.attachment import AttachmentDisposition

if TYPE_CHECKING:
    from email.message import EmailMessage

# Blocked file extensions for security
BLOCKED_EXTENSIONS = {
    ".exe",
    ".bat",
    ".cmd",
    ".scr",
    ".com",
    ".pif",
    ".vbs",
    ".vbe",
    ".js",
    ".jse",
    ".ws",
    ".wsf",
    ".wsc",
    ".wsh",
    ".ps1",
    ".ps1xml",
    ".ps2",
    ".ps2xml",
    ".psc1",
    ".psc2",
    ".msh",
    ".msh1",
    ".msh2",
    ".mshxml",
    ".msh1xml",
    ".msh2xml",
    ".scf",
    ".lnk",
    ".inf",
    ".reg",
}

# Maximum sizes
MAX_SINGLE_ATTACHMENT_SIZE = 25 * 1024 * 1024  # 25 MB
MAX_TOTAL_ATTACHMENT_SIZE = 35 * 1024 * 1024  # 35 MB
MAX_ATTACHMENT_COUNT = 20


@dataclass
class AttachmentValidationResult:
    """Result of attachment validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ContentIdMapping:
    """Mapping from Content-ID to attachment info."""

    content_id: str
    filename: str
    attachment_index: int


def parse_mime_attachments(raw_mime: str | bytes) -> list[InboundAttachment]:
    """
    Parse attachments from raw MIME email content.

    Used for AWS SES which provides the full raw email.

    Args:
        raw_mime: Raw MIME email content

    Returns:
        List of InboundAttachment objects
    """
    if isinstance(raw_mime, bytes):
        raw_mime = raw_mime.decode("utf-8", errors="replace")

    msg = email.message_from_string(raw_mime, policy=policy.default)
    return _extract_attachments_from_message(msg)


def _extract_attachments_from_message(msg: EmailMessage) -> list[InboundAttachment]:
    """Extract attachments from an EmailMessage object."""
    attachments: list[InboundAttachment] = []

    for part in msg.walk():
        # Skip multipart containers
        if part.is_multipart():
            continue

        content_disposition = part.get_content_disposition()

        # Process both attachment and inline parts
        if content_disposition in ("attachment", "inline"):
            filename = part.get_filename() or "unnamed"
            content_type = part.get_content_type()
            payload = part.get_payload(decode=True)

            # get_payload returns bytes when decode=True for non-multipart
            if payload is None or not isinstance(payload, bytes):
                continue
            content: bytes = payload

            # Get Content-ID for inline attachments
            content_id = part.get("Content-ID")
            if content_id:
                # Strip angle brackets
                content_id = content_id.strip("<>")

            disposition = (
                AttachmentDisposition.INLINE
                if content_disposition == "inline"
                else AttachmentDisposition.ATTACHMENT
            )

            attachments.append(
                InboundAttachment(
                    filename=filename,
                    content_type=content_type,
                    content=content,
                    size_bytes=len(content),
                    disposition=disposition,
                    content_id=content_id,
                )
            )

    return attachments


def parse_content_id_map(content_id_map_json: str | dict[str, str] | None) -> dict[str, str]:
    """
    Parse content-id-map from Mailgun/SendGrid format.

    The content-id-map maps Content-IDs to attachment field names:
    {"ii_abc123": "attachment1", "ii_def456": "attachment2"}

    Args:
        content_id_map_json: JSON string or dict of content ID mappings

    Returns:
        Dictionary mapping Content-ID to attachment field name
    """
    if not content_id_map_json:
        return {}

    if isinstance(content_id_map_json, str):
        import json

        try:
            return json.loads(content_id_map_json)
        except (json.JSONDecodeError, ValueError):
            return {}

    return dict(content_id_map_json)


def normalize_content_id(content_id: str | None) -> str | None:
    """
    Normalize a Content-ID by stripping angle brackets.

    Args:
        content_id: Raw Content-ID value

    Returns:
        Normalized Content-ID without angle brackets
    """
    if not content_id:
        return None

    cid = content_id.strip()
    if cid.startswith("<"):
        cid = cid[1:]
    if cid.endswith(">"):
        cid = cid[:-1]

    return cid if cid else None


def build_content_id_to_filename_map(
    attachments: list[InboundAttachment],
) -> dict[str, str]:
    """
    Build a mapping from Content-ID to filename for inline attachments.

    Args:
        attachments: List of attachments

    Returns:
        Dictionary mapping Content-ID to filename
    """
    mapping: dict[str, str] = {}

    for att in attachments:
        if att.content_id:
            cid = normalize_content_id(att.content_id)
            if cid:
                mapping[cid] = att.filename

    return mapping


def validate_attachments(
    attachments: list[InboundAttachment],
    *,
    max_single_size: int = MAX_SINGLE_ATTACHMENT_SIZE,
    max_total_size: int = MAX_TOTAL_ATTACHMENT_SIZE,
    max_count: int = MAX_ATTACHMENT_COUNT,
    check_extensions: bool = True,
) -> AttachmentValidationResult:
    """
    Validate a list of attachments against size and security constraints.

    Args:
        attachments: List of attachments to validate
        max_single_size: Maximum size for single attachment
        max_total_size: Maximum total size for all attachments
        max_count: Maximum number of attachments
        check_extensions: Whether to check for blocked extensions

    Returns:
        AttachmentValidationResult with validation status
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Check count
    if len(attachments) > max_count:
        errors.append(f"Too many attachments: {len(attachments)} > {max_count}")

    total_size = 0

    for i, att in enumerate(attachments):
        # Check single size
        if att.size_bytes > max_single_size:
            errors.append(
                f"Attachment {i + 1} ({att.filename}) too large: "
                f"{att.size_bytes / 1024 / 1024:.1f}MB > {max_single_size / 1024 / 1024:.1f}MB"
            )

        total_size += att.size_bytes

        # Check extension
        if check_extensions:
            ext = _get_extension(att.filename).lower()
            if ext in BLOCKED_EXTENSIONS:
                errors.append(f"Blocked file type: {att.filename}")

        # Validate content-type matches filename
        guessed_type, _ = mimetypes.guess_type(att.filename)
        if guessed_type and guessed_type != att.content_type:
            warnings.append(
                f"Content-type mismatch for {att.filename}: "
                f"claimed {att.content_type}, expected {guessed_type}"
            )

    # Check total size
    if total_size > max_total_size:
        errors.append(
            f"Total attachment size too large: "
            f"{total_size / 1024 / 1024:.1f}MB > {max_total_size / 1024 / 1024:.1f}MB"
        )

    return AttachmentValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def _get_extension(filename: str) -> str:
    """Get the file extension from a filename."""
    if not filename:
        return ""
    parts = filename.rsplit(".", 1)
    if len(parts) > 1:
        return "." + parts[1]
    return ""


def resolve_cid_urls_in_html(
    html: str,
    attachments: list[InboundAttachment],
    *,
    base_url: str = "/v1/attachments",
) -> str:
    """
    Replace cid: URLs in HTML with actual attachment URLs.

    This is useful for rendering HTML emails with inline images.

    Args:
        html: HTML content with cid: URLs
        attachments: List of attachments
        base_url: Base URL for attachment downloads

    Returns:
        HTML with cid: URLs replaced with actual URLs
    """
    if not html:
        return html

    # Build cid to attachment_id mapping
    cid_to_id: dict[str, str] = {}
    for i, att in enumerate(attachments):
        if att.content_id:
            cid = normalize_content_id(att.content_id)
            if cid:
                # Use index as ID placeholder (real ID would come from storage)
                cid_to_id[cid] = f"att_{i}"

    # Replace cid: URLs
    def replace_cid(match: re.Match[str]) -> str:
        cid = match.group(1)
        att_id = cid_to_id.get(cid)
        if att_id:
            return f"{base_url}/{att_id}/download"
        return match.group(0)  # Keep original if not found

    # Pattern matches cid:xxx in src attributes
    pattern = r'cid:([^"\'\s>]+)'
    return re.sub(pattern, replace_cid, html)


def extract_text_from_attachment(
    content_bytes: bytes,
    content_type: str,
    filename: str | None = None,
) -> str:
    """
    Extract plain text from attachment content.

    Supports:
    - Plain text files
    - PDF files (requires pypdf or pdfplumber)
    - CSV files
    - More formats in Phase 2

    Args:
        content_bytes: Raw attachment content
        content_type: MIME content type
        filename: Optional filename for type detection

    Returns:
        Extracted plain text or empty string
    """
    # Plain text
    if content_type.startswith("text/"):
        try:
            return content_bytes.decode("utf-8", errors="replace")
        except Exception:
            return ""

    # CSV (treat as text)
    if content_type == "text/csv" or (filename and filename.endswith(".csv")):
        try:
            return content_bytes.decode("utf-8", errors="replace")
        except Exception:
            return ""

    # PDF extraction (requires optional dependency)
    if content_type == "application/pdf" or (filename and filename.endswith(".pdf")):
        try:
            return _extract_text_from_pdf(content_bytes)
        except Exception:
            return ""

    # Unknown type
    return ""


def _extract_text_from_pdf(content_bytes: bytes) -> str:
    """Extract text from PDF using available library."""
    # Try pypdf first
    try:
        from io import BytesIO

        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content_bytes))
        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
        return "\n\n".join(text_parts)
    except ImportError:
        pass

    # Try pdfplumber
    try:
        from io import BytesIO

        import pdfplumber

        with pdfplumber.open(BytesIO(content_bytes)) as pdf:
            text_parts = []
            for page in pdf.pages:
                text_parts.append(page.extract_text() or "")
            return "\n\n".join(text_parts)
    except ImportError:
        pass

    return ""


def parse_attachment_info_json(
    attachment_info: str | dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    """
    Parse SendGrid attachment-info JSON format.

    Format:
    {
        "attachment1": {
            "filename": "image.jpg",
            "name": "image.jpg",
            "type": "image/jpeg",
            "content-id": "ii_abc123"
        }
    }

    Args:
        attachment_info: JSON string or dict

    Returns:
        Parsed attachment info dictionary
    """
    if not attachment_info:
        return {}

    if isinstance(attachment_info, str):
        import json

        try:
            return json.loads(attachment_info)
        except (json.JSONDecodeError, ValueError):
            return {}

    return dict(attachment_info)


def guess_content_type(filename: str, default: str = "application/octet-stream") -> str:
    """
    Guess the content type from a filename.

    Args:
        filename: The filename to check
        default: Default type if guessing fails

    Returns:
        MIME content type
    """
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or default
