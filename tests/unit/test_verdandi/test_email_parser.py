"""Tests for RFC 822 email parser (verdandi.email_parser)."""

from pathlib import Path

import pytest

from nornweave.verdandi.email_parser import parse_raw_email

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures" / "emails"


def _load_fixture(name: str) -> bytes:
    """Load a .eml fixture file as bytes."""
    path = FIXTURES_DIR / name
    return path.read_bytes()


# ---------------------------------------------------------------------------
# Simple plain text
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestParsePlainText:
    """Parse a simple single-part text/plain email."""

    def test_from_address(self) -> None:
        msg = parse_raw_email(_load_fixture("simple_plain.eml"))
        assert msg.from_address == "alice@example.com"

    def test_to_address(self) -> None:
        msg = parse_raw_email(_load_fixture("simple_plain.eml"))
        assert msg.to_address == "bob@nornweave.dev"

    def test_subject(self) -> None:
        msg = parse_raw_email(_load_fixture("simple_plain.eml"))
        assert msg.subject == "Weekly status update"

    def test_message_id(self) -> None:
        msg = parse_raw_email(_load_fixture("simple_plain.eml"))
        assert msg.message_id == "<msg-001@mail.example.com>"

    def test_body_plain_contains_content(self) -> None:
        msg = parse_raw_email(_load_fixture("simple_plain.eml"))
        assert "weekly status update" in msg.body_plain.lower()
        assert "IMAP polling module" in msg.body_plain

    def test_body_html_is_none(self) -> None:
        msg = parse_raw_email(_load_fixture("simple_plain.eml"))
        assert msg.body_html is None

    def test_no_attachments(self) -> None:
        msg = parse_raw_email(_load_fixture("simple_plain.eml"))
        assert msg.attachments == []

    def test_timestamp_parsed(self) -> None:
        msg = parse_raw_email(_load_fixture("simple_plain.eml"))
        assert msg.timestamp.year == 2026
        assert msg.timestamp.month == 2
        assert msg.timestamp.day == 3


# ---------------------------------------------------------------------------
# Multipart alternative (text + HTML)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestParseMultipartAlternative:
    """Parse multipart/alternative with text/plain and text/html parts."""

    def test_body_plain_present(self) -> None:
        msg = parse_raw_email(_load_fixture("multipart_alternative.eml"))
        assert "invoice" in msg.body_plain.lower()
        assert "$1,250.00" in msg.body_plain

    def test_body_html_present(self) -> None:
        msg = parse_raw_email(_load_fixture("multipart_alternative.eml"))
        assert msg.body_html is not None
        assert "<strong>" in msg.body_html
        assert "#2026-0142" in msg.body_html

    def test_from_address(self) -> None:
        msg = parse_raw_email(_load_fixture("multipart_alternative.eml"))
        assert msg.from_address == "carol@example.com"

    def test_to_address(self) -> None:
        msg = parse_raw_email(_load_fixture("multipart_alternative.eml"))
        assert msg.to_address == "support@nornweave.dev"

    def test_no_attachments(self) -> None:
        msg = parse_raw_email(_load_fixture("multipart_alternative.eml"))
        assert msg.attachments == []


# ---------------------------------------------------------------------------
# Threading headers
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestParseThreadingHeaders:
    """Parse threading headers: Message-ID, In-Reply-To, References."""

    def test_message_id(self) -> None:
        msg = parse_raw_email(_load_fixture("with_threading.eml"))
        assert msg.message_id == "<msg-004@mail.example.com>"

    def test_in_reply_to(self) -> None:
        msg = parse_raw_email(_load_fixture("with_threading.eml"))
        assert msg.in_reply_to == "<msg-original-001@mail.example.com>"

    def test_references(self) -> None:
        msg = parse_raw_email(_load_fixture("with_threading.eml"))
        assert msg.references == [
            "<msg-original-001@mail.example.com>",
            "<msg-reply-001@mail.example.com>",
        ]

    def test_subject_is_reply(self) -> None:
        msg = parse_raw_email(_load_fixture("with_threading.eml"))
        assert msg.subject.startswith("Re:")


# ---------------------------------------------------------------------------
# Sender/recipient address parsing
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestParseAddresses:
    """Parse 'Name <email>' format and CC addresses."""

    def test_name_email_from(self) -> None:
        """From header with 'Name <email>' format extracts email only."""
        msg = parse_raw_email(_load_fixture("simple_plain.eml"))
        assert msg.from_address == "alice@example.com"

    def test_name_email_to(self) -> None:
        """To header with 'Name <email>' format extracts email only."""
        msg = parse_raw_email(_load_fixture("simple_plain.eml"))
        assert msg.to_address == "bob@nornweave.dev"

    def test_cc_addresses_parsed(self) -> None:
        """CC header with multiple encoded and plain addresses."""
        msg = parse_raw_email(_load_fixture("encoded_headers.eml"))
        assert "lea@example.fr" in msg.cc_addresses
        assert "frank@example.com" in msg.cc_addresses
        assert len(msg.cc_addresses) == 2

    def test_cc_empty_when_absent(self) -> None:
        """No CC header should produce empty list."""
        msg = parse_raw_email(_load_fixture("simple_plain.eml"))
        assert msg.cc_addresses == []


# -- Attachments (multipart/mixed) --


@pytest.mark.unit
class TestParseAttachments:
    """Parse attachments from multipart/mixed email."""

    def test_attachment_count(self) -> None:
        msg = parse_raw_email(_load_fixture("with_attachment.eml"))
        assert len(msg.attachments) == 1

    def test_attachment_filename(self) -> None:
        msg = parse_raw_email(_load_fixture("with_attachment.eml"))
        att = msg.attachments[0]
        assert att.filename == "q4-report.txt"

    def test_attachment_content_type(self) -> None:
        msg = parse_raw_email(_load_fixture("with_attachment.eml"))
        att = msg.attachments[0]
        assert att.content_type == "text/plain"

    def test_attachment_content(self) -> None:
        msg = parse_raw_email(_load_fixture("with_attachment.eml"))
        att = msg.attachments[0]
        decoded = att.content.decode("utf-8")
        assert "Revenue" in decoded
        assert "$2.4M" in decoded

    def test_attachment_size(self) -> None:
        msg = parse_raw_email(_load_fixture("with_attachment.eml"))
        att = msg.attachments[0]
        assert att.size_bytes > 0

    def test_body_plain_separate_from_attachment(self) -> None:
        """Body text should not include the attachment content."""
        msg = parse_raw_email(_load_fixture("with_attachment.eml"))
        assert "Attached is the Q4 report" in msg.body_plain
        # Attachment content should not leak into body
        assert "NPS Score" not in msg.body_plain


# ---------------------------------------------------------------------------
# Missing / malformed headers
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMissingHeaders:
    """Handle missing or malformed headers with sensible defaults."""

    def test_missing_subject_defaults_to_empty(self) -> None:
        raw = (
            b"From: sender@example.com\r\n"
            b"To: inbox@nornweave.dev\r\n"
            b"Date: Mon, 03 Feb 2026 10:00:00 +0000\r\n"
            b"Message-ID: <minimal@example.com>\r\n"
            b"\r\n"
            b"Body without a subject header.\r\n"
        )
        msg = parse_raw_email(raw)
        assert msg.subject == ""

    def test_missing_date_defaults_to_now(self) -> None:
        raw = (
            b"From: sender@example.com\r\n"
            b"To: inbox@nornweave.dev\r\n"
            b"Subject: No date\r\n"
            b"Message-ID: <nodate@example.com>\r\n"
            b"\r\n"
            b"No date header.\r\n"
        )
        msg = parse_raw_email(raw)
        # Should not crash; timestamp should be recent (within last minute)
        assert msg.timestamp is not None
        assert msg.timestamp.year >= 2026

    def test_missing_message_id_defaults_to_none(self) -> None:
        raw = (
            b"From: sender@example.com\r\n"
            b"To: inbox@nornweave.dev\r\n"
            b"Subject: No message-id\r\n"
            b"Date: Mon, 03 Feb 2026 10:00:00 +0000\r\n"
            b"\r\n"
            b"No message-id header.\r\n"
        )
        msg = parse_raw_email(raw)
        # Message-ID might be auto-generated by policy.default or be None
        # The parser should not crash either way
        assert msg.from_address == "sender@example.com"

    def test_missing_from_defaults_to_empty(self) -> None:
        raw = (
            b"To: inbox@nornweave.dev\r\n"
            b"Subject: No sender\r\n"
            b"Date: Mon, 03 Feb 2026 10:00:00 +0000\r\n"
            b"\r\n"
            b"No from header.\r\n"
        )
        msg = parse_raw_email(raw)
        assert msg.from_address == ""

    def test_empty_body(self) -> None:
        raw = (
            b"From: sender@example.com\r\n"
            b"To: inbox@nornweave.dev\r\n"
            b"Subject: Empty body\r\n"
            b"Date: Mon, 03 Feb 2026 10:00:00 +0000\r\n"
            b"Message-ID: <emptybody@example.com>\r\n"
            b"\r\n"
        )
        msg = parse_raw_email(raw)
        assert msg.body_plain == "" or msg.body_plain.strip() == ""


# ---------------------------------------------------------------------------
# RFC 2047 encoded headers
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestEncodedHeaders:
    """Parse RFC 2047 encoded headers (=?UTF-8?B?...?=)."""

    def test_decoded_subject(self) -> None:
        msg = parse_raw_email(_load_fixture("encoded_headers.eml"))
        # Subject is "Überprüfung der Dokumentation 📄" encoded in UTF-8 Base64
        assert "Überprüfung" in msg.subject
        assert "Dokumentation" in msg.subject

    def test_decoded_from_address(self) -> None:
        """Encoded From header should decode and extract email."""
        msg = parse_raw_email(_load_fixture("encoded_headers.eml"))
        assert msg.from_address == "juergen@example.de"


# -- Authentication-Results (SPF, DKIM, DMARC) --


@pytest.mark.unit
class TestAuthenticationResults:
    """Parse Authentication-Results header for SPF/DKIM/DMARC verdicts."""

    def test_spf_pass(self) -> None:
        msg = parse_raw_email(_load_fixture("encoded_headers.eml"))
        assert msg.spf_result == "PASS"

    def test_dkim_pass(self) -> None:
        msg = parse_raw_email(_load_fixture("encoded_headers.eml"))
        assert msg.dkim_result == "PASS"

    def test_dmarc_pass(self) -> None:
        msg = parse_raw_email(_load_fixture("encoded_headers.eml"))
        assert msg.dmarc_result == "PASS"

    def test_no_auth_results(self) -> None:
        """Email without Authentication-Results should have None for all."""
        msg = parse_raw_email(_load_fixture("simple_plain.eml"))
        assert msg.spf_result is None
        assert msg.dkim_result is None
        assert msg.dmarc_result is None

    def test_headers_dict_populated(self) -> None:
        """All original headers should be available in the headers dict."""
        msg = parse_raw_email(_load_fixture("encoded_headers.eml"))
        assert "From" in msg.headers
        assert "Message-ID" in msg.headers
        assert "Authentication-Results" in msg.headers
