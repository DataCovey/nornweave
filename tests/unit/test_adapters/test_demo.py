"""Unit tests for DemoAdapter (demo/sandbox email provider)."""

from __future__ import annotations

import pytest

from nornweave.adapters.demo import DemoAdapter


class TestDemoAdapterSendEmail:
    """Tests for DemoAdapter.send_email()."""

    @pytest.mark.asyncio
    async def test_returns_synthetic_message_id(self) -> None:
        """send_email returns a synthetic provider message ID."""
        adapter = DemoAdapter(domain="demo.nornweave.local")
        msg_id = await adapter.send_email(
            to=["alice@example.com"],
            subject="Test",
            body="Hello",
            from_address="demo@demo.nornweave.local",
        )
        assert msg_id.startswith("<demo-")
        assert "@demo.nornweave.local>" in msg_id

    @pytest.mark.asyncio
    async def test_uses_provided_message_id_when_given(self) -> None:
        """When message_id is provided, it is returned as-is."""
        adapter = DemoAdapter()
        msg_id = await adapter.send_email(
            to=["bob@example.com"],
            subject="Re: Test",
            body="Reply",
            from_address="support@demo.nornweave.local",
            message_id="<custom-123@example.com>",
        )
        assert msg_id == "<custom-123@example.com>"


class TestDemoAdapterParseInboundWebhook:
    """Tests for DemoAdapter.parse_inbound_webhook()."""

    def test_generic_format_produces_inbound_message(self) -> None:
        """parse_inbound_webhook accepts generic dict and returns InboundMessage."""
        adapter = DemoAdapter()
        payload = {
            "from_address": "customer@example.com",
            "to_address": "support@demo.nornweave.local",
            "subject": "Help",
            "body_plain": "I need assistance.",
        }
        inbound = adapter.parse_inbound_webhook(payload)
        assert inbound.from_address == "customer@example.com"
        assert inbound.to_address == "support@demo.nornweave.local"
        assert inbound.subject == "Help"
        assert inbound.body_plain == "I need assistance."

    def test_accepts_from_and_to_aliases(self) -> None:
        """Payload can use 'from' and 'to' instead of from_address/to_address."""
        adapter = DemoAdapter()
        payload = {
            "from": "a@x.com",
            "to": "b@demo.nornweave.local",
            "subject": "S",
            "body": "B",
        }
        inbound = adapter.parse_inbound_webhook(payload)
        assert inbound.from_address == "a@x.com"
        assert inbound.to_address == "b@demo.nornweave.local"
        assert inbound.body_plain == "B"

    def test_optional_threading_headers(self) -> None:
        """message_id, in_reply_to, references are passed through."""
        adapter = DemoAdapter()
        payload = {
            "from_address": "a@x.com",
            "to_address": "b@demo.nornweave.local",
            "subject": "Re: T",
            "body_plain": "Reply",
            "message_id": "<msg-1@x.com>",
            "in_reply_to": "<parent@x.com>",
            "references": ["<parent@x.com>", "<msg-1@x.com>"],
        }
        inbound = adapter.parse_inbound_webhook(payload)
        assert inbound.message_id == "<msg-1@x.com>"
        assert inbound.in_reply_to == "<parent@x.com>"
        assert inbound.references == ["<parent@x.com>", "<msg-1@x.com>"]
