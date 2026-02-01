"""SendGrid email provider adapter."""

from typing import TYPE_CHECKING, Any

from nornweave.core.interfaces import EmailProvider, InboundMessage

if TYPE_CHECKING:
    from nornweave.models.attachment import SendAttachment


class SendGridAdapter(EmailProvider):
    """SendGrid implementation of EmailProvider."""

    def __init__(self, api_key: str) -> None:
        """Initialize SendGrid adapter.

        Args:
            api_key: SendGrid API key
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
        """Send email via SendGrid API.

        TODO: Implement actual SendGrid API call using httpx.
        """
        raise NotImplementedError("SendGridAdapter.send_email")

    def parse_inbound_webhook(self, payload: dict[str, Any]) -> InboundMessage:
        """Parse SendGrid inbound webhook payload.

        TODO: Implement SendGrid webhook payload parsing.
        """
        raise NotImplementedError("SendGridAdapter.parse_inbound_webhook")
