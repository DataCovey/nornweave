"""SQLite storage adapter (Urdr) for local development."""

from nornweave.core.interfaces import StorageInterface
from nornweave.models import Inbox, Thread, Message


class SQLiteAdapter(StorageInterface):
    """SQLite implementation of StorageInterface."""

    async def create_inbox(self, inbox: Inbox) -> Inbox:
        raise NotImplementedError("SQLiteAdapter.create_inbox")

    async def get_inbox(self, inbox_id: str) -> Inbox | None:
        raise NotImplementedError("SQLiteAdapter.get_inbox")

    async def get_inbox_by_email(self, email_address: str) -> Inbox | None:
        raise NotImplementedError("SQLiteAdapter.get_inbox_by_email")

    async def delete_inbox(self, inbox_id: str) -> bool:
        raise NotImplementedError("SQLiteAdapter.delete_inbox")

    async def create_thread(self, thread: Thread) -> Thread:
        raise NotImplementedError("SQLiteAdapter.create_thread")

    async def get_thread(self, thread_id: str) -> Thread | None:
        raise NotImplementedError("SQLiteAdapter.get_thread")

    async def create_message(self, message: Message) -> Message:
        raise NotImplementedError("SQLiteAdapter.create_message")

    async def get_message(self, message_id: str) -> Message | None:
        raise NotImplementedError("SQLiteAdapter.get_message")

    async def list_messages_for_inbox(
        self,
        inbox_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        raise NotImplementedError("SQLiteAdapter.list_messages_for_inbox")

    async def list_threads_for_inbox(
        self,
        inbox_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Thread]:
        raise NotImplementedError("SQLiteAdapter.list_threads_for_inbox")
