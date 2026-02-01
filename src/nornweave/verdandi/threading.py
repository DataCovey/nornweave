"""Thread grouping logic using JWZ algorithm with Gmail-like heuristics.

This module implements email threading based on:
1. RFC 5322 headers: Message-ID, In-Reply-To, References
2. Subject normalization for subject-only matching
3. Time-window constraints (7-day window for subject matches)
4. Participant consistency checks (optional)

Reference: https://www.jwz.org/doc/threading.html
"""

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nornweave.core.interfaces import StorageInterface


# Subject prefixes to strip for normalization (multi-language)
REPLY_PREFIXES = re.compile(
    r"^(?:re|fwd|fw|reply|aw|wg|sv|antw|vs|ref|enc|rv):\s*",
    re.IGNORECASE,
)

# Default time window for subject-only matching (Gmail uses ~7 days)
SUBJECT_MATCH_WINDOW_DAYS = 7


@dataclass
class ThreadResolutionResult:
    """Result of thread resolution."""

    thread_id: str
    is_new_thread: bool
    matched_by: str  # "references", "in_reply_to", "subject", or "new"


def normalize_subject(subject: str) -> str:
    """
    Normalize subject for thread matching.

    Strips common reply/forward prefixes in multiple languages,
    collapses whitespace, and lowercases for comparison.

    Examples:
        "Re: Hello" -> "hello"
        "Fwd: Re: Meeting" -> "meeting"
        "AW: Anfrage" -> "anfrage" (German)
        "SV: Förfrågan" -> "förfrågan" (Swedish)

    Args:
        subject: Original email subject

    Returns:
        Normalized subject string for comparison
    """
    if not subject:
        return ""

    normalized = subject.strip()

    # Iteratively strip reply/forward prefixes
    while True:
        result = REPLY_PREFIXES.sub("", normalized, count=1).strip()
        if result == normalized:
            break
        normalized = result

    # Collapse whitespace and lowercase
    normalized = " ".join(normalized.split()).lower()

    return normalized


def compute_participant_hash(
    from_address: str,
    to_addresses: list[str],
    cc_addresses: list[str] | None = None,
) -> str:
    """
    Compute a hash of thread participants for grouping.

    This creates a canonical representation of participants
    that can be used as a secondary threading signal.

    Args:
        from_address: Sender email address
        to_addresses: List of recipient addresses
        cc_addresses: Optional list of CC addresses

    Returns:
        SHA-256 hash of sorted, normalized participants
    """
    # Normalize and collect all addresses
    participants = set()

    def normalize_addr(addr: str) -> str:
        # Extract just the email part, lowercase
        addr = addr.lower().strip()
        # Handle "Name <email>" format
        if "<" in addr and ">" in addr:
            addr = addr.split("<")[1].split(">")[0]
        return addr

    participants.add(normalize_addr(from_address))
    for addr in to_addresses:
        participants.add(normalize_addr(addr))
    if cc_addresses:
        for addr in cc_addresses:
            participants.add(normalize_addr(addr))

    # Sort for consistent hashing
    sorted_participants = sorted(participants)
    combined = ",".join(sorted_participants)

    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def parse_references_header(references: str | None) -> list[str]:
    """
    Parse the References header into a list of Message-IDs.

    References header contains space-separated Message-IDs:
    "<id1@host> <id2@host> <id3@host>"

    Args:
        references: Raw References header value

    Returns:
        List of Message-ID strings
    """
    if not references:
        return []

    # Split by whitespace and filter empty
    refs = [ref.strip() for ref in references.split() if ref.strip()]

    # Validate that each looks like a Message-ID (contains @, wrapped in <>)
    valid_refs = []
    for ref in refs:
        if "@" in ref:
            # Normalize: ensure angle brackets
            if not ref.startswith("<"):
                ref = "<" + ref
            if not ref.endswith(">"):
                ref = ref + ">"
            valid_refs.append(ref)

    return valid_refs


def normalize_message_id(message_id: str | None) -> str | None:
    """
    Normalize a Message-ID for consistent storage and lookup.

    Args:
        message_id: Raw Message-ID value

    Returns:
        Normalized Message-ID with angle brackets, or None
    """
    if not message_id:
        return None

    mid = message_id.strip()
    if not mid:
        return None

    # Ensure angle brackets
    if not mid.startswith("<"):
        mid = "<" + mid
    if not mid.endswith(">"):
        mid = mid + ">"

    return mid


async def resolve_thread(
    storage: StorageInterface,
    inbox_id: str,
    *,
    message_id: str | None = None,  # noqa: ARG001 - reserved for future use
    in_reply_to: str | None = None,
    references: list[str] | None = None,
    subject: str = "",
    timestamp: datetime | None = None,
    from_address: str = "",  # noqa: ARG001 - reserved for future use
    to_addresses: list[str] | None = None,  # noqa: ARG001 - reserved for future use
) -> ThreadResolutionResult:
    """
    Resolve thread ID using JWZ algorithm with Gmail-like heuristics.

    Algorithm:
    1. If References exist, find matching parent message (last ref first)
    2. If In-Reply-To exists and no References match, try In-Reply-To
    3. If neither header matches, try subject-only matching within 7-day window
    4. If no match, create new thread

    Args:
        storage: Storage interface for lookups
        inbox_id: Inbox to search within
        message_id: This message's Message-ID (for storing)
        in_reply_to: In-Reply-To header (parent Message-ID)
        references: List of Message-IDs from References header
        subject: Email subject
        timestamp: Message timestamp (for subject matching window)
        from_address: Sender address (for participant hash)
        to_addresses: Recipient addresses (for participant hash)

    Returns:
        ThreadResolutionResult with thread_id and metadata
    """
    import uuid

    timestamp = timestamp or datetime.utcnow()

    # Priority 1: Check References header (most reliable)
    if references:
        # Check references in reverse order (most recent parent first)
        for ref in reversed(references):
            normalized_ref = normalize_message_id(ref)
            if normalized_ref:
                parent_msg = await storage.get_message_by_provider_id(inbox_id, normalized_ref)
                if parent_msg:
                    return ThreadResolutionResult(
                        thread_id=parent_msg.thread_id,
                        is_new_thread=False,
                        matched_by="references",
                    )

    # Priority 2: Check In-Reply-To header
    if in_reply_to:
        in_reply_to = normalize_message_id(in_reply_to)
        if in_reply_to:
            parent_msg = await storage.get_message_by_provider_id(inbox_id, in_reply_to)
            if parent_msg:
                return ThreadResolutionResult(
                    thread_id=parent_msg.thread_id,
                    is_new_thread=False,
                    matched_by="in_reply_to",
                )

    # Priority 3: Subject-only matching within time window
    if subject:
        normalized = normalize_subject(subject)
        if normalized:
            # Only match subjects within 7-day window
            since_time = timestamp - timedelta(days=SUBJECT_MATCH_WINDOW_DAYS)
            thread = await storage.get_thread_by_subject(inbox_id, normalized, since=since_time)
            if thread:
                return ThreadResolutionResult(
                    thread_id=thread.thread_id,
                    is_new_thread=False,
                    matched_by="subject",
                )

    # No match found: create new thread
    new_thread_id = str(uuid.uuid4())
    return ThreadResolutionResult(
        thread_id=new_thread_id,
        is_new_thread=True,
        matched_by="new",
    )


def resolve_thread_id(
    _message_id: str | None,
    _references: str | None,
    _in_reply_to: str | None,
    _subject: str,
) -> str | None:
    """
    Legacy synchronous placeholder for thread resolution.

    Deprecated: Use async resolve_thread() instead.
    """
    return None


def build_references_chain(
    parent_references: list[str] | None,
    parent_message_id: str | None,
    *,
    max_length: int = 20,
) -> list[str]:
    """
    Build References chain for a reply message.

    Per RFC 5322, the References header should contain the Message-IDs
    of all ancestor messages in the thread. To prevent unbounded growth,
    we limit to the most recent ~20 entries.

    Args:
        parent_references: References from the parent message
        parent_message_id: Message-ID of the parent message
        max_length: Maximum number of references to include

    Returns:
        List of Message-IDs for the new References header
    """
    refs: list[str] = []

    # Start with existing references
    if parent_references:
        refs.extend(parent_references)

    # Add parent's Message-ID
    if parent_message_id:
        parent_mid = normalize_message_id(parent_message_id)
        if parent_mid and parent_mid not in refs:
            refs.append(parent_mid)

    # Trim to max length (keep most recent)
    if len(refs) > max_length:
        refs = refs[-max_length:]

    return refs


def should_thread_together(
    subject1: str,
    subject2: str,
    time_diff: timedelta | None = None,
) -> bool:
    """
    Determine if two messages should be in the same thread based on subject.

    Uses normalized subject comparison and optional time constraint.

    Args:
        subject1: First message subject
        subject2: Second message subject
        time_diff: Time difference between messages (optional)

    Returns:
        True if messages should be threaded together
    """
    # Normalize both subjects
    norm1 = normalize_subject(subject1)
    norm2 = normalize_subject(subject2)

    # Empty subjects never match
    if not norm1 or not norm2:
        return False

    # Subjects must match
    if norm1 != norm2:
        return False

    # Check time window if provided
    if time_diff is not None:
        max_diff = timedelta(days=SUBJECT_MATCH_WINDOW_DAYS)
        if abs(time_diff) > max_diff:
            return False

    return True
