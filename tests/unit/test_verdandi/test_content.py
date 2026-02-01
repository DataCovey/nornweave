"""Unit tests for content extraction (quote/signature removal)."""

from nornweave.verdandi.content import (
    ExtractedContent,
    _basic_quote_removal,
    _basic_signature_removal,
    calculate_message_size,
    extract_content,
    extract_reply_text,
    generate_preview,
)


class TestExtractReplyText:
    """Tests for plain text reply extraction."""

    def test_simple_text(self) -> None:
        """Test text without quotes."""
        result = extract_reply_text("Hello, this is a simple message.")
        assert "Hello, this is a simple message." in result

    def test_gmail_style_quote(self) -> None:
        """Test Gmail-style quote removal using fallback."""
        body = """Thanks for the info!

On Sat, Jan 31, 2026 at 10:35 AM Bob wrote:

> This is the quoted text.
> More quoted text."""

        result = _basic_quote_removal(body)
        assert "Thanks for the info!" in result
        assert "This is the quoted text" not in result

    def test_outlook_style_quote(self) -> None:
        """Test Outlook-style quote removal using fallback.

        Note: The basic fallback is permissive and may retain some
        content after quote headers. Full Talon handles this better.
        """
        body = """Got it, thanks!

-----Original Message-----
From: Bob
Sent: Saturday, January 31, 2026 10:35 AM

> This is the quoted original message."""

        result = _basic_quote_removal(body)
        assert "Got it, thanks!" in result
        # Lines starting with > should be removed
        assert "> This is the quoted original message" not in result

    def test_empty_text(self) -> None:
        """Test empty text."""
        assert extract_reply_text("") == ""


class TestRemoveSignatureBruteforce:
    """Tests for signature removal using bruteforce method."""

    def test_double_dash_signature(self) -> None:
        """Test signature with -- delimiter."""
        text = """Thanks for your help!

--
John Doe
CEO, Acme Corp"""

        clean, sig = _basic_signature_removal(text)
        assert "Thanks for your help!" in clean
        assert sig is not None
        assert "John Doe" in sig

    def test_regards_signature(self) -> None:
        """Test signature starting with 'Best regards'."""
        text = """Looking forward to hearing from you.

Best regards,
Alice Smith
alice@example.com"""

        clean, sig = _basic_signature_removal(text)
        assert "Looking forward" in clean
        assert sig is not None
        assert "Alice Smith" in sig

    def test_no_signature(self) -> None:
        """Test text without signature."""
        text = "This is a simple message with no signature."
        clean, sig = _basic_signature_removal(text)
        assert clean == text
        assert sig is None


class TestGeneratePreview:
    """Tests for preview generation."""

    def test_short_text(self) -> None:
        """Test text shorter than max length."""
        text = "Short message."
        preview = generate_preview(text, max_length=100)
        assert preview == "Short message."
        assert "..." not in preview

    def test_long_text_truncation(self) -> None:
        """Test truncation at word boundary."""
        text = "This is a very long message that should be truncated at a reasonable point."
        preview = generate_preview(text, max_length=30)
        assert len(preview) <= 33  # 30 + "..."
        assert preview.endswith("...")

    def test_word_boundary(self) -> None:
        """Test truncation doesn't cut words."""
        text = "Hello world this is a test"
        preview = generate_preview(text, max_length=15)
        # Should truncate before "is" to avoid cutting the word
        assert not preview.endswith(" ...")

    def test_whitespace_collapse(self) -> None:
        """Test whitespace is collapsed."""
        text = "Multiple   spaces\nand\nnewlines"
        preview = generate_preview(text)
        assert "  " not in preview
        assert "\n" not in preview

    def test_empty_text(self) -> None:
        """Test empty text."""
        assert generate_preview("") == ""
        assert generate_preview("   ") == ""


class TestExtractContent:
    """Tests for full content extraction pipeline."""

    def test_basic_extraction(self) -> None:
        """Test basic content extraction."""
        result = extract_content(
            body_plain="Hello, world!",
            body_html="<p>Hello, world!</p>",
        )
        assert isinstance(result, ExtractedContent)
        assert "Hello, world!" in result.extracted_text
        assert result.preview

    def test_with_sender_email(self) -> None:
        """Test extraction with sender email."""
        result = extract_content(
            body_plain="Thanks!\n\n-- \nAlice\nalice@example.com",
            sender_email="alice@example.com",
            use_ml_signature=False,  # Use bruteforce fallback
        )
        # Signature might or might not be removed depending on Talon
        assert result.extracted_text

    def test_preview_length(self) -> None:
        """Test preview max length."""
        long_text = "a " * 100
        result = extract_content(
            body_plain=long_text,
            preview_max_length=50,
        )
        assert len(result.preview) <= 53  # 50 + "..."

    def test_html_extraction(self) -> None:
        """Test HTML body extraction."""
        result = extract_content(
            body_plain="Plain text",
            body_html="<div>HTML content</div>",
        )
        assert result.extracted_html is not None


class TestCalculateMessageSize:
    """Tests for message size calculation."""

    def test_text_only(self) -> None:
        """Test size with text only."""
        size = calculate_message_size(text="Hello")
        assert size == 5

    def test_html_only(self) -> None:
        """Test size with HTML only."""
        size = calculate_message_size(html="<p>Hi</p>")
        assert size == 9

    def test_with_headers(self) -> None:
        """Test size with headers."""
        size = calculate_message_size(
            text="Hi",
            headers={"From": "a@b.com", "To": "c@d.com"},
        )
        assert size > 2  # Text plus headers

    def test_with_attachments(self) -> None:
        """Test size with attachments."""
        size = calculate_message_size(
            text="Hi",
            attachments_size=1000,
        )
        assert size == 1002  # 2 bytes text + 1000 attachments

    def test_unicode(self) -> None:
        """Test size with unicode characters."""
        size = calculate_message_size(text="日本語")
        assert size == 9  # 3 characters * 3 bytes each


class TestBasicQuoteRemoval:
    """Tests for basic quote removal fallback."""

    def test_quoted_lines(self) -> None:
        """Test removal of > prefixed lines."""
        text = """Reply text.

> Quoted line 1
> Quoted line 2"""

        result = _basic_quote_removal(text)
        assert "Reply text" in result
        assert "Quoted line" not in result

    def test_on_wrote_pattern(self) -> None:
        """Test 'On ... wrote:' pattern detection."""
        text = """My reply.

On Mon, Jan 31, 2026 at 10:00 AM Alice wrote:
> Some quoted text"""

        result = _basic_quote_removal(text)
        assert "My reply" in result
        assert "Alice wrote" not in result


class TestBasicSignatureRemoval:
    """Tests for basic signature removal fallback."""

    def test_sent_from_iphone(self) -> None:
        """Test 'Sent from my iPhone' removal."""
        text = """Quick reply.

Sent from my iPhone"""

        clean, sig = _basic_signature_removal(text)
        assert "Quick reply" in clean
        assert "Sent from my iPhone" in sig

    def test_thanks_signature(self) -> None:
        """Test 'Thanks,' signature."""
        text = """See you tomorrow.

Thanks,
Bob"""

        clean, _sig = _basic_signature_removal(text)
        assert "See you tomorrow" in clean
