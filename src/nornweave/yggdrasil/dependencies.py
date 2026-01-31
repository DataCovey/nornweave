"""Dependency injection (storage, provider). Placeholder."""

from nornweave.core.interfaces import StorageInterface, EmailProvider


def get_storage() -> StorageInterface:
    """Return configured storage adapter. Placeholder."""
    raise NotImplementedError("get_storage")


def get_email_provider() -> EmailProvider:
    """Return configured email provider. Placeholder."""
    raise NotImplementedError("get_email_provider")
