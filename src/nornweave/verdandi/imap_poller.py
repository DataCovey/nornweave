"""IMAP polling worker — periodically fetches new emails from IMAP.

Runs as an asyncio.Task in the FastAPI lifespan. Polls the configured
IMAP mailbox on an interval, parses new messages, and feeds them into
the shared ingestion pipeline.
"""

import asyncio
import logging
from typing import TYPE_CHECKING

from nornweave.verdandi.ingest import ingest_message

if TYPE_CHECKING:
    from nornweave.core.config import Settings
    from nornweave.core.interfaces import StorageInterface

logger = logging.getLogger(__name__)


class ImapPoller:
    """Background IMAP polling worker.

    Periodically checks for new messages, parses them, and ingests via
    the shared pipeline. Uses UID-based state tracking to avoid re-processing.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize poller from settings."""
        self._settings = settings
        self._poll_interval = settings.imap_poll_interval
        self._backoff = 1.0  # Exponential backoff for connection failures
        self._max_backoff = 300.0  # Max 5 minutes between retries

    async def run(self) -> None:
        """Main polling loop. Runs until cancelled."""
        logger.info(
            "IMAP poller starting: %s:%s/%s (interval=%ds)",
            self._settings.imap_host,
            self._settings.imap_port,
            self._settings.imap_mailbox,
            self._poll_interval,
        )

        while True:
            try:
                await self._poll_cycle()
                self._backoff = 1.0  # Reset backoff on success
                await asyncio.sleep(self._poll_interval)
            except asyncio.CancelledError:
                logger.info("IMAP poller shutting down")
                raise
            except Exception:
                logger.error(
                    "IMAP poll cycle failed, retrying in %.0fs",
                    self._backoff,
                    exc_info=True,
                )
                await asyncio.sleep(self._backoff)
                self._backoff = min(self._backoff * 2, self._max_backoff)

    async def _poll_cycle(self) -> None:
        """Execute one poll cycle: connect, fetch, ingest, disconnect."""
        from nornweave.adapters.smtp_imap import ImapReceiver
        from nornweave.yggdrasil.dependencies import get_session

        receiver = ImapReceiver(
            host=self._settings.imap_host,
            port=self._settings.imap_port,
            username=self._settings.imap_username,
            password=self._settings.imap_password,
            use_ssl=self._settings.imap_use_ssl,
            mailbox=self._settings.imap_mailbox,
            mark_as_read=self._settings.imap_mark_as_read,
            delete_after_fetch=self._settings.imap_delete_after_fetch,
        )

        try:
            await receiver.connect()

            async with get_session() as session:
                # Import storage adapter
                storage: StorageInterface
                if self._settings.db_driver == "postgres":
                    from nornweave.urdr.adapters.postgres import PostgresAdapter

                    storage = PostgresAdapter(session)
                else:
                    from nornweave.urdr.adapters.sqlite import SQLiteAdapter

                    storage = SQLiteAdapter(session)

                # Get all inboxes to check IMAP state
                inboxes = await storage.list_inboxes(limit=1000)

                if not inboxes:
                    logger.debug("No inboxes configured, skipping IMAP poll")
                    return

                # Get UIDVALIDITY
                uid_validity = await receiver.get_uid_validity()

                # Process each inbox
                for inbox in inboxes:
                    await self._poll_inbox(receiver, storage, inbox.id, uid_validity)

        finally:
            await receiver.disconnect()

    async def _poll_inbox(
        self,
        receiver: object,
        storage: object,
        inbox_id: str,
        uid_validity: int,
    ) -> int:
        """Poll for new messages for a specific inbox.

        Returns:
            Number of new messages ingested.
        """
        from nornweave.adapters.smtp_imap import ImapReceiver
        from nornweave.core.interfaces import StorageInterface

        # Type narrowing
        assert isinstance(receiver, ImapReceiver)
        assert isinstance(storage, StorageInterface)

        # Get current poll state
        state = await storage.get_imap_poll_state(inbox_id)

        if state is None:
            last_uid = 0
        elif state.uid_validity != uid_validity and state.uid_validity != 0:
            # UIDVALIDITY changed — reset and re-sync
            logger.warning(
                "UIDVALIDITY changed for inbox %s (was %d, now %d). Re-syncing.",
                inbox_id,
                state.uid_validity,
                uid_validity,
            )
            last_uid = 0
        else:
            last_uid = state.last_uid

        # Fetch new messages
        messages = await receiver.fetch_new_messages(last_uid)

        if not messages:
            return 0

        logger.info("Processing %d new messages for inbox %s", len(messages), inbox_id)

        count = 0
        highest_uid = last_uid

        for uid, raw_bytes in messages:
            try:
                inbound = receiver.parse_message(raw_bytes)
                result = await ingest_message(inbound, storage, self._settings)

                if result.status == "received":
                    count += 1
                    # Post-fetch behavior
                    await receiver.mark_as_read(uid)
                    await receiver.delete_message(uid)

                if uid > highest_uid:
                    highest_uid = uid

            except Exception:
                logger.error("Failed to process UID %d", uid, exc_info=True)

        # Update state
        if highest_uid > last_uid:
            await storage.upsert_imap_poll_state(
                inbox_id=inbox_id,
                last_uid=highest_uid,
                uid_validity=uid_validity,
                mailbox=self._settings.imap_mailbox,
            )

        logger.info("Ingested %d messages for inbox %s (last_uid=%d)", count, inbox_id, highest_uid)
        return count

    async def sync_inbox(self, inbox_id: str) -> int:
        """On-demand sync for a specific inbox. Used by the manual sync endpoint.

        Returns:
            Number of new messages ingested.
        """
        from nornweave.adapters.smtp_imap import ImapReceiver
        from nornweave.yggdrasil.dependencies import get_session

        receiver = ImapReceiver(
            host=self._settings.imap_host,
            port=self._settings.imap_port,
            username=self._settings.imap_username,
            password=self._settings.imap_password,
            use_ssl=self._settings.imap_use_ssl,
            mailbox=self._settings.imap_mailbox,
            mark_as_read=self._settings.imap_mark_as_read,
            delete_after_fetch=self._settings.imap_delete_after_fetch,
        )

        try:
            await receiver.connect()
            uid_validity = await receiver.get_uid_validity()

            async with get_session() as session:
                storage: StorageInterface
                if self._settings.db_driver == "postgres":
                    from nornweave.urdr.adapters.postgres import PostgresAdapter

                    storage = PostgresAdapter(session)
                else:
                    from nornweave.urdr.adapters.sqlite import SQLiteAdapter

                    storage = SQLiteAdapter(session)

                return await self._poll_inbox(receiver, storage, inbox_id, uid_validity)
        finally:
            await receiver.disconnect()
