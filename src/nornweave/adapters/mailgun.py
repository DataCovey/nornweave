"""Mailgun email provider adapter."""

from typing import Any

from nornweave.core.interfaces import EmailProvider, InboundMessage


class MailgunAdapter(EmailProvider):
    """Mailgun implementation of EmailProvider."""

    def __init__(self, api_key: str, domain: str, api_url: str = "https://api.mailgun.net") -> None:
        """Initialize Mailgun adapter.

        Args:
            api_key: Mailgun API key
            domain: Mailgun domain (e.g., mail.example.com)
            api_url: Mailgun API URL (default: https://api.mailgun.net)
        """
        self._api_key = api_key
        self._domain = domain
        self._api_url = api_url

    async def send_email(
        self,
        to: list[str],
        subject: str,
        body: str,
        *,
        from_address: str,
        reply_to: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        """Send email via Mailgun API.

        TODO: Implement actual Mailgun API call using httpx.
        """
        raise NotImplementedError("MailgunAdapter.send_email")

    def parse_inbound_webhook(self, payload: dict[str, Any]) -> InboundMessage:
        """Parse Mailgun inbound webhook payload.

        TODO: Implement Mailgun webhook payload parsing.
        """
        raise NotImplementedError("MailgunAdapter.parse_inbound_webhook")
