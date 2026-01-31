"""Shared utilities."""

import hashlib
import re
from typing import Sequence


def slugify(s: str, max_length: int = 64) -> str:
    """Convert string to a safe slug (lowercase, alphanumeric and hyphens)."""
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s)
    return s[:max_length].strip("-")


def participant_hash(addresses: Sequence[str]) -> str:
    """Stable hash of participant addresses for thread grouping."""
    normalized = sorted(a.lower().strip() for a in addresses if a)
    combined = "|".join(normalized)
    return hashlib.sha256(combined.encode()).hexdigest()[:16]
