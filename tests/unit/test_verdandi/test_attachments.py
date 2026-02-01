"""Unit tests for attachment parsing and validation."""

from nornweave.core.interfaces import InboundAttachment
from nornweave.models.attachment import AttachmentDisposition
from nornweave.verdandi.attachments import (
    BLOCKED_EXTENSIONS,
    MAX_ATTACHMENT_COUNT,
    MAX_SINGLE_ATTACHMENT_SIZE,
    MAX_TOTAL_ATTACHMENT_SIZE,
    build_content_id_to_filename_map,
    guess_content_type,
    normalize_content_id,
    parse_attachment_info_json,
    parse_content_id_map,
    resolve_cid_urls_in_html,
    validate_attachments,
)


class TestNormalizeContentId:
    """Tests for Content-ID normalization."""

    def test_with_brackets(self) -> None:
        """Test Content-ID with angle brackets."""
        assert normalize_content_id("<image001>") == "image001"

    def test_without_brackets(self) -> None:
        """Test Content-ID without brackets."""
        assert normalize_content_id("image001") == "image001"

    def test_whitespace(self) -> None:
        """Test Content-ID with whitespace."""
        assert normalize_content_id("  <image001>  ") == "image001"

    def test_empty(self) -> None:
        """Test empty Content-ID."""
        assert normalize_content_id("") is None
        assert normalize_content_id(None) is None


class TestParseContentIdMap:
    """Tests for parsing content-id-map JSON."""

    def test_json_string(self) -> None:
        """Test parsing JSON string."""
        result = parse_content_id_map('{"ii_abc123": "attachment1"}')
        assert result == {"ii_abc123": "attachment1"}

    def test_dict_input(self) -> None:
        """Test with dict input."""
        result = parse_content_id_map({"ii_abc123": "attachment1"})
        assert result == {"ii_abc123": "attachment1"}

    def test_empty(self) -> None:
        """Test empty input."""
        assert parse_content_id_map("") == {}
        assert parse_content_id_map(None) == {}
        assert parse_content_id_map("{}") == {}

    def test_invalid_json(self) -> None:
        """Test invalid JSON."""
        assert parse_content_id_map("not json") == {}


class TestBuildContentIdToFilenameMap:
    """Tests for building Content-ID to filename mapping."""

    def test_with_content_ids(self) -> None:
        """Test mapping with Content-IDs."""
        attachments = [
            InboundAttachment(
                filename="logo.png",
                content_type="image/png",
                content=b"",
                size_bytes=0,
                disposition=AttachmentDisposition.INLINE,
                content_id="ii_logo123",
            ),
            InboundAttachment(
                filename="doc.pdf",
                content_type="application/pdf",
                content=b"",
                size_bytes=0,
                disposition=AttachmentDisposition.ATTACHMENT,
                content_id=None,
            ),
        ]
        mapping = build_content_id_to_filename_map(attachments)
        assert mapping == {"ii_logo123": "logo.png"}

    def test_empty_attachments(self) -> None:
        """Test with no attachments."""
        assert build_content_id_to_filename_map([]) == {}


class TestValidateAttachments:
    """Tests for attachment validation."""

    def test_valid_attachments(self) -> None:
        """Test valid attachments pass validation."""
        attachments = [
            InboundAttachment(
                filename="document.pdf",
                content_type="application/pdf",
                content=b"test content",
                size_bytes=100,
            ),
        ]
        result = validate_attachments(attachments)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_too_many_attachments(self) -> None:
        """Test too many attachments."""
        attachments = [
            InboundAttachment(
                filename=f"file{i}.txt",
                content_type="text/plain",
                content=b"test",
                size_bytes=4,
            )
            for i in range(MAX_ATTACHMENT_COUNT + 5)
        ]
        result = validate_attachments(attachments)
        assert result.valid is False
        assert any("Too many" in e for e in result.errors)

    def test_single_file_too_large(self) -> None:
        """Test single file too large."""
        attachments = [
            InboundAttachment(
                filename="large.bin",
                content_type="application/octet-stream",
                content=b"x",
                size_bytes=MAX_SINGLE_ATTACHMENT_SIZE + 1,
            ),
        ]
        result = validate_attachments(attachments)
        assert result.valid is False
        assert any("too large" in e for e in result.errors)

    def test_total_size_too_large(self) -> None:
        """Test total size too large."""
        # Create attachments that individually pass but together exceed limit
        size_per_file = MAX_SINGLE_ATTACHMENT_SIZE - 1
        num_files = (MAX_TOTAL_ATTACHMENT_SIZE // size_per_file) + 2

        attachments = [
            InboundAttachment(
                filename=f"file{i}.bin",
                content_type="application/octet-stream",
                content=b"x",
                size_bytes=size_per_file,
            )
            for i in range(num_files)
        ]
        result = validate_attachments(attachments, max_count=50)  # Override count limit
        assert result.valid is False
        assert any("Total attachment size" in e for e in result.errors)

    def test_blocked_extension(self) -> None:
        """Test blocked file extension."""
        attachments = [
            InboundAttachment(
                filename="virus.exe",
                content_type="application/x-msdownload",
                content=b"",
                size_bytes=0,
            ),
        ]
        result = validate_attachments(attachments)
        assert result.valid is False
        assert any("Blocked file type" in e for e in result.errors)

    def test_content_type_mismatch_warning(self) -> None:
        """Test content-type mismatch produces warning."""
        attachments = [
            InboundAttachment(
                filename="image.png",
                content_type="application/pdf",  # Wrong type
                content=b"",
                size_bytes=0,
            ),
        ]
        result = validate_attachments(attachments)
        # This should produce a warning, not an error
        assert any("mismatch" in w for w in result.warnings)


class TestResolveCidUrls:
    """Tests for resolving cid: URLs in HTML."""

    def test_replace_cid(self) -> None:
        """Test cid: URL replacement."""
        html = '<img src="cid:image001" alt="Logo">'
        attachments = [
            InboundAttachment(
                filename="logo.png",
                content_type="image/png",
                content=b"",
                size_bytes=0,
                disposition=AttachmentDisposition.INLINE,
                content_id="image001",
            ),
        ]
        result = resolve_cid_urls_in_html(html, attachments)
        assert "cid:image001" not in result
        assert "/v1/attachments/" in result

    def test_unmatched_cid(self) -> None:
        """Test unmatched cid: is preserved."""
        html = '<img src="cid:unknown" alt="Missing">'
        result = resolve_cid_urls_in_html(html, [])
        assert "cid:unknown" in result

    def test_empty_html(self) -> None:
        """Test empty HTML."""
        assert resolve_cid_urls_in_html("", []) == ""


class TestParseAttachmentInfoJson:
    """Tests for parsing SendGrid attachment-info JSON."""

    def test_json_string(self) -> None:
        """Test parsing JSON string."""
        json_str = """{"attachment1": {
            "filename": "image.jpg",
            "type": "image/jpeg",
            "content-id": "ii_abc123"
        }}"""
        result = parse_attachment_info_json(json_str)
        assert "attachment1" in result
        assert result["attachment1"]["filename"] == "image.jpg"

    def test_dict_input(self) -> None:
        """Test dict input."""
        data = {"attachment1": {"filename": "doc.pdf"}}
        result = parse_attachment_info_json(data)
        assert result == data

    def test_empty(self) -> None:
        """Test empty input."""
        assert parse_attachment_info_json("") == {}
        assert parse_attachment_info_json(None) == {}


class TestGuessContentType:
    """Tests for content type guessing."""

    def test_common_types(self) -> None:
        """Test common file types."""
        assert guess_content_type("document.pdf") == "application/pdf"
        assert guess_content_type("image.png") == "image/png"
        assert guess_content_type("photo.jpg") == "image/jpeg"
        assert guess_content_type("data.json") == "application/json"

    def test_unknown_extension(self) -> None:
        """Test truly unknown extension returns default."""
        # Use an extension that has no known MIME type
        assert guess_content_type("file.unknown12345") == "application/octet-stream"

    def test_custom_default(self) -> None:
        """Test custom default type for unknown extension."""
        assert guess_content_type("file.unknown12345", default="text/plain") == "text/plain"


class TestBlockedExtensions:
    """Tests for blocked extension list."""

    def test_common_dangerous_extensions(self) -> None:
        """Test that common dangerous extensions are blocked."""
        assert ".exe" in BLOCKED_EXTENSIONS
        assert ".bat" in BLOCKED_EXTENSIONS
        assert ".cmd" in BLOCKED_EXTENSIONS
        assert ".vbs" in BLOCKED_EXTENSIONS
        assert ".ps1" in BLOCKED_EXTENSIONS

    def test_safe_extensions_not_blocked(self) -> None:
        """Test that safe extensions are not blocked."""
        assert ".pdf" not in BLOCKED_EXTENSIONS
        assert ".jpg" not in BLOCKED_EXTENSIONS
        assert ".docx" not in BLOCKED_EXTENSIONS
