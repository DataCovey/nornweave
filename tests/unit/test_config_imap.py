"""Tests for IMAP/SMTP-related config validation."""

import pytest
from pydantic import ValidationError

from nornweave.core.config import Settings


@pytest.mark.unit
class TestImapConfigValidation:
    """Validate IMAP configuration constraints in Settings."""

    def test_delete_after_fetch_requires_mark_as_read(self) -> None:
        """IMAP_DELETE_AFTER_FETCH=true with IMAP_MARK_AS_READ=false must raise."""
        with pytest.raises(ValidationError, match="IMAP_DELETE_AFTER_FETCH"):
            Settings(
                IMAP_DELETE_AFTER_FETCH=True,
                IMAP_MARK_AS_READ=False,
                DATABASE_URL="sqlite+aiosqlite:///test.db",
                DB_DRIVER="sqlite",
            )

    def test_delete_after_fetch_with_mark_as_read_is_valid(self) -> None:
        """IMAP_DELETE_AFTER_FETCH=true with IMAP_MARK_AS_READ=true should be fine."""
        settings = Settings(
            IMAP_DELETE_AFTER_FETCH=True,
            IMAP_MARK_AS_READ=True,
            DATABASE_URL="sqlite+aiosqlite:///test.db",
            DB_DRIVER="sqlite",
        )
        assert settings.imap_delete_after_fetch is True
        assert settings.imap_mark_as_read is True

    def test_email_provider_imap_smtp_accepted(self) -> None:
        """EMAIL_PROVIDER='imap-smtp' should be a valid choice."""
        settings = Settings(
            EMAIL_PROVIDER="imap-smtp",
            DATABASE_URL="sqlite+aiosqlite:///test.db",
            DB_DRIVER="sqlite",
        )
        assert settings.email_provider == "imap-smtp"

    def test_default_imap_settings(self) -> None:
        """Default IMAP settings should have safe values."""
        settings = Settings(
            DATABASE_URL="sqlite+aiosqlite:///test.db",
            DB_DRIVER="sqlite",
        )
        assert settings.imap_mark_as_read is True
        assert settings.imap_delete_after_fetch is False
        assert settings.imap_port == 993
        assert settings.imap_use_ssl is True
        assert settings.imap_poll_interval == 60
        assert settings.imap_mailbox == "INBOX"
