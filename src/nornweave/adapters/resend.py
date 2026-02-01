"""Resend email provider adapter."""

from typing import TYPE_CHECKING, Any

from nornweave.core.interfaces import EmailProvider, InboundMessage

if TYPE_CHECKING:
    from nornweave.models.attachment import SendAttachment


class ResendAdapter(EmailProvider):
    """Resend implementation of EmailProvider."""

    def __init__(self, api_key: str) -> None:
        """Initialize Resend adapter.

        Args:
            api_key: Resend API key
        """
        self._api_key = api_key

    async def send_email(
        self,
        to: list[str],
        subject: str,
        body: str,
        *,
        from_address: str,
        reply_to: str | None = None,
        headers: dict[str, str] | None = None,
        message_id: str | None = None,
        in_reply_to: str | None = None,
        references: list[str] | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[SendAttachment] | None = None,
        html_body: str | None = None,
    ) -> str:
        """Send email via Resend API.

        TODO: Implement actual Resend API call using httpx.
        """
        raise NotImplementedError("ResendAdapter.send_email")

    def parse_inbound_webhook(self, payload: dict[str, Any]) -> InboundMessage:
        """Parse Resend inbound webhook payload.

        TODO: Implement Resend webhook payload parsing.
        """
        raise NotImplementedError("ResendAdapter.parse_inbound_webhook")
