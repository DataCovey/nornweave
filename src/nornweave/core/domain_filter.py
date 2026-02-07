"""Domain-level allow/blocklist filtering for inbound and outbound email.

Provides a ``DomainFilter`` that compiles regex patterns once at construction
and evaluates them via ``re.fullmatch`` against the domain portion of email
addresses.  Evaluation order: blocklist first (reject), then allowlist
(must match if non-empty), otherwise allow.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


class DomainFilter:
    """Regex-based domain allow/blocklist filter.

    Args:
        allowlist: Comma-separated regex patterns.  If non-empty, a domain
            must match at least one pattern to be allowed.
        blocklist: Comma-separated regex patterns.  If a domain matches any
            pattern it is rejected (takes precedence over the allowlist).
        direction: Label used in log messages (e.g. ``"inbound"``, ``"outbound"``).
    """

    def __init__(
        self,
        allowlist: str = "",
        blocklist: str = "",
        *,
        direction: str = "",
    ) -> None:
        self._allow_patterns = self._compile(allowlist)
        self._block_patterns = self._compile(blocklist)
        self._direction = direction

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_allowed(self, domain: str) -> bool:
        """Check whether *domain* passes the filter.

        Returns ``True`` if the domain is allowed, ``False`` if rejected.
        """
        domain = domain.lower()

        # 1. Blocklist — reject if any pattern matches
        for pattern in self._block_patterns:
            if pattern.fullmatch(domain):
                logger.info(
                    "Domain rejected (%s): '%s' matched blocklist pattern '%s'",
                    self._direction or "unknown",
                    domain,
                    pattern.pattern,
                )
                return False

        # 2. Allowlist — if non-empty, domain must match at least one pattern
        if self._allow_patterns:
            for pattern in self._allow_patterns:
                if pattern.fullmatch(domain):
                    logger.debug(
                        "Domain allowed (%s): '%s' matched allowlist pattern '%s'",
                        self._direction or "unknown",
                        domain,
                        pattern.pattern,
                    )
                    return True
            # Non-empty allowlist and no match → reject
            logger.info(
                "Domain rejected (%s): '%s' did not match any allowlist pattern",
                self._direction or "unknown",
                domain,
            )
            return False

        # 3. No allowlist restriction — allow
        logger.debug(
            "Domain allowed (%s): '%s' (no restrictions)",
            self._direction or "unknown",
            domain,
        )
        return True

    def check(self, email_address: str) -> bool:
        """Extract the domain from *email_address* and delegate to :meth:`is_allowed`.

        Args:
            email_address: A full email address (e.g. ``user@example.com``).

        Returns:
            ``True`` if the domain is allowed, ``False`` if rejected.
        """
        _local, sep, domain = email_address.rpartition("@")
        if not sep or not domain:
            logger.warning("Cannot extract domain from address: '%s'", email_address)
            return False
        return self.is_allowed(domain)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _compile(raw: str) -> Sequence[re.Pattern[str]]:
        """Split comma-separated string and compile each non-empty entry."""
        if not raw.strip():
            return ()
        patterns: list[re.Pattern[str]] = []
        for entry in raw.split(","):
            entry = entry.strip()
            if entry:
                patterns.append(re.compile(entry, re.IGNORECASE))
        return tuple(patterns)
