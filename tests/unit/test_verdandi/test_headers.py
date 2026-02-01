"""Unit tests for email header utilities."""

from datetime import datetime

from nornweave.verdandi.headers import (
    OutboundHeaders,
    build_references_header,
    build_reply_headers,
    ensure_reply_subject,
    format_rfc2822_date,
    generate_message_id,
    get_header,
    headers_list_to_dict,
    parse_email_address,
    parse_email_list,
    parse_header_list,
    parse_references_header,
)


class TestGenerateMessageId:
    """Tests for Message-ID generation."""

    def test_format(self) -> None:
        """Test Message-ID format."""
        mid = generate_message_id("example.com")
        assert mid.startswith("<")
        assert mid.endswith(">")
        assert "@example.com>" in mid

    def test_uniqueness(self) -> None:
        """Test that Message-IDs are unique."""
        mid1 = generate_message_id("example.com")
        mid2 = generate_message_id("example.com")
        assert mid1 != mid2

    def test_custom_timestamp(self) -> None:
        """Test with custom timestamp."""
        ts = datetime(2026, 1, 31, 12, 0, 0)
        mid = generate_message_id("example.com", timestamp=ts)
        assert "20260131120000" in mid


class TestParseEmailAddress:
    """Tests for email address parsing."""

    def test_simple_email(self) -> None:
        """Test simple email address."""
        parsed = parse_email_address("alice@example.com")
        assert parsed.email == "alice@example.com"
        assert parsed.display_name == ""

    def test_with_name(self) -> None:
        """Test email with display name."""
        parsed = parse_email_address("Alice Smith <alice@example.com>")
        assert parsed.email == "alice@example.com"
        assert parsed.display_name == "Alice Smith"

    def test_formatted_output(self) -> None:
        """Test formatted output."""
        parsed = parse_email_address("Alice Smith <alice@example.com>")
        assert "Alice Smith" in parsed.formatted
        assert "alice@example.com" in parsed.formatted


class TestParseEmailList:
    """Tests for email list parsing."""

    def test_single_email(self) -> None:
        """Test single email."""
        emails = parse_email_list("alice@example.com")
        assert len(emails) == 1
        assert emails[0].email == "alice@example.com"

    def test_comma_separated(self) -> None:
        """Test comma-separated emails."""
        emails = parse_email_list("alice@example.com, bob@example.com")
        assert len(emails) == 2
        assert emails[0].email == "alice@example.com"
        assert emails[1].email == "bob@example.com"

    def test_with_names(self) -> None:
        """Test emails with display names."""
        emails = parse_email_list("Alice <alice@example.com>, Bob <bob@example.com>")
        assert len(emails) == 2
        assert emails[0].display_name == "Alice"
        assert emails[1].display_name == "Bob"

    def test_list_input(self) -> None:
        """Test list input."""
        emails = parse_email_list(["alice@example.com", "bob@example.com"])
        assert len(emails) == 2

    def test_empty(self) -> None:
        """Test empty input."""
        assert parse_email_list("") == []
        assert parse_email_list(None) == []


class TestBuildReferencesHeader:
    """Tests for building References header."""

    def test_no_parent(self) -> None:
        """Test with no parent references."""
        refs = build_references_header(None, "<parent@example.com>")
        assert refs == "<parent@example.com>"

    def test_with_parent_refs(self) -> None:
        """Test with parent references."""
        refs = build_references_header(
            ["<ref1@example.com>", "<ref2@example.com>"],
            "<parent@example.com>",
        )
        assert "<ref1@example.com>" in refs
        assert "<ref2@example.com>" in refs
        assert "<parent@example.com>" in refs

    def test_max_references(self) -> None:
        """Test reference count limit."""
        parent_refs = [f"<ref{i}@example.com>" for i in range(25)]
        refs = build_references_header(parent_refs, "<parent@example.com>", max_references=5)
        # Count space-separated refs
        ref_count = len(refs.split())
        assert ref_count == 5


class TestParseReferencesHeader:
    """Tests for parsing References header."""

    def test_single_ref(self) -> None:
        """Test single reference."""
        refs = parse_references_header("<abc@example.com>")
        assert refs == ["<abc@example.com>"]

    def test_multiple_refs(self) -> None:
        """Test multiple references."""
        refs = parse_references_header("<abc@example.com> <def@example.com>")
        assert len(refs) == 2

    def test_empty(self) -> None:
        """Test empty input."""
        assert parse_references_header("") == []
        assert parse_references_header(None) == []


class TestParseHeaderList:
    """Tests for parsing header list format."""

    def test_mailgun_format(self) -> None:
        """Test Mailgun's [name, value] format."""
        headers = parse_header_list('[["From", "alice@example.com"], ["To", "bob@example.com"]]')
        assert len(headers) == 2
        assert headers[0]["name"] == "From"
        assert headers[0]["value"] == "alice@example.com"

    def test_dict_format(self) -> None:
        """Test dict list format."""
        headers = parse_header_list(
            [
                {"name": "From", "value": "alice@example.com"},
                {"name": "To", "value": "bob@example.com"},
            ]
        )
        assert len(headers) == 2

    def test_empty(self) -> None:
        """Test empty input."""
        assert parse_header_list("") == []
        assert parse_header_list(None) == []


class TestHeadersListToDict:
    """Tests for converting header list to dict."""

    def test_conversion(self) -> None:
        """Test list to dict conversion."""
        headers = [
            {"name": "From", "value": "alice@example.com"},
            {"name": "To", "value": "bob@example.com"},
        ]
        result = headers_list_to_dict(headers)
        assert result["From"] == "alice@example.com"
        assert result["To"] == "bob@example.com"

    def test_duplicate_last_wins(self) -> None:
        """Test that last value wins for duplicates."""
        headers = [
            {"name": "X-Custom", "value": "first"},
            {"name": "X-Custom", "value": "second"},
        ]
        result = headers_list_to_dict(headers)
        assert result["X-Custom"] == "second"


class TestGetHeader:
    """Tests for getting header values."""

    def test_from_dict(self) -> None:
        """Test getting header from dict."""
        headers = {"From": "alice@example.com", "To": "bob@example.com"}
        assert get_header(headers, "From") == "alice@example.com"

    def test_case_insensitive(self) -> None:
        """Test case-insensitive lookup."""
        headers = {"From": "alice@example.com"}
        assert get_header(headers, "from") == "alice@example.com"
        assert get_header(headers, "FROM") == "alice@example.com"

    def test_from_list(self) -> None:
        """Test getting header from list."""
        headers = [{"name": "From", "value": "alice@example.com"}]
        assert get_header(headers, "From") == "alice@example.com"

    def test_not_found(self) -> None:
        """Test header not found."""
        headers = {"From": "alice@example.com"}
        assert get_header(headers, "X-Missing") is None


class TestFormatRfc2822Date:
    """Tests for RFC 2822 date formatting."""

    def test_format(self) -> None:
        """Test date format."""
        dt = datetime(2026, 1, 31, 12, 0, 0)
        formatted = format_rfc2822_date(dt)
        # January 31, 2026 is a Saturday
        assert "Sat, 31 Jan 2026" in formatted

    def test_default_now(self) -> None:
        """Test default to current time."""
        formatted = format_rfc2822_date()
        assert formatted  # Just ensure it returns something


class TestEnsureReplySubject:
    """Tests for ensuring reply subject prefix."""

    def test_adds_re_prefix(self) -> None:
        """Test adding Re: prefix."""
        assert ensure_reply_subject("Hello") == "Re: Hello"

    def test_preserves_existing_re(self) -> None:
        """Test preserving existing Re: prefix."""
        assert ensure_reply_subject("Re: Hello") == "Re: Hello"
        assert ensure_reply_subject("RE: Hello") == "RE: Hello"

    def test_empty_subject(self) -> None:
        """Test empty subject."""
        assert ensure_reply_subject("") == "Re: "
        assert ensure_reply_subject(None) == "Re: "


class TestBuildReplyHeaders:
    """Tests for building complete reply headers."""

    def test_basic_reply(self) -> None:
        """Test basic reply headers."""
        headers = build_reply_headers(
            "example.com",
            parent_message_id="<parent@example.com>",
        )
        assert isinstance(headers, OutboundHeaders)
        assert "@example.com>" in headers.message_id
        assert headers.in_reply_to == "<parent@example.com>"
        assert headers.date

    def test_with_parent_refs(self) -> None:
        """Test with parent references."""
        headers = build_reply_headers(
            "example.com",
            parent_message_id="<parent@example.com>",
            parent_references=["<ref1@example.com>"],
        )
        assert headers.references
        assert "<ref1@example.com>" in headers.references
        assert "<parent@example.com>" in headers.references

    def test_to_dict(self) -> None:
        """Test conversion to dict."""
        headers = build_reply_headers(
            "example.com",
            parent_message_id="<parent@example.com>",
        )
        d = headers.to_dict()
        assert "Message-ID" in d
        assert "Date" in d
        assert "In-Reply-To" in d
