"""Global send rate limiting (sliding-window counters).

Provides per-minute and per-hour rate limits for outbound email.
In-memory, single-process — no external dependencies required.
"""

import logging
import math
import threading
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimitResult:
    """Result of a rate-limit check.

    Attributes:
        allowed: Whether the request is allowed.
        retry_after_seconds: Seconds until capacity is expected (0.0 if allowed).
        detail: Human-readable explanation.
    """

    allowed: bool
    retry_after_seconds: float
    detail: str


class SlidingWindowCounter:
    """Sliding-window counter using time-bucketed sub-windows.

    Divides a rolling window into fixed-size buckets and sums their counts
    to approximate a true sliding window.  Thread-safe via ``threading.Lock``.

    Args:
        window_seconds: Total window duration in seconds (e.g. 60 for 1 minute).
        bucket_seconds: Duration of each sub-bucket in seconds (e.g. 1 for 1-second buckets).
        limit: Maximum events allowed within the window.  ``0`` means unlimited.
    """

    def __init__(self, window_seconds: int, bucket_seconds: int, limit: int) -> None:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if bucket_seconds <= 0:
            raise ValueError("bucket_seconds must be positive")
        if limit < 0:
            raise ValueError("limit must be non-negative")

        self._window_seconds = window_seconds
        self._bucket_seconds = bucket_seconds
        self._limit = limit
        self._num_buckets = window_seconds // bucket_seconds
        # Ring buffer: index → count
        self._buckets: list[int] = [0] * self._num_buckets
        # Timestamp of the last bucket that was written to
        self._last_bucket_time: float = 0.0
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _current_bucket_index(self, now: float) -> int:
        """Return the ring-buffer index for *now*."""
        return int(now / self._bucket_seconds) % self._num_buckets

    def _expire_old_buckets(self, now: float) -> None:
        """Zero-out buckets that have fallen outside the window."""
        if self._last_bucket_time == 0.0:
            # First call — clear everything
            self._buckets = [0] * self._num_buckets
            self._last_bucket_time = now
            return

        elapsed = now - self._last_bucket_time
        if elapsed >= self._window_seconds:
            # Entire window has elapsed — reset all
            self._buckets = [0] * self._num_buckets
        elif elapsed >= self._bucket_seconds:
            # Clear buckets that have rotated out
            buckets_to_clear = min(
                int(elapsed / self._bucket_seconds),
                self._num_buckets,
            )
            start_idx = self._current_bucket_index(self._last_bucket_time) + 1
            for i in range(buckets_to_clear):
                idx = (start_idx + i) % self._num_buckets
                self._buckets[idx] = 0

        self._last_bucket_time = now

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def limit(self) -> int:
        """Return the configured limit (0 = unlimited)."""
        return self._limit

    @property
    def window_name(self) -> str:
        """Human-readable window name for logging."""
        if self._window_seconds == 60:
            return "per-minute"
        if self._window_seconds == 3600:
            return "per-hour"
        return f"per-{self._window_seconds}s"

    def count(self, *, _now: float | None = None) -> int:
        """Return current event count within the rolling window.

        The optional ``_now`` parameter is for testing only.
        """
        now = _now if _now is not None else time.monotonic()
        with self._lock:
            self._expire_old_buckets(now)
            return sum(self._buckets)

    def record(self, *, _now: float | None = None) -> None:
        """Increment the counter for the current bucket.

        The optional ``_now`` parameter is for testing only.
        """
        now = _now if _now is not None else time.monotonic()
        with self._lock:
            self._expire_old_buckets(now)
            idx = self._current_bucket_index(now)
            self._buckets[idx] += 1

    def seconds_until_capacity(self, *, _now: float | None = None) -> float:
        """Return seconds until the window will have capacity again.

        Returns ``0.0`` if there is already capacity.
        The optional ``_now`` parameter is for testing only.
        """
        if self._limit == 0:
            return 0.0

        now = _now if _now is not None else time.monotonic()
        with self._lock:
            self._expire_old_buckets(now)
            current = sum(self._buckets)

        if current < self._limit:
            return 0.0

        # The oldest bucket will expire after bucket_seconds from the start
        # of the current window position.  Walk backwards to find the oldest
        # non-zero bucket and calculate when it will rotate out.
        cur_idx = self._current_bucket_index(now)
        for offset in range(self._num_buckets - 1, -1, -1):
            idx = (cur_idx - offset) % self._num_buckets
            if self._buckets[idx] > 0:
                # This bucket was written ~(offset * bucket_seconds) ago.
                # It expires when the window rolls past it.
                age = offset * self._bucket_seconds
                remaining = self._window_seconds - age
                # But we also need to account for partial bucket time
                bucket_start = int(now / self._bucket_seconds) * self._bucket_seconds
                time_into_current_bucket = now - bucket_start
                wait = remaining - time_into_current_bucket
                return max(wait, self._bucket_seconds)
        return float(self._bucket_seconds)


class GlobalRateLimiter:
    """Instance-level rate limiter for outbound email sends.

    Wraps two optional ``SlidingWindowCounter`` instances (per-minute and
    per-hour).  When both limits are 0 (unlimited), all checks pass
    immediately with no overhead.

    Args:
        per_minute_limit: Max sends per rolling minute (0 = unlimited).
        per_hour_limit: Max sends per rolling hour (0 = unlimited).
    """

    def __init__(self, per_minute_limit: int = 0, per_hour_limit: int = 0) -> None:
        self._per_minute: SlidingWindowCounter | None = None
        self._per_hour: SlidingWindowCounter | None = None

        if per_minute_limit > 0:
            self._per_minute = SlidingWindowCounter(
                window_seconds=60,
                bucket_seconds=1,
                limit=per_minute_limit,
            )
        if per_hour_limit > 0:
            self._per_hour = SlidingWindowCounter(
                window_seconds=3600,
                bucket_seconds=60,
                limit=per_hour_limit,
            )

    @property
    def enabled(self) -> bool:
        """Return True if at least one rate limit is configured."""
        return self._per_minute is not None or self._per_hour is not None

    def check(self) -> RateLimitResult:
        """Check whether a send is allowed without incrementing counters.

        Returns a ``RateLimitResult`` with ``allowed=True`` if both windows
        have capacity, or ``allowed=False`` with the longer ``retry_after``
        of the two windows.
        """
        if not self.enabled:
            return RateLimitResult(allowed=True, retry_after_seconds=0.0, detail="")

        exceeded: list[str] = []
        retry_after = 0.0

        for counter in (self._per_minute, self._per_hour):
            if counter is None or counter.limit == 0:
                continue
            current = counter.count()
            if current >= counter.limit:
                exceeded.append(f"{counter.window_name} limit reached ({current}/{counter.limit})")
                wait = counter.seconds_until_capacity()
                retry_after = max(retry_after, wait)

        if exceeded:
            detail = f"Rate limit exceeded: {'; '.join(exceeded)}"
            logger.warning(
                "Send rate-limited: %s (retry_after=%.1fs)",
                detail,
                retry_after,
            )
            return RateLimitResult(
                allowed=False,
                retry_after_seconds=retry_after,
                detail=detail,
            )

        # Log allowed at DEBUG with current counts
        minute_status = (
            f"{self._per_minute.count()}/{self._per_minute.limit}" if self._per_minute else "n/a"
        )
        hour_status = (
            f"{self._per_hour.count()}/{self._per_hour.limit}" if self._per_hour else "n/a"
        )
        logger.debug(
            "Send allowed (per-minute: %s, per-hour: %s)",
            minute_status,
            hour_status,
        )

        return RateLimitResult(allowed=True, retry_after_seconds=0.0, detail="")

    def record(self) -> None:
        """Record a successful send in both windows."""
        if self._per_minute is not None:
            self._per_minute.record()
        if self._per_hour is not None:
            self._per_hour.record()

    def retry_after_header(self, result: RateLimitResult) -> int:
        """Return integer seconds for the Retry-After header (rounded up)."""
        return max(1, math.ceil(result.retry_after_seconds))
