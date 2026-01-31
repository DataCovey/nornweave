"""Custom exception hierarchy for NornWeave."""


class NornWeaveError(Exception):
    """Base exception for all NornWeave errors."""

    pass


class NotFoundError(NornWeaveError):
    """Resource not found (inbox, thread, message)."""

    pass


class ValidationError(NornWeaveError):
    """Invalid input or state."""

    pass


class ProviderError(NornWeaveError):
    """Email or storage provider error."""

    pass
