"""Unit tests for the DomainFilter class (core.domain_filter)."""

import pytest

from nornweave.core.domain_filter import DomainFilter

# ---------------------------------------------------------------------------
# Empty lists → allow all
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestEmptyLists:
    """When both allowlist and blocklist are empty, all domains pass."""

    def test_empty_strings_allow_all(self) -> None:
        f = DomainFilter(allowlist="", blocklist="")
        assert f.is_allowed("anything.com") is True

    def test_whitespace_only_treated_as_empty(self) -> None:
        f = DomainFilter(allowlist="  ", blocklist="  ")
        assert f.is_allowed("anything.com") is True


# ---------------------------------------------------------------------------
# Allowlist-only
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAllowlistOnly:
    """Non-empty allowlist with empty blocklist."""

    def test_matching_domain_allowed(self) -> None:
        f = DomainFilter(allowlist=r"example\.com")
        assert f.is_allowed("example.com") is True

    def test_non_matching_domain_rejected(self) -> None:
        f = DomainFilter(allowlist=r"example\.com")
        assert f.is_allowed("other.com") is False

    def test_multiple_patterns(self) -> None:
        f = DomainFilter(allowlist=r"example\.com,acme\.org")
        assert f.is_allowed("example.com") is True
        assert f.is_allowed("acme.org") is True
        assert f.is_allowed("other.com") is False


# ---------------------------------------------------------------------------
# Blocklist-only
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestBlocklistOnly:
    """Non-empty blocklist with empty allowlist."""

    def test_matching_domain_rejected(self) -> None:
        f = DomainFilter(blocklist=r"spam\.com")
        assert f.is_allowed("spam.com") is False

    def test_non_matching_domain_allowed(self) -> None:
        f = DomainFilter(blocklist=r"spam\.com")
        assert f.is_allowed("clean.com") is True

    def test_multiple_blocklist_patterns(self) -> None:
        f = DomainFilter(blocklist=r"spam\.com,junk\.org")
        assert f.is_allowed("spam.com") is False
        assert f.is_allowed("junk.org") is False
        assert f.is_allowed("clean.com") is True


# ---------------------------------------------------------------------------
# Both allowlist and blocklist (blocklist wins)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestBothLists:
    """Blocklist takes precedence over allowlist."""

    def test_blocklist_wins_over_allowlist(self) -> None:
        f = DomainFilter(
            allowlist=r"(.*\.)?example\.com",
            blocklist=r"noreply\.example\.com",
        )
        assert f.is_allowed("noreply.example.com") is False
        assert f.is_allowed("sales.example.com") is True
        assert f.is_allowed("example.com") is True

    def test_domain_not_in_either_list_rejected_by_allowlist(self) -> None:
        f = DomainFilter(
            allowlist=r"example\.com",
            blocklist=r"spam\.com",
        )
        assert f.is_allowed("other.com") is False


# ---------------------------------------------------------------------------
# Full-match semantics (no partial match)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFullMatch:
    """Patterns must match the entire domain, not a substring."""

    def test_no_partial_match_blocklist(self) -> None:
        f = DomainFilter(blocklist=r"evil\.com")
        assert f.is_allowed("evil.com") is False
        assert f.is_allowed("notevil.com") is True

    def test_no_partial_match_allowlist(self) -> None:
        f = DomainFilter(allowlist=r"ok\.com")
        assert f.is_allowed("ok.com") is True
        assert f.is_allowed("notok.com") is False

    def test_wildcard_subdomain_pattern(self) -> None:
        f = DomainFilter(allowlist=r"(.*\.)?acme\.com")
        assert f.is_allowed("acme.com") is True
        assert f.is_allowed("sub.acme.com") is True
        assert f.is_allowed("deep.sub.acme.com") is True
        assert f.is_allowed("other.com") is False


# ---------------------------------------------------------------------------
# Case insensitivity
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCaseInsensitivity:
    """Domain matching should be case-insensitive."""

    def test_uppercase_domain_matches(self) -> None:
        f = DomainFilter(allowlist=r"example\.com")
        assert f.is_allowed("EXAMPLE.COM") is True
        assert f.is_allowed("Example.Com") is True


# ---------------------------------------------------------------------------
# check() convenience method
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCheckMethod:
    """check() extracts domain from a full email address and delegates."""

    def test_extracts_domain_and_checks(self) -> None:
        f = DomainFilter(blocklist=r"blocked\.org")
        assert f.check("user@blocked.org") is False
        assert f.check("user@clean.com") is True

    def test_handles_display_name_style(self) -> None:
        """Addresses like 'user@sub@domain.com' pick rightmost @."""
        f = DomainFilter(allowlist=r"domain\.com")
        assert f.check("weird@user@domain.com") is True

    def test_no_at_sign_returns_false(self) -> None:
        f = DomainFilter()
        assert f.check("invalidemail") is False

    def test_empty_string_returns_false(self) -> None:
        f = DomainFilter()
        assert f.check("") is False


# ---------------------------------------------------------------------------
# Invalid regex detection (compile-time)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestInvalidRegex:
    """Invalid patterns should raise at compile time."""

    def test_invalid_allowlist_pattern_raises(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            DomainFilter(allowlist="[invalid")

    def test_invalid_blocklist_pattern_raises(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            DomainFilter(blocklist="(unclosed")
