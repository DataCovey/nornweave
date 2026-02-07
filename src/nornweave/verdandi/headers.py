"""Email header parsing and generation utilities.

Provides RFC 5322 compliant header handling for:
- Message-ID generation
- References/In-Reply-To header building
- Header parsing and extraction
- Email address parsing
"""

import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import formataddr, formatdate, parseaddr
from typing import Any


@dataclass
class ParsedEmailAddress:
    """Parsed email address with display name and address parts."""

    display_name: str
    email: str
    original: str

    @property
    def formatted(self) -> str:
        """Get formatted address 'Name <email>' or just 'email' if no name."""
        if self.display_name:
            return formataddr((self.display_name, self.email))
        return self.email


def generate_message_id(domain: str, *, timestamp: datetime | None = None) -> str:
    """
    Generate an RFC 5322 compliant Message-ID.

    Format: <YYYYMMDDHHMMSS.UUID@domain>

    Args:
        domain: Domain to use in the Message-ID
        timestamp: Optional timestamp (defaults to now)

    Returns:
        Message-ID string with angle brackets

    Example:
        >>> generate_message_id("example.com")
        '<20260131153045.a1b2c3d4e5f6@example.com>'
    """
    timestamp = timestamp or datetime.now(UTC)
    ts_str = timestamp.strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex[:12]
    return f"<{ts_str}.{unique_id}@{domain}>"


def parse_email_address(address: str) -> ParsedEmailAddress:
    """
    Parse an email address into display name and email parts.

    Handles formats like:
    - "user@example.com"
    - "John Doe <john@example.com>"
    - "<john@example.com>"

    Args:
        address: Raw email address string

    Returns:
        ParsedEmailAddress with name and email parts
    """
    name, email = parseaddr(address)
    return ParsedEmailAddress(
        display_name=name.strip(),
        email=email.strip().lower(),
        original=address,
    )


def parse_email_list(addresses: str | list[str] | None) -> list[ParsedEmailAddress]:
    """
    Parse a list of email addresses.

    Args:
        addresses: Single address, comma-separated string, or list

    Returns:
        List of ParsedEmailAddress objects
    """
    if not addresses:
        return []

    if isinstance(addresses, str):
        # Split by comma, handling quoted names
        addr_list = []
        current = ""
        in_quotes = False
        in_brackets = False

        for char in addresses:
            if char == '"' and not in_brackets:
                in_quotes = not in_quotes
            elif char == "<":
                in_brackets = True
            elif char == ">":
                in_brackets = False
            elif char == "," and not in_quotes and not in_brackets:
                if current.strip():
                    addr_list.append(current.strip())
                current = ""
                continue
            current += char

        if current.strip():
            addr_list.append(current.strip())

        return [parse_email_address(addr) for addr in addr_list]

    return [parse_email_address(addr) for addr in addresses]


def build_references_header(
    parent_references: list[str] | None = None,
    parent_message_id: str | None = None,
    *,
    max_references: int = 20,
) -> str:
    """
    Build a References header for a reply message.

    Per RFC 5322, References should contain Message-IDs of all ancestors.
    We limit to max_references to prevent unbounded growth.

    Args:
        parent_references: References from the parent message
        parent_message_id: Message-ID of the parent message
        max_references: Maximum number of references to include

    Returns:
        Space-separated string of Message-IDs for the References header
    """
    refs: list[str] = []

    # Add existing references
    if parent_references:
        for ref in parent_references:
            normalized = normalize_message_id(ref)
            if normalized and normalized not in refs:
                refs.append(normalized)

    # Add parent Message-ID
    if parent_message_id:
        normalized = normalize_message_id(parent_message_id)
        if normalized and normalized not in refs:
            refs.append(normalized)

    # Trim to max (keep most recent)
    if len(refs) > max_references:
        refs = refs[-max_references:]

    return " ".join(refs)


def normalize_message_id(message_id: str | None) -> str | None:
    """
    Normalize a Message-ID to consistent format with angle brackets.

    Args:
        message_id: Raw Message-ID value

    Returns:
        Normalized Message-ID or None if invalid
    """
    if not message_id:
        return None

    mid = message_id.strip()
    if not mid:
        return None

    # Must contain @
    if "@" not in mid:
        return None

    # Ensure angle brackets
    if not mid.startswith("<"):
        mid = "<" + mid
    if not mid.endswith(">"):
        mid = mid + ">"

    return mid


def parse_references_header(references: str | None) -> list[str]:
    """
    Parse a References header into a list of Message-IDs.

    Args:
        references: Raw References header value

    Returns:
        List of normalized Message-ID strings
    """
    if not references:
        return []

    # Split by whitespace and filter
    refs = references.split()
    result = []

    for ref in refs:
        normalized = normalize_message_id(ref.strip())
        if normalized:
            result.append(normalized)

    return result


def parse_header_list(header_value: str | None) -> list[dict[str, str]]:
    """
    Parse header list format like Mailgun's message-headers JSON.

    Input format: [["Header-Name", "value"], ["Other", "value2"]]

    Args:
        header_value: JSON string or already parsed list

    Returns:
        List of dicts with 'name' and 'value' keys
    """
    if not header_value:
        return []

    import json

    if isinstance(header_value, str):
        try:
            parsed = json.loads(header_value)
        except json.JSONDecodeError, ValueError:
            return []
    else:
        parsed = header_value

    if not isinstance(parsed, list):
        return []

    result = []
    for item in parsed:
        if isinstance(item, list) and len(item) >= 2:
            result.append({"name": str(item[0]), "value": str(item[1])})
        elif isinstance(item, dict) and "name" in item and "value" in item:
            result.append({"name": str(item["name"]), "value": str(item["value"])})

    return result


def headers_list_to_dict(headers: list[dict[str, str]]) -> dict[str, str]:
    """
    Convert header list to dictionary (last value wins for duplicates).

    Args:
        headers: List of {'name': ..., 'value': ...} dicts

    Returns:
        Dictionary mapping header names to values
    """
    result: dict[str, str] = {}
    for h in headers:
        result[h["name"]] = h["value"]
    return result


def get_header(
    headers: dict[str, str] | list[dict[str, str]] | Any,
    name: str,
    *,
    case_insensitive: bool = True,
) -> str | None:
    """
    Get a header value by name from various header formats.

    Args:
        headers: Headers as dict, list, or other format
        name: Header name to find
        case_insensitive: Whether to match case-insensitively

    Returns:
        Header value or None if not found
    """
    if not headers:
        return None

    if isinstance(headers, dict):
        if case_insensitive:
            name_lower = name.lower()
            for k, v in headers.items():
                if k.lower() == name_lower:
                    return v
        return headers.get(name)

    if isinstance(headers, list):
        name_lower = name.lower() if case_insensitive else name
        for item in headers:
            if isinstance(item, dict):
                item_name = item.get("name", "")
                if case_insensitive:
                    if item_name.lower() == name_lower:
                        return item.get("value")
                elif item_name == name:
                    return item.get("value")

    return None


def format_rfc2822_date(dt: datetime | None = None) -> str:
    """
    Format a datetime as RFC 2822 for email Date header.

    Args:
        dt: Datetime to format (defaults to now)

    Returns:
        RFC 2822 formatted date string
    """
    dt = dt or datetime.now(UTC)
    return formatdate(dt.timestamp(), localtime=False, usegmt=True)


def ensure_reply_subject(subject: str | None, prefix: str = "Re: ") -> str:
    """
    Ensure subject has reply prefix.

    Args:
        subject: Original subject
        prefix: Prefix to add if missing (default "Re: ")

    Returns:
        Subject with reply prefix
    """
    if not subject:
        return prefix.rstrip(": ") + ": "

    # Check if already has Re: prefix (case-insensitive)
    if re.match(r"^re:\s*", subject, re.IGNORECASE):
        return subject

    return prefix + subject


@dataclass
class OutboundHeaders:
    """Headers to include in an outbound email."""

    message_id: str
    date: str
    in_reply_to: str | None = None
    references: str | None = None

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for provider API."""
        headers = {
            "Message-ID": self.message_id,
            "Date": self.date,
        }
        if self.in_reply_to:
            headers["In-Reply-To"] = self.in_reply_to
        if self.references:
            headers["References"] = self.references
        return headers


def build_reply_headers(
    domain: str,
    parent_message_id: str | None = None,
    parent_references: list[str] | None = None,
    *,
    timestamp: datetime | None = None,
) -> OutboundHeaders:
    """
    Build complete headers for a reply message.

    Args:
        domain: Domain for Message-ID generation
        parent_message_id: Message-ID of the parent message
        parent_references: References from the parent message
        timestamp: Optional timestamp for headers

    Returns:
        OutboundHeaders with all necessary fields
    """
    timestamp = timestamp or datetime.now(UTC)

    message_id = generate_message_id(domain, timestamp=timestamp)
    date_header = format_rfc2822_date(timestamp)

    in_reply_to = normalize_message_id(parent_message_id)
    references = build_references_header(parent_references, parent_message_id)

    return OutboundHeaders(
        message_id=message_id,
        date=date_header,
        in_reply_to=in_reply_to,
        references=references if references else None,
    )
