"""Domain models: Inbox, Thread, Message, Event, Attachment."""

from nornweave.models.attachment import (
    Attachment,
    AttachmentCreate,
    AttachmentDisposition,
    AttachmentMeta,
    AttachmentResponse,
    AttachmentUpload,
    SendAttachment,
)
from nornweave.models.event import (
    BounceEvent,
    ComplaintEvent,
    DeliveryEvent,
    Event,
    EventCreate,
    EventType,
    ListEventsResponse,
    MessageBouncedEvent,
    MessageComplainedEvent,
    MessageDeliveredEvent,
    MessageReceivedEvent,
    MessageRejectedEvent,
    MessageSentEvent,
    Recipient,
    RejectEvent,
    SendEvent,
    WebhookEvent,
)
from nornweave.models.inbox import Inbox, InboxBase, InboxCreate
from nornweave.models.message import (
    ListMessagesResponse,
    Message,
    MessageBase,
    MessageCreate,
    MessageDirection,
    MessageInCreate,
    MessageItem,
    ReplyToMessageRequest,
    SendMessageRequest,
    SendMessageResponse,
    UpdateMessageRequest,
)
from nornweave.models.thread import (
    ListThreadsResponse,
    Thread,
    ThreadBase,
    ThreadCreate,
    ThreadItem,
    ThreadSummary,
    UpdateThreadRequest,
)

# Rebuild models with forward references now that all models are imported.
# This is necessary because some models have circular references (e.g., Thread->Message,
# MessageReceivedEvent->Message) which cannot be resolved at module load time.
Thread.model_rebuild()
MessageReceivedEvent.model_rebuild()

__all__ = [
    # Attachment models
    "Attachment",
    "AttachmentCreate",
    "AttachmentDisposition",
    "AttachmentMeta",
    "AttachmentResponse",
    "AttachmentUpload",
    "SendAttachment",
    # Event models
    "BounceEvent",
    "ComplaintEvent",
    "DeliveryEvent",
    "Event",
    "EventCreate",
    "EventType",
    "ListEventsResponse",
    "MessageBouncedEvent",
    "MessageComplainedEvent",
    "MessageDeliveredEvent",
    "MessageReceivedEvent",
    "MessageRejectedEvent",
    "MessageSentEvent",
    "Recipient",
    "RejectEvent",
    "SendEvent",
    "WebhookEvent",
    # Inbox models
    "Inbox",
    "InboxBase",
    "InboxCreate",
    # Message models
    "ListMessagesResponse",
    "Message",
    "MessageBase",
    "MessageCreate",
    "MessageDirection",
    "MessageInCreate",
    "MessageItem",
    "ReplyToMessageRequest",
    "SendMessageRequest",
    "SendMessageResponse",
    "UpdateMessageRequest",
    # Thread models
    "ListThreadsResponse",
    "Thread",
    "ThreadBase",
    "ThreadCreate",
    "ThreadItem",
    "ThreadSummary",
    "UpdateThreadRequest",
]
