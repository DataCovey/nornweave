"""Unit tests for the rate limiter (skuld.rate_limiter)."""

import pytest

from nornweave.skuld.rate_limiter import GlobalRateLimiter, RateLimitResult, SlidingWindowCounter

# ---------------------------------------------------------------------------
# SlidingWindowCounter — basic counting
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSlidingWindowCounterBasics:
    """Core counting behaviour of SlidingWindowCounter."""

    def test_initial_count_is_zero(self) -> None:
        c = SlidingWindowCounter(window_seconds=60, bucket_seconds=1, limit=10)
        assert c.count() == 0

    def test_record_increments_count(self) -> None:
        c = SlidingWindowCounter(window_seconds=60, bucket_seconds=1, limit=10)
        base = 1000.0
        c.record(_now=base)
        c.record(_now=base + 0.5)
        assert c.count(_now=base + 0.5) == 2

    def test_multiple_records_in_same_bucket(self) -> None:
        c = SlidingWindowCounter(window_seconds=10, bucket_seconds=1, limit=100)
        base = 500.0
        for _ in range(5):
            c.record(_now=base)
        assert c.count(_now=base) == 5

    def test_records_across_different_buckets(self) -> None:
        c = SlidingWindowCounter(window_seconds=10, bucket_seconds=1, limit=100)
        base = 500.0
        c.record(_now=base)
        c.record(_now=base + 1.0)
        c.record(_now=base + 2.0)
        assert c.count(_now=base + 2.5) == 3


# ---------------------------------------------------------------------------
# SlidingWindowCounter — window expiry
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSlidingWindowExpiry:
    """Events should expire after the window elapses."""

    def test_events_expire_after_window(self) -> None:
        c = SlidingWindowCounter(window_seconds=10, bucket_seconds=1, limit=5)
        base = 1000.0
        for i in range(5):
            c.record(_now=base + i)
        assert c.count(_now=base + 5) == 5
        # After full window passes, count resets
        assert c.count(_now=base + 15) == 0

    def test_partial_expiry(self) -> None:
        c = SlidingWindowCounter(window_seconds=10, bucket_seconds=1, limit=10)
        base = 1000.0
        # Record in buckets 0..4 (seconds 0-4)
        for i in range(5):
            c.record(_now=base + i)
        # At base+10, bucket 0 has expired but bucket 4 hasn't
        assert c.count(_now=base + 10) == 4  # buckets 1-4 still in window
        assert c.count(_now=base + 14) == 0  # all expired

    def test_full_window_elapsed_resets(self) -> None:
        c = SlidingWindowCounter(window_seconds=5, bucket_seconds=1, limit=3)
        base = 100.0
        c.record(_now=base)
        c.record(_now=base + 1)
        assert c.count(_now=base + 100) == 0  # far in the future


# ---------------------------------------------------------------------------
# SlidingWindowCounter — seconds_until_capacity
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSecondsUntilCapacity:
    """Retry-after calculation accuracy."""

    def test_has_capacity_returns_zero(self) -> None:
        c = SlidingWindowCounter(window_seconds=10, bucket_seconds=1, limit=5)
        assert c.seconds_until_capacity() == 0.0

    def test_at_limit_returns_positive(self) -> None:
        c = SlidingWindowCounter(window_seconds=10, bucket_seconds=1, limit=3)
        base = 1000.0
        for i in range(3):
            c.record(_now=base + i)
        wait = c.seconds_until_capacity(_now=base + 2.5)
        assert wait > 0

    def test_unlimited_always_zero(self) -> None:
        c = SlidingWindowCounter(window_seconds=60, bucket_seconds=1, limit=0)
        assert c.seconds_until_capacity() == 0.0

    def test_returns_at_least_bucket_seconds(self) -> None:
        """Minimum wait is one bucket interval."""
        c = SlidingWindowCounter(window_seconds=10, bucket_seconds=2, limit=1)
        base = 500.0
        c.record(_now=base)
        wait = c.seconds_until_capacity(_now=base)
        assert wait >= 2.0


# ---------------------------------------------------------------------------
# SlidingWindowCounter — property helpers
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSlidingWindowProperties:
    def test_limit_property(self) -> None:
        c = SlidingWindowCounter(window_seconds=60, bucket_seconds=1, limit=42)
        assert c.limit == 42

    def test_window_name_minute(self) -> None:
        c = SlidingWindowCounter(window_seconds=60, bucket_seconds=1, limit=1)
        assert c.window_name == "per-minute"

    def test_window_name_hour(self) -> None:
        c = SlidingWindowCounter(window_seconds=3600, bucket_seconds=60, limit=1)
        assert c.window_name == "per-hour"

    def test_window_name_custom(self) -> None:
        c = SlidingWindowCounter(window_seconds=30, bucket_seconds=1, limit=1)
        assert c.window_name == "per-30s"


# ---------------------------------------------------------------------------
# SlidingWindowCounter — constructor validation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSlidingWindowValidation:
    def test_zero_window_raises(self) -> None:
        with pytest.raises(ValueError, match="window_seconds"):
            SlidingWindowCounter(window_seconds=0, bucket_seconds=1, limit=1)

    def test_negative_limit_raises(self) -> None:
        with pytest.raises(ValueError, match="limit"):
            SlidingWindowCounter(window_seconds=60, bucket_seconds=1, limit=-1)


# ---------------------------------------------------------------------------
# GlobalRateLimiter — both disabled
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGlobalRateLimiterDisabled:
    """When both limits are 0, everything is allowed."""

    def test_always_allowed(self) -> None:
        rl = GlobalRateLimiter(per_minute_limit=0, per_hour_limit=0)
        assert not rl.enabled
        result = rl.check()
        assert result.allowed is True
        assert result.retry_after_seconds == 0.0

    def test_record_is_noop(self) -> None:
        rl = GlobalRateLimiter()
        rl.record()  # should not raise


# ---------------------------------------------------------------------------
# GlobalRateLimiter — per-minute only
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGlobalRateLimiterPerMinute:
    def test_allows_under_limit(self) -> None:
        rl = GlobalRateLimiter(per_minute_limit=3)
        assert rl.enabled
        rl.record()
        rl.record()
        result = rl.check()
        assert result.allowed is True

    def test_blocks_at_limit(self) -> None:
        rl = GlobalRateLimiter(per_minute_limit=2)
        rl.record()
        rl.record()
        result = rl.check()
        assert result.allowed is False
        assert result.retry_after_seconds > 0
        assert "per-minute" in result.detail


# ---------------------------------------------------------------------------
# GlobalRateLimiter — per-hour only
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGlobalRateLimiterPerHour:
    def test_allows_under_limit(self) -> None:
        rl = GlobalRateLimiter(per_hour_limit=5)
        for _ in range(4):
            rl.record()
        result = rl.check()
        assert result.allowed is True

    def test_blocks_at_limit(self) -> None:
        rl = GlobalRateLimiter(per_hour_limit=2)
        rl.record()
        rl.record()
        result = rl.check()
        assert result.allowed is False
        assert "per-hour" in result.detail


# ---------------------------------------------------------------------------
# GlobalRateLimiter — both active
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGlobalRateLimiterBothActive:
    def test_both_under_limit(self) -> None:
        rl = GlobalRateLimiter(per_minute_limit=5, per_hour_limit=50)
        rl.record()
        result = rl.check()
        assert result.allowed is True

    def test_minute_exceeded_hour_ok(self) -> None:
        rl = GlobalRateLimiter(per_minute_limit=2, per_hour_limit=50)
        rl.record()
        rl.record()
        result = rl.check()
        assert result.allowed is False
        assert "per-minute" in result.detail

    def test_check_only_does_not_increment(self) -> None:
        """check() must not affect counters."""
        rl = GlobalRateLimiter(per_minute_limit=1)
        result = rl.check()
        assert result.allowed is True
        # Still allowed — check didn't consume capacity
        result2 = rl.check()
        assert result2.allowed is True


# ---------------------------------------------------------------------------
# RateLimitResult
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRateLimitResult:
    def test_allowed_result(self) -> None:
        r = RateLimitResult(allowed=True, retry_after_seconds=0.0, detail="")
        assert r.allowed is True

    def test_denied_result(self) -> None:
        r = RateLimitResult(allowed=False, retry_after_seconds=5.3, detail="exceeded")
        assert r.allowed is False
        assert r.retry_after_seconds == 5.3
        assert r.detail == "exceeded"

    def test_retry_after_header_rounds_up(self) -> None:
        rl = GlobalRateLimiter(per_minute_limit=1)
        r = RateLimitResult(allowed=False, retry_after_seconds=2.1, detail="x")
        assert rl.retry_after_header(r) == 3  # ceil(2.1)

    def test_retry_after_header_minimum_one(self) -> None:
        rl = GlobalRateLimiter()
        r = RateLimitResult(allowed=False, retry_after_seconds=0.01, detail="x")
        assert rl.retry_after_header(r) >= 1


# ---------------------------------------------------------------------------
# Settings validation — negative values
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSettingsRateLimitValidation:
    """Negative rate-limit settings should be rejected at startup."""

    def test_negative_per_minute_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from nornweave.core.config import Settings

        monkeypatch.setenv("GLOBAL_SEND_RATE_LIMIT_PER_MINUTE", "-1")
        monkeypatch.setenv("GLOBAL_SEND_RATE_LIMIT_PER_HOUR", "0")
        with pytest.raises(Exception, match="GLOBAL_SEND_RATE_LIMIT_PER_MINUTE"):
            Settings(_env_file=None)  # type: ignore[call-arg]

    def test_negative_per_hour_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from nornweave.core.config import Settings

        monkeypatch.setenv("GLOBAL_SEND_RATE_LIMIT_PER_MINUTE", "0")
        monkeypatch.setenv("GLOBAL_SEND_RATE_LIMIT_PER_HOUR", "-5")
        with pytest.raises(Exception, match="GLOBAL_SEND_RATE_LIMIT_PER_HOUR"):
            Settings(_env_file=None)  # type: ignore[call-arg]

    def test_zero_values_accepted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from nornweave.core.config import Settings

        monkeypatch.setenv("GLOBAL_SEND_RATE_LIMIT_PER_MINUTE", "0")
        monkeypatch.setenv("GLOBAL_SEND_RATE_LIMIT_PER_HOUR", "0")
        s = Settings(_env_file=None)  # type: ignore[call-arg]
        assert s.global_send_rate_limit_per_minute == 0
        assert s.global_send_rate_limit_per_hour == 0

    def test_positive_values_accepted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from nornweave.core.config import Settings

        monkeypatch.setenv("GLOBAL_SEND_RATE_LIMIT_PER_MINUTE", "10")
        monkeypatch.setenv("GLOBAL_SEND_RATE_LIMIT_PER_HOUR", "100")
        s = Settings(_env_file=None)  # type: ignore[call-arg]
        assert s.global_send_rate_limit_per_minute == 10
        assert s.global_send_rate_limit_per_hour == 100
