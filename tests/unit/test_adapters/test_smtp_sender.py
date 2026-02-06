"""Unit tests for SmtpSender.send_email().

Tests message building, TLS mode selection, threading headers, CC/BCC handling,
attachments, HTML body, and Markdown conversion — all with aiosmtplib mocked.
"""

import base64
import sys
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

if TYPE_CHECKING:
    from email.message import EmailMessage

import pytest

from nornweave.adapters.smtp_imap import SmtpSender
from nornweave.models.attachment import SendAttachment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _sender(port: int = 587, use_tls: bool = True) -> SmtpSender:
    return SmtpSender(
        host="smtp.test.com",
        port=port,
        username="user@test.com",
        password="secret",
        use_tls=use_tls,
    )


def _mock_aiosmtplib() -> MagicMock:
    """Create a mock aiosmtplib module with send() and SMTPException."""
    mock = MagicMock()
    mock.send = AsyncMock()
    mock.SMTPException = type("SMTPException", (Exception,), {})
    return mock


def _last_send_kwargs(mock_mod: MagicMock) -> dict:
    """Return the keyword arguments from the last aiosmtplib.send() call."""
    return mock_mod.send.call_args.kwargs


def _last_sent_message(mock_mod: MagicMock) -> EmailMessage:
    """Return the EmailMessage passed to the last aiosmtplib.send() call."""
    return mock_mod.send.call_args.args[0]


# ===========================================================================
# Basic send
# ===========================================================================
@pytest.mark.unit
class TestSmtpSenderBasicSend:
    """Basic send_email() tests."""

    @pytest.mark.asyncio
    async def test_returns_message_id(self) -> None:
        sender = _sender()
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            result = await sender.send_email(
                to=["to@test.com"],
                subject="Hello",
                body="World",
                from_address="from@test.com",
                message_id="<test-123@test.com>",
            )
        assert result == "<test-123@test.com>"

    @pytest.mark.asyncio
    async def test_generates_message_id_when_not_provided(self) -> None:
        sender = _sender()
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            result = await sender.send_email(
                to=["to@test.com"],
                subject="Hello",
                body="World",
                from_address="from@test.com",
            )
        assert result.startswith("<") and result.endswith(">")

    @pytest.mark.asyncio
    async def test_calls_aiosmtplib_send(self) -> None:
        sender = _sender()
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            await sender.send_email(
                to=["to@test.com"],
                subject="Test",
                body="Body",
                from_address="from@test.com",
            )
        mock.send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_message_has_core_headers(self) -> None:
        sender = _sender()
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            await sender.send_email(
                to=["to@test.com"],
                subject="Subject Line",
                body="Body",
                from_address="from@test.com",
                message_id="<core-headers@test.com>",
            )
        msg = _last_sent_message(mock)
        assert msg["From"] == "from@test.com"
        assert msg["To"] == "to@test.com"
        assert msg["Subject"] == "Subject Line"
        assert msg["Message-ID"] == "<core-headers@test.com>"
        assert msg["Date"] is not None

    @pytest.mark.asyncio
    async def test_body_has_plain_and_html(self) -> None:
        sender = _sender()
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            await sender.send_email(
                to=["to@test.com"],
                subject="Test",
                body="Plain text body",
                from_address="from@test.com",
            )
        msg = _last_sent_message(mock)
        body = msg.get_body(preferencelist=("plain",))
        assert body is not None
        assert "Plain text body" in str(body.get_content())


# ===========================================================================
# TLS modes
# ===========================================================================
@pytest.mark.unit
class TestSmtpSenderTlsModes:
    """TLS/STARTTLS mode selection."""

    @pytest.mark.asyncio
    async def test_starttls_on_port_587(self) -> None:
        sender = _sender(port=587, use_tls=True)
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            await sender.send_email(
                to=["to@test.com"], subject="T", body="B", from_address="f@t.com"
            )
        kw = _last_send_kwargs(mock)
        assert kw["start_tls"] is True
        assert kw["use_tls"] is False

    @pytest.mark.asyncio
    async def test_implicit_tls_on_port_465(self) -> None:
        sender = _sender(port=465, use_tls=True)
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            await sender.send_email(
                to=["to@test.com"], subject="T", body="B", from_address="f@t.com"
            )
        kw = _last_send_kwargs(mock)
        assert kw["use_tls"] is True
        assert kw["start_tls"] is False

    @pytest.mark.asyncio
    async def test_no_tls_when_disabled(self) -> None:
        sender = _sender(port=25, use_tls=False)
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            await sender.send_email(
                to=["to@test.com"], subject="T", body="B", from_address="f@t.com"
            )
        kw = _last_send_kwargs(mock)
        assert kw["use_tls"] is False
        assert kw["start_tls"] is False


# ===========================================================================
# Threading headers
# ===========================================================================
@pytest.mark.unit
class TestSmtpSenderThreadingHeaders:
    """In-Reply-To / References headers."""

    @pytest.mark.asyncio
    async def test_in_reply_to_header(self) -> None:
        sender = _sender()
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            await sender.send_email(
                to=["to@test.com"],
                subject="Re: Test",
                body="Reply",
                from_address="from@test.com",
                in_reply_to="<parent@test.com>",
            )
        msg = _last_sent_message(mock)
        assert msg["In-Reply-To"] == "<parent@test.com>"

    @pytest.mark.asyncio
    async def test_references_header(self) -> None:
        sender = _sender()
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            await sender.send_email(
                to=["to@test.com"],
                subject="Re: Test",
                body="Reply",
                from_address="from@test.com",
                references=["<first@test.com>", "<second@test.com>"],
            )
        msg = _last_sent_message(mock)
        assert msg["References"] == "<first@test.com> <second@test.com>"


# ===========================================================================
# CC / BCC
# ===========================================================================
@pytest.mark.unit
class TestSmtpSenderCcBcc:
    """CC and BCC recipient handling."""

    @pytest.mark.asyncio
    async def test_cc_in_header(self) -> None:
        sender = _sender()
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            await sender.send_email(
                to=["to@test.com"],
                subject="T",
                body="B",
                from_address="f@t.com",
                cc=["cc1@test.com", "cc2@test.com"],
            )
        msg = _last_sent_message(mock)
        assert "cc1@test.com" in msg["Cc"]
        assert "cc2@test.com" in msg["Cc"]

    @pytest.mark.asyncio
    async def test_bcc_not_in_header(self) -> None:
        sender = _sender()
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            await sender.send_email(
                to=["to@test.com"],
                subject="T",
                body="B",
                from_address="f@t.com",
                bcc=["secret@test.com"],
            )
        msg = _last_sent_message(mock)
        assert msg["Bcc"] is None

    @pytest.mark.asyncio
    async def test_all_recipients_in_envelope(self) -> None:
        sender = _sender()
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            await sender.send_email(
                to=["to@test.com"],
                subject="T",
                body="B",
                from_address="f@t.com",
                cc=["cc@test.com"],
                bcc=["bcc@test.com"],
            )
        kw = _last_send_kwargs(mock)
        assert "to@test.com" in kw["recipients"]
        assert "cc@test.com" in kw["recipients"]
        assert "bcc@test.com" in kw["recipients"]


# ===========================================================================
# Attachments
# ===========================================================================
@pytest.mark.unit
class TestSmtpSenderAttachments:
    """Attachment handling."""

    @pytest.mark.asyncio
    async def test_attachment_added_to_message(self) -> None:
        sender = _sender()
        content_b64 = base64.b64encode(b"file contents").decode()
        att = SendAttachment(
            filename="report.txt",
            content_type="text/plain",
            content=content_b64,
        )
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            await sender.send_email(
                to=["to@test.com"],
                subject="T",
                body="See attached",
                from_address="f@t.com",
                attachments=[att],
            )
        msg = _last_sent_message(mock)
        attachment_parts = [p for p in msg.walk() if p.get_filename() == "report.txt"]
        assert len(attachment_parts) == 1
        assert attachment_parts[0].get_content_type() == "text/plain"

    @pytest.mark.asyncio
    async def test_inline_attachment_has_cid(self) -> None:
        sender = _sender()
        content_b64 = base64.b64encode(b"\x89PNG").decode()
        att = SendAttachment(
            filename="logo.png",
            content_type="image/png",
            content=content_b64,
            content_disposition="inline",
            content_id="<logo-cid>",
        )
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            await sender.send_email(
                to=["to@test.com"],
                subject="T",
                body="Inline image",
                from_address="f@t.com",
                attachments=[att],
            )
        msg = _last_sent_message(mock)
        inline_parts = [p for p in msg.walk() if p.get_filename() == "logo.png"]
        assert len(inline_parts) == 1
        disp = str(inline_parts[0].get("Content-Disposition", ""))
        assert "inline" in disp.lower()


# ===========================================================================
# HTML body and Markdown conversion
# ===========================================================================
@pytest.mark.unit
class TestSmtpSenderHtmlMarkdown:
    """HTML body and Markdown conversion tests."""

    @pytest.mark.asyncio
    async def test_explicit_html_body(self) -> None:
        sender = _sender()
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            await sender.send_email(
                to=["to@test.com"],
                subject="T",
                body="Plain text",
                from_address="f@t.com",
                html_body="<h1>HTML Body</h1>",
            )
        msg = _last_sent_message(mock)
        html_body = msg.get_body(preferencelist=("html",))
        assert html_body is not None
        assert "<h1>HTML Body</h1>" in str(html_body.get_content())

    @pytest.mark.asyncio
    async def test_markdown_converted_when_no_html(self) -> None:
        sender = _sender()
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            await sender.send_email(
                to=["to@test.com"],
                subject="T",
                body="**bold text**",
                from_address="f@t.com",
            )
        msg = _last_sent_message(mock)
        html_body = msg.get_body(preferencelist=("html",))
        assert html_body is not None
        content = str(html_body.get_content())
        assert "<strong>bold text</strong>" in content


# ===========================================================================
# SMTP failure
# ===========================================================================
@pytest.mark.unit
class TestSmtpSenderFailure:
    """SMTP error propagation."""

    @pytest.mark.asyncio
    async def test_smtp_exception_propagated(self) -> None:
        sender = _sender()
        mock = _mock_aiosmtplib()
        mock.send = AsyncMock(side_effect=mock.SMTPException("Connection refused"))
        with (
            patch.dict(sys.modules, {"aiosmtplib": mock}),
            pytest.raises(Exception, match="Connection refused"),
        ):
            await sender.send_email(
                to=["to@test.com"],
                subject="T",
                body="B",
                from_address="f@t.com",
            )


# ===========================================================================
# Authentication
# ===========================================================================
@pytest.mark.unit
class TestSmtpSenderAuth:
    """SMTP authentication."""

    @pytest.mark.asyncio
    async def test_credentials_passed_to_aiosmtplib(self) -> None:
        sender = _sender()
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            await sender.send_email(
                to=["to@test.com"], subject="T", body="B", from_address="f@t.com"
            )
        kw = _last_send_kwargs(mock)
        assert kw["username"] == "user@test.com"
        assert kw["password"] == "secret"
        assert kw["hostname"] == "smtp.test.com"
        assert kw["port"] == 587

    @pytest.mark.asyncio
    async def test_empty_credentials_passed_as_none(self) -> None:
        sender = SmtpSender(host="smtp.test.com", port=587, username="", password="")
        mock = _mock_aiosmtplib()
        with patch.dict(sys.modules, {"aiosmtplib": mock}):
            await sender.send_email(
                to=["to@test.com"], subject="T", body="B", from_address="f@t.com"
            )
        kw = _last_send_kwargs(mock)
        assert kw["username"] is None
        assert kw["password"] is None
