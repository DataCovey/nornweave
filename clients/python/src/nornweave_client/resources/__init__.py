"""Resource classes for NornWeave API endpoints."""

from nornweave_client.resources._base import AsyncBaseResource, SyncBaseResource
from nornweave_client.resources.inboxes import AsyncInboxesResource, InboxesResource
from nornweave_client.resources.messages import AsyncMessagesResource, MessagesResource
from nornweave_client.resources.search import AsyncSearchResource, SearchResource
from nornweave_client.resources.threads import AsyncThreadsResource, ThreadsResource

__all__ = [
    "SyncBaseResource",
    "AsyncBaseResource",
    "InboxesResource",
    "AsyncInboxesResource",
    "MessagesResource",
    "AsyncMessagesResource",
    "ThreadsResource",
    "AsyncThreadsResource",
    "SearchResource",
    "AsyncSearchResource",
]
