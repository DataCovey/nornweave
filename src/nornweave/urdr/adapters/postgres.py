"""PostgreSQL storage adapter (Urdr)."""

from nornweave.core.interfaces import StorageInterface
from nornweave.models import Inbox, Thread, Message


class PostgresAdapter(StorageInterface):
    """PostgreSQL implementation of StorageInterface."""

    async def create_inbox(self, inbox: Inbox) -> Inbox:
        raise NotImplementedError("PostgresAdapter.create_inbox")

    async def get_inbox(self, inbox_id: str) -> Inbox | None:
        raise NotImplementedError("PostgresAdapter.get_inbox")

    async def get_inbox_by_email(self, email_address: str) -> Inbox | None:
        raise NotImplementedError("PostgresAdapter.get_inbox_by_email")

    async def delete_inbox(self, inbox_id: str) -> bool:
        raise NotImplementedError("PostgresAdapter.delete_inbox")

    async def create_thread(self, thread: Thread) -> Thread:
        raise NotImplementedError("PostgresAdapter.create_thread")

    async def get_thread(self, thread_id: str) -> Thread | None:
        raise NotImplementedError("PostgresAdapter.get_thread")

    async def create_message(self, message: Message) -> Message:
        raise NotImplementedError("PostgresAdapter.create_message")

    async def get_message(self, message_id: str) -> Message | None:
        raise NotImplementedError("PostgresAdapter.get_message")

    async def list_messages_for_inbox(
        self,
        inbox_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        raise NotImplementedError("PostgresAdapter.list_messages_for_inbox")

    async def list_threads_for_inbox(
        self,
        inbox_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Thread]:
        raise NotImplementedError("PostgresAdapter.list_threads_for_inbox")
