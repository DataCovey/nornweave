"""AWS SES webhook handler."""

from fastapi import APIRouter, Request, status

router = APIRouter()


@router.post("/ses", status_code=status.HTTP_200_OK)
async def ses_webhook(_request: Request) -> dict[str, str]:
    """Handle inbound email webhook from AWS SES.

    TODO: Parse webhook payload (SNS notification), create/resolve thread, store message.
    """
    # Placeholder - will be implemented with Verdandi (ingestion engine)
    return {"status": "received"}
