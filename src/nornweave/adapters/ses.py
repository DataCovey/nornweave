"""AWS SES email provider adapter."""

from typing import Any

from nornweave.core.interfaces import EmailProvider, InboundMessage


class SESAdapter(EmailProvider):
    """AWS SES implementation of EmailProvider."""

    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        region: str = "us-east-1",
    ) -> None:
        """Initialize AWS SES adapter.

        Args:
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key
            region: AWS region (default: us-east-1)
        """
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._region = region

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
        """Send email via AWS SES.

        TODO: Implement actual SES API call using boto3 or aioboto3.
        """
        raise NotImplementedError("SESAdapter.send_email")

    def parse_inbound_webhook(self, payload: dict[str, Any]) -> InboundMessage:
        """Parse AWS SES inbound webhook payload (SNS notification).

        TODO: Implement SES/SNS webhook payload parsing.
        """
        raise NotImplementedError("SESAdapter.parse_inbound_webhook")
