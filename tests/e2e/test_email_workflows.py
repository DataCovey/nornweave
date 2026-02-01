"""End-to-end tests for email workflows.

Tests the main use cases:
1. Create inbox
2. Send email (new thread)
3. Receive reply (simple)
4. Receive reply with attachments
5. Multi-party thread
6. Thread API returns LLM-ready format
7. Search messages
8. LLM agent workflow via API
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import pytest

from nornweave.core.interfaces import InboundAttachment, InboundMessage
from nornweave.models.attachment import AttachmentDisposition
from tests.helpers.ingest import ingest_inbound_message

if TYPE_CHECKING:
    from httpx import AsyncClient

    from nornweave.urdr.adapters.sqlite import SQLiteAdapter
    from tests.mocks.email_provider import MockEmailProvider


@pytest.mark.asyncio
class TestCreateInbox:
    """Test Scenario 1: Create Inbox."""

    async def test_create_inbox_success(
        self,
        e2e_client: AsyncClient,
    ) -> None:
        """Create an inbox via API and verify it's persisted."""
        # Create inbox
        response = await e2e_client.post(
            "/v1/inboxes",
            json={
                "name": "Support Inbox",
                "email_username": "support",
            },
        )
        assert response.status_code == 201, response.text
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["email_address"].startswith("support@")  # Domain may vary by config
        assert data["name"] == "Support Inbox"

        inbox_id = data["id"]

        # Verify inbox can be retrieved
        response = await e2e_client.get(f"/v1/inboxes/{inbox_id}")
        assert response.status_code == 200
        retrieved = response.json()
        assert retrieved["id"] == inbox_id
        assert retrieved["email_address"] == data["email_address"]

    async def test_create_inbox_duplicate_email_fails(
        self,
        e2e_client: AsyncClient,
    ) -> None:
        """Creating an inbox with duplicate email address fails with 409."""
        # Create first inbox
        response = await e2e_client.post(
            "/v1/inboxes",
            json={"name": "First", "email_username": "duplicate"},
        )
        assert response.status_code == 201

        # Try to create another with same email
        response = await e2e_client.post(
            "/v1/inboxes",
            json={"name": "Second", "email_username": "duplicate"},
        )
        assert response.status_code == 409

    async def test_list_inboxes(
        self,
        e2e_client: AsyncClient,
    ) -> None:
        """List all inboxes via API."""
        # Create multiple inboxes
        for name in ["sales", "support", "info"]:
            response = await e2e_client.post(
                "/v1/inboxes",
                json={"name": name.title(), "email_username": name},
            )
            assert response.status_code == 201

        # List inboxes
        response = await e2e_client.get("/v1/inboxes")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert len(data["items"]) == 3


@pytest.mark.asyncio
class TestSendEmail:
    """Test Scenario 2: Send Email (New Thread)."""

    async def test_send_email_creates_thread(
        self,
        e2e_client: AsyncClient,
        mock_provider: MockEmailProvider,
    ) -> None:
        """Send an email and verify thread is created."""
        # Create inbox
        inbox_response = await e2e_client.post(
            "/v1/inboxes",
            json={"name": "Outbound Test", "email_username": "outbound"},
        )
        assert inbox_response.status_code == 201
        inbox_id = inbox_response.json()["id"]

        # Send email
        response = await e2e_client.post(
            "/v1/messages",
            json={
                "inbox_id": inbox_id,
                "to": ["alice@example.com"],
                "subject": "Hello Alice",
                "body": "Hi Alice,\n\nThis is a test email.\n\nBest,\nSupport",
            },
        )
        assert response.status_code == 201, response.text
        data = response.json()

        # Verify response
        assert "id" in data
        assert "thread_id" in data
        assert data["status"] == "sent"
        assert data["provider_message_id"] is not None

        # Verify mock provider received the email
        assert len(mock_provider.sent_emails) == 1
        sent = mock_provider.sent_emails[0]
        assert sent.to == ["alice@example.com"]
        assert sent.subject == "Hello Alice"
        assert "test email" in sent.body

        # Verify message is stored
        msg_response = await e2e_client.get(f"/v1/messages/{data['id']}")
        assert msg_response.status_code == 200
        msg_data = msg_response.json()
        assert msg_data["direction"] == "outbound"
        assert msg_data["thread_id"] == data["thread_id"]

    async def test_send_reply_to_existing_thread(
        self,
        e2e_client: AsyncClient,
        mock_provider: MockEmailProvider,
    ) -> None:
        """Send a reply to an existing thread."""
        # Create inbox and send first message
        inbox_response = await e2e_client.post(
            "/v1/inboxes",
            json={"name": "Reply Test", "email_username": "reply"},
        )
        inbox_id = inbox_response.json()["id"]

        first_response = await e2e_client.post(
            "/v1/messages",
            json={
                "inbox_id": inbox_id,
                "to": ["bob@example.com"],
                "subject": "Initial Message",
                "body": "First message content",
            },
        )
        thread_id = first_response.json()["thread_id"]

        # Send reply to the same thread
        reply_response = await e2e_client.post(
            "/v1/messages",
            json={
                "inbox_id": inbox_id,
                "to": ["bob@example.com"],
                "subject": "Re: Initial Message",
                "body": "This is a follow-up",
                "reply_to_thread_id": thread_id,
            },
        )
        assert reply_response.status_code == 201

        # Verify both messages are in the same thread
        reply_data = reply_response.json()
        assert reply_data["thread_id"] == thread_id

        # Verify two emails were sent
        assert len(mock_provider.sent_emails) == 2


@pytest.mark.asyncio
class TestReceiveReply:
    """Test Scenario 3: Receive Reply (Simple)."""

    async def test_receive_reply_joins_thread(
        self,
        e2e_client: AsyncClient,
        e2e_storage: SQLiteAdapter,
        mock_provider: MockEmailProvider,
    ) -> None:
        """Receive an inbound reply and verify it joins the correct thread."""
        # Create inbox
        inbox_response = await e2e_client.post(
            "/v1/inboxes",
            json={"name": "Inbound Test", "email_username": "inbound"},
        )
        inbox_id = inbox_response.json()["id"]
        inbox_email = inbox_response.json()["email_address"]

        # Send outbound email to create thread
        send_response = await e2e_client.post(
            "/v1/messages",
            json={
                "inbox_id": inbox_id,
                "to": ["customer@example.com"],
                "subject": "Your Order Status",
                "body": "Your order has shipped!",
            },
        )
        thread_id = send_response.json()["thread_id"]
        outbound_message_id = mock_provider.sent_emails[0].provider_message_id

        # Simulate receiving a reply via ingest helper
        inbound = InboundMessage(
            from_address="customer@example.com",
            to_address=inbox_email,
            subject="Re: Your Order Status",
            body_plain="Thanks for the update! When will it arrive?",
            message_id="<reply-123@example.com>",
            in_reply_to=outbound_message_id,
            references=[outbound_message_id],
            timestamp=datetime.utcnow(),
        )

        ingested = await ingest_inbound_message(e2e_storage, inbox_id, inbound)

        # Verify message was added to the same thread
        assert ingested.thread_id == thread_id
        assert ingested.direction.value == "inbound"

        # Verify thread has 2 messages via API
        thread_response = await e2e_client.get(f"/v1/threads/{thread_id}")
        assert thread_response.status_code == 200
        thread_data = thread_response.json()
        assert len(thread_data["messages"]) == 2

    async def test_receive_new_email_creates_thread(
        self,
        e2e_client: AsyncClient,
        e2e_storage: SQLiteAdapter,
    ) -> None:
        """Receive a new inbound email (not a reply) creates a new thread."""
        # Create inbox
        inbox_response = await e2e_client.post(
            "/v1/inboxes",
            json={"name": "New Email Test", "email_username": "new"},
        )
        inbox_id = inbox_response.json()["id"]
        inbox_email = inbox_response.json()["email_address"]

        # Simulate receiving a new email
        inbound = InboundMessage(
            from_address="newcustomer@example.com",
            to_address=inbox_email,
            subject="Inquiry about your product",
            body_plain="I'd like to learn more about your pricing.",
            message_id="<new-inquiry-456@example.com>",
            timestamp=datetime.utcnow(),
        )

        ingested = await ingest_inbound_message(e2e_storage, inbox_id, inbound)

        # Verify a new thread was created
        assert ingested.thread_id is not None

        # Verify thread via API
        thread_response = await e2e_client.get(f"/v1/threads/{ingested.thread_id}")
        assert thread_response.status_code == 200
        thread_data = thread_response.json()
        assert thread_data["subject"] == "Inquiry about your product"
        assert len(thread_data["messages"]) == 1


@pytest.mark.asyncio
class TestReceiveReplyWithAttachments:
    """Test Scenario 4: Receive Reply with Attachments."""

    async def test_receive_email_with_attachments(
        self,
        e2e_client: AsyncClient,
        e2e_storage: SQLiteAdapter,
    ) -> None:
        """Receive an email with attachments and verify they are stored."""
        # Create inbox
        inbox_response = await e2e_client.post(
            "/v1/inboxes",
            json={"name": "Attachment Test", "email_username": "attachments"},
        )
        inbox_id = inbox_response.json()["id"]
        inbox_email = inbox_response.json()["email_address"]

        # Create test attachments
        pdf_content = b"%PDF-1.4 fake pdf content"
        image_content = b"\x89PNG\r\n\x1a\n fake image content"

        attachments = [
            InboundAttachment(
                filename="document.pdf",
                content_type="application/pdf",
                content=pdf_content,
                size_bytes=len(pdf_content),
                disposition=AttachmentDisposition.ATTACHMENT,
            ),
            InboundAttachment(
                filename="image.png",
                content_type="image/png",
                content=image_content,
                size_bytes=len(image_content),
                disposition=AttachmentDisposition.INLINE,
                content_id="<img001>",
            ),
        ]

        # Simulate receiving email with attachments
        inbound = InboundMessage(
            from_address="sender@example.com",
            to_address=inbox_email,
            subject="Documents attached",
            body_plain="Please find the documents attached.",
            message_id="<attach-789@example.com>",
            timestamp=datetime.utcnow(),
            attachments=attachments,
        )

        ingested = await ingest_inbound_message(
            e2e_storage, inbox_id, inbound, create_attachments=True
        )

        # Verify attachments were stored
        stored_attachments = await e2e_storage.list_attachments_for_message(ingested.message_id)
        assert len(stored_attachments) == 2

        # Check attachment details
        filenames = {att["filename"] for att in stored_attachments}
        assert "document.pdf" in filenames
        assert "image.png" in filenames

        # Check inline attachment has content_id
        image_att = next(att for att in stored_attachments if att["filename"] == "image.png")
        assert image_att["content_id"] == "<img001>"
        assert image_att["disposition"] == "inline"


@pytest.mark.asyncio
class TestMultiPartyThread:
    """Test Scenario 5: Multi-Party Thread with 5 messages."""

    async def test_multi_party_thread_maintains_threading(
        self,
        e2e_client: AsyncClient,
        e2e_storage: SQLiteAdapter,
        mock_provider: MockEmailProvider,
    ) -> None:
        """
        Test a multi-party conversation:
        1. Inbox receives email from Alice (new thread)
        2. Inbox replies to Alice
        3. Alice replies, CC's Bob
        4. Bob replies (has References header)
        5. Inbox replies to all

        All 5 messages should be in the same thread.
        """
        # Create inbox
        inbox_response = await e2e_client.post(
            "/v1/inboxes",
            json={"name": "Multi-Party Test", "email_username": "multiparty"},
        )
        inbox_id = inbox_response.json()["id"]
        inbox_email = inbox_response.json()["email_address"]

        # Message 1: Alice sends initial email
        msg1_id = "<alice-initial@example.com>"
        inbound1 = InboundMessage(
            from_address="alice@example.com",
            to_address=inbox_email,
            subject="Project Discussion",
            body_plain="Hi, I'd like to discuss the project timeline.",
            message_id=msg1_id,
            timestamp=datetime.utcnow(),
        )
        msg1 = await ingest_inbound_message(e2e_storage, inbox_id, inbound1)
        thread_id = msg1.thread_id

        # Message 2: Inbox replies to Alice
        send_response = await e2e_client.post(
            "/v1/messages",
            json={
                "inbox_id": inbox_id,
                "to": ["alice@example.com"],
                "subject": "Re: Project Discussion",
                "body": "Thanks for reaching out! Let's set up a call.",
                "reply_to_thread_id": thread_id,
            },
        )
        assert send_response.status_code == 201
        msg2_id = mock_provider.sent_emails[-1].provider_message_id

        # Message 3: Alice replies and CC's Bob
        msg3_id = "<alice-reply-cc-bob@example.com>"
        inbound3 = InboundMessage(
            from_address="alice@example.com",
            to_address=inbox_email,
            subject="Re: Project Discussion",
            body_plain="Great! I'm adding Bob to this thread as well.",
            message_id=msg3_id,
            in_reply_to=msg2_id,
            references=[msg1_id, msg2_id],
            cc_addresses=["bob@example.com"],
            timestamp=datetime.utcnow() + timedelta(minutes=5),
        )
        msg3 = await ingest_inbound_message(e2e_storage, inbox_id, inbound3)
        assert msg3.thread_id == thread_id, "Message 3 should be in same thread"

        # Message 4: Bob replies (using References header)
        msg4_id = "<bob-reply@example.com>"
        inbound4 = InboundMessage(
            from_address="bob@example.com",
            to_address=inbox_email,
            subject="Re: Project Discussion",
            body_plain="Happy to join! What's the timeline looking like?",
            message_id=msg4_id,
            in_reply_to=msg3_id,
            references=[msg1_id, msg2_id, msg3_id],
            cc_addresses=["alice@example.com"],
            timestamp=datetime.utcnow() + timedelta(minutes=10),
        )
        msg4 = await ingest_inbound_message(e2e_storage, inbox_id, inbound4)
        assert msg4.thread_id == thread_id, "Message 4 should be in same thread"

        # Message 5: Inbox replies to all
        send_response2 = await e2e_client.post(
            "/v1/messages",
            json={
                "inbox_id": inbox_id,
                "to": ["alice@example.com", "bob@example.com"],
                "subject": "Re: Project Discussion",
                "body": "We're targeting Q2 for completion. I'll send a calendar invite.",
                "reply_to_thread_id": thread_id,
            },
        )
        assert send_response2.status_code == 201

        # Verify all 5 messages are in the same thread
        thread_response = await e2e_client.get(f"/v1/threads/{thread_id}")
        assert thread_response.status_code == 200
        thread_data = thread_response.json()
        assert len(thread_data["messages"]) == 5

        # Verify message order (by timestamp ascending)
        messages = thread_data["messages"]
        assert messages[0]["content"] == "Hi, I'd like to discuss the project timeline."
        assert "Bob" in messages[2]["content"] or "bob" in messages[2]["content"].lower()
        assert "Q2" in messages[4]["content"]


@pytest.mark.asyncio
class TestThreadAPILLMFormat:
    """Test Scenario 6: Thread API Returns LLM-Ready Format."""

    async def test_thread_messages_have_correct_roles(
        self,
        e2e_client: AsyncClient,
        e2e_storage: SQLiteAdapter,
        mock_provider: MockEmailProvider,  # noqa: ARG002 - fixture dependency
    ) -> None:
        """Verify thread API returns messages with role: user/assistant."""
        # Create inbox
        inbox_response = await e2e_client.post(
            "/v1/inboxes",
            json={"name": "LLM Format Test", "email_username": "llmformat"},
        )
        inbox_id = inbox_response.json()["id"]
        inbox_email = inbox_response.json()["email_address"]

        # Receive inbound email (role should be "user")
        inbound = InboundMessage(
            from_address="user@example.com",
            to_address=inbox_email,
            subject="Question about pricing",
            body_plain="How much does your service cost?",
            message_id="<question@example.com>",
            timestamp=datetime.utcnow(),
        )
        msg1 = await ingest_inbound_message(e2e_storage, inbox_id, inbound)
        thread_id = msg1.thread_id

        # Send outbound reply (role should be "assistant")
        await e2e_client.post(
            "/v1/messages",
            json={
                "inbox_id": inbox_id,
                "to": ["user@example.com"],
                "subject": "Re: Question about pricing",
                "body": "Our pricing starts at $20/month.",
                "reply_to_thread_id": thread_id,
            },
        )

        # Get thread in LLM-ready format
        thread_response = await e2e_client.get(f"/v1/threads/{thread_id}")
        assert thread_response.status_code == 200
        thread_data = thread_response.json()

        # Verify roles
        messages = thread_data["messages"]
        assert len(messages) == 2

        # First message (inbound) should have role "user"
        assert messages[0]["role"] == "user"
        assert messages[0]["author"] == "user@example.com"
        assert "cost" in messages[0]["content"].lower()  # From "How much does your service cost?"

        # Second message (outbound) should have role "assistant"
        assert messages[1]["role"] == "assistant"
        assert "$20" in messages[1]["content"]

    async def test_thread_content_is_clean_markdown(
        self,
        e2e_client: AsyncClient,
        e2e_storage: SQLiteAdapter,
    ) -> None:
        """Verify thread messages contain clean markdown, not raw HTML."""
        # Create inbox
        inbox_response = await e2e_client.post(
            "/v1/inboxes",
            json={"name": "Markdown Test", "email_username": "markdown"},
        )
        inbox_id = inbox_response.json()["id"]
        inbox_email = inbox_response.json()["email_address"]

        # Receive email with HTML content
        inbound = InboundMessage(
            from_address="sender@example.com",
            to_address=inbox_email,
            subject="HTML Email",
            body_plain="This is the plain text version.",
            body_html="<html><body><p>This is <b>bold</b> text.</p></body></html>",
            message_id="<html-email@example.com>",
            timestamp=datetime.utcnow(),
        )
        msg = await ingest_inbound_message(e2e_storage, inbox_id, inbound)

        # Get thread
        thread_response = await e2e_client.get(f"/v1/threads/{msg.thread_id}")
        assert thread_response.status_code == 200
        thread_data = thread_response.json()

        # Content should be clean (not contain raw HTML tags in the clean version)
        content = thread_data["messages"][0]["content"]
        assert "<html>" not in content
        assert "<body>" not in content


@pytest.mark.asyncio
class TestSearchMessages:
    """Test Scenario 7: Search Messages."""

    async def test_search_finds_matching_messages(
        self,
        e2e_client: AsyncClient,
        e2e_storage: SQLiteAdapter,
    ) -> None:
        """Search for messages containing specific keywords."""
        # Create inbox
        inbox_response = await e2e_client.post(
            "/v1/inboxes",
            json={"name": "Search Test", "email_username": "search"},
        )
        inbox_id = inbox_response.json()["id"]
        inbox_email = inbox_response.json()["email_address"]

        # Create several messages
        messages_data = [
            ("Order Confirmation", "Your order #12345 has been confirmed."),
            ("Shipping Update", "Your package has shipped via FedEx."),
            ("Delivery Notice", "Your package was delivered."),
            ("Feedback Request", "How was your experience with order #12345?"),
        ]

        for subject, body in messages_data:
            inbound = InboundMessage(
                from_address="store@example.com",
                to_address=inbox_email,
                subject=subject,
                body_plain=body,
                message_id=f"<{subject.lower().replace(' ', '-')}@example.com>",
                timestamp=datetime.utcnow(),
            )
            await ingest_inbound_message(e2e_storage, inbox_id, inbound)

        # Search for "order"
        search_response = await e2e_client.post(
            "/v1/search",
            json={
                "query": "order",
                "inbox_id": inbox_id,
            },
        )
        assert search_response.status_code == 200
        results = search_response.json()

        # Should find 2 messages mentioning "order"
        assert results["count"] == 2
        contents = [item["content_clean"] for item in results["items"]]
        assert any("12345" in c for c in contents)

    async def test_search_excludes_non_matching(
        self,
        e2e_client: AsyncClient,
        e2e_storage: SQLiteAdapter,
    ) -> None:
        """Search should not return messages that don't match."""
        # Create inbox
        inbox_response = await e2e_client.post(
            "/v1/inboxes",
            json={"name": "Search Exclude Test", "email_username": "searchexclude"},
        )
        inbox_id = inbox_response.json()["id"]
        inbox_email = inbox_response.json()["email_address"]

        # Create messages
        inbound = InboundMessage(
            from_address="test@example.com",
            to_address=inbox_email,
            subject="Hello World",
            body_plain="This is a test message about cats.",
            message_id="<cats@example.com>",
            timestamp=datetime.utcnow(),
        )
        await ingest_inbound_message(e2e_storage, inbox_id, inbound)

        # Search for something not in the message
        search_response = await e2e_client.post(
            "/v1/search",
            json={
                "query": "dogs",
                "inbox_id": inbox_id,
            },
        )
        assert search_response.status_code == 200
        results = search_response.json()
        assert results["count"] == 0


@pytest.mark.asyncio
class TestLLMAgentWorkflow:
    """Test Scenario 8: LLM Agent Workflow via API."""

    async def test_agent_workflow_check_inbox_read_respond(
        self,
        e2e_client: AsyncClient,
        e2e_storage: SQLiteAdapter,
        mock_provider: MockEmailProvider,
    ) -> None:
        """
        Simulate an LLM agent workflow:
        1. Agent checks inbox for threads
        2. Agent reads thread content
        3. Agent sends a reply
        """
        # Create inbox (simulating agent provisioning an inbox)
        inbox_response = await e2e_client.post(
            "/v1/inboxes",
            json={"name": "Agent Inbox", "email_username": "agent"},
        )
        assert inbox_response.status_code == 201
        inbox_id = inbox_response.json()["id"]
        inbox_email = inbox_response.json()["email_address"]

        # Simulate an inbound email arriving
        inbound = InboundMessage(
            from_address="customer@example.com",
            to_address=inbox_email,
            subject="Need help with my account",
            body_plain="I'm having trouble logging in. Can you help?",
            message_id="<help-request@example.com>",
            timestamp=datetime.utcnow(),
        )
        await ingest_inbound_message(e2e_storage, inbox_id, inbound)

        # Step 1: Agent checks inbox for recent threads
        threads_response = await e2e_client.get(f"/v1/threads?inbox_id={inbox_id}")
        assert threads_response.status_code == 200
        threads_data = threads_response.json()
        assert threads_data["count"] >= 1

        # Find the thread we're looking for
        thread = next(t for t in threads_data["items"] if "account" in t["subject"].lower())
        thread_id = thread["id"]

        # Step 2: Agent reads the thread to get full context
        thread_response = await e2e_client.get(f"/v1/threads/{thread_id}")
        assert thread_response.status_code == 200
        thread_content = thread_response.json()

        # Verify agent can see the customer's message
        messages = thread_content["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert "logging in" in messages[0]["content"]

        # Step 3: Agent sends a reply
        # (In a real scenario, the LLM would generate this based on the thread content)
        agent_reply = (
            "Hi,\n\n"
            "I'd be happy to help you with your login issue. "
            "Please try resetting your password using the 'Forgot Password' link.\n\n"
            "Let me know if that doesn't work.\n\n"
            "Best,\nSupport Bot"
        )

        reply_response = await e2e_client.post(
            "/v1/messages",
            json={
                "inbox_id": inbox_id,
                "to": ["customer@example.com"],
                "subject": "Re: Need help with my account",
                "body": agent_reply,
                "reply_to_thread_id": thread_id,
            },
        )
        assert reply_response.status_code == 201
        assert reply_response.json()["status"] == "sent"

        # Verify the reply was sent via mock provider
        assert len(mock_provider.sent_emails) == 1
        sent = mock_provider.sent_emails[0]
        assert sent.to == ["customer@example.com"]
        assert "password" in sent.body.lower()

        # Verify thread now has 2 messages
        updated_thread = await e2e_client.get(f"/v1/threads/{thread_id}")
        assert len(updated_thread.json()["messages"]) == 2

    async def test_agent_workflow_search_and_respond(
        self,
        e2e_client: AsyncClient,
        e2e_storage: SQLiteAdapter,
        mock_provider: MockEmailProvider,
    ) -> None:
        """
        Simulate agent using search to find relevant messages:
        1. Agent searches for messages mentioning "refund"
        2. Agent reads the found thread
        3. Agent responds
        """
        # Create inbox
        inbox_response = await e2e_client.post(
            "/v1/inboxes",
            json={"name": "Search Agent", "email_username": "searchagent"},
        )
        inbox_id = inbox_response.json()["id"]
        inbox_email = inbox_response.json()["email_address"]

        # Create several messages, one about refunds
        messages_data = [
            ("Product Question", "What colors does this come in?"),
            ("Refund Request", "I'd like to request a refund for order #999."),
            ("Shipping Question", "When will my order arrive?"),
        ]

        for subject, body in messages_data:
            inbound = InboundMessage(
                from_address="customer@example.com",
                to_address=inbox_email,
                subject=subject,
                body_plain=body,
                message_id=f"<{subject.lower().replace(' ', '-')}@example.com>",
                timestamp=datetime.utcnow(),
            )
            await ingest_inbound_message(e2e_storage, inbox_id, inbound)

        # Agent searches for "refund"
        search_response = await e2e_client.post(
            "/v1/search",
            json={"query": "refund", "inbox_id": inbox_id},
        )
        assert search_response.status_code == 200
        results = search_response.json()
        assert results["count"] == 1

        # Get the thread containing the refund request
        refund_message = results["items"][0]
        thread_id = refund_message["thread_id"]

        # Agent reads the thread
        thread_response = await e2e_client.get(f"/v1/threads/{thread_id}")
        assert thread_response.status_code == 200

        # Agent responds to the refund request
        await e2e_client.post(
            "/v1/messages",
            json={
                "inbox_id": inbox_id,
                "to": ["customer@example.com"],
                "subject": "Re: Refund Request",
                "body": "I've processed your refund for order #999. Please allow 3-5 business days.",
                "reply_to_thread_id": thread_id,
            },
        )

        # Verify response was sent
        assert any("refund" in e.body.lower() for e in mock_provider.sent_emails)
