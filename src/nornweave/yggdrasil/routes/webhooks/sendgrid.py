"""SendGrid webhook handler."""


from fastapi import APIRouter, Request, status

router = APIRouter()


@router.post("/sendgrid", status_code=status.HTTP_200_OK)
async def sendgrid_webhook(_request: Request) -> dict[str, str]:
    """Handle inbound email webhook from SendGrid.

    TODO: Parse webhook payload, create/resolve thread, store message.
    """
    # Placeholder - will be implemented with Verdandi (ingestion engine)
    return {"status": "received"}
