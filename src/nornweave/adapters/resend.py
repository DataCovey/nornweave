"""Resend email provider adapter. Placeholder."""

from nornweave.core.interfaces import EmailProvider, InboundMessage


class ResendAdapter(EmailProvider):
    """Resend implementation of EmailProvider."""

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
        raise NotImplementedError("ResendAdapter.send_email")

    def parse_inbound_webhook(self, payload: dict) -> InboundMessage:
        raise NotImplementedError("ResendAdapter.parse_inbound_webhook")
