"""Email sending via configured provider. Placeholder."""

from nornweave.core.interfaces import EmailProvider


async def send_via_provider(
    provider: EmailProvider,
    to: list[str],
    subject: str,
    body: str,
    *,
    from_address: str,
    reply_to: str | None = None,
) -> str:
    """Send email through provider. Returns provider message id."""
    return await provider.send_email(
        to=to,
        subject=subject,
        body=body,
        from_address=from_address,
        reply_to=reply_to,
    )
