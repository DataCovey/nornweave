#!/usr/bin/env python3
"""Validate NornWeave Python SDK against a local installation.

This script tests all SDK features against a running NornWeave instance
(typically started via docker-compose).

Usage:
    # Ensure NornWeave is running locally
    docker compose --profile storage_psql --profile mail_mailgun up -d

    # Run migrations
    docker compose exec api alembic upgrade head

    # Run validation
    python scripts/validate_local.py

    # Or specify a custom base URL
    python scripts/validate_local.py --base-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from collections.abc import Callable
from dataclasses import dataclass

# Add the src directory to the path for development
sys.path.insert(0, "src")

from nornweave_client import (
    ApiError,
    AsyncNornWeave,
    NornWeave,
    NotFoundError,
    ValidationError,
)


@dataclass
class TestResult:
    """Result of a single test."""

    name: str
    passed: bool
    error: str | None = None


class ValidationRunner:
    """Runs validation tests against a NornWeave instance."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.results: list[TestResult] = []
        self.created_inbox_ids: list[str] = []

    def record(self, name: str, passed: bool, error: str | None = None) -> None:
        """Record a test result."""
        self.results.append(TestResult(name=name, passed=passed, error=error))
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if error:
            print(f"         Error: {error}")

    def run_test(self, name: str, test_fn: Callable[[], None]) -> None:
        """Run a test function and record the result."""
        try:
            test_fn()
            self.record(name, True)
        except AssertionError as e:
            self.record(name, False, str(e))
        except Exception as e:
            self.record(name, False, f"{type(e).__name__}: {e}")

    async def run_async_test(self, name: str, test_fn: Callable[[], object]) -> None:
        """Run an async test function and record the result."""
        try:
            await test_fn()
            self.record(name, True)
        except AssertionError as e:
            self.record(name, False, str(e))
        except Exception as e:
            self.record(name, False, f"{type(e).__name__}: {e}")

    def cleanup(self) -> None:
        """Clean up created resources."""
        print("\nCleaning up created resources...")
        with NornWeave(base_url=self.base_url) as client:
            for inbox_id in self.created_inbox_ids:
                try:
                    client.inboxes.delete(inbox_id)
                    print(f"  Deleted inbox: {inbox_id}")
                except Exception as e:
                    print(f"  Failed to delete inbox {inbox_id}: {e}")

    def print_summary(self) -> bool:
        """Print test summary and return True if all tests passed."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        print("\n" + "=" * 60)
        print(f"SUMMARY: {passed}/{total} tests passed")
        if failed > 0:
            print("\nFailed tests:")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.name}: {r.error}")
        print("=" * 60)

        return failed == 0


def run_sync_tests(runner: ValidationRunner) -> None:
    """Run synchronous client tests."""
    print("\n--- Sync Client Tests ---")

    # Test 1: Health check
    def test_health() -> None:
        with NornWeave(base_url=runner.base_url) as client:
            response = client.health()
            assert response.status == "ok", f"Expected 'ok', got '{response.status}'"

    runner.run_test("Health check", test_health)

    # Test 2: Create inbox
    inbox_id: str | None = None
    unique_suffix = uuid.uuid4().hex[:8]

    def test_create_inbox() -> None:
        nonlocal inbox_id
        with NornWeave(base_url=runner.base_url) as client:
            inbox = client.inboxes.create(
                name=f"Test Inbox {unique_suffix}",
                email_username=f"test-{unique_suffix}",
            )
            inbox_id = inbox.id
            runner.created_inbox_ids.append(inbox_id)
            assert inbox.name == f"Test Inbox {unique_suffix}"
            assert f"test-{unique_suffix}" in inbox.email_address

    runner.run_test("Create inbox", test_create_inbox)

    # Test 3: Get inbox
    def test_get_inbox() -> None:
        assert inbox_id is not None, "No inbox created"
        with NornWeave(base_url=runner.base_url) as client:
            inbox = client.inboxes.get(inbox_id)
            assert inbox.id == inbox_id

    runner.run_test("Get inbox by ID", test_get_inbox)

    # Test 4: List inboxes
    def test_list_inboxes() -> None:
        with NornWeave(base_url=runner.base_url) as client:
            pager = client.inboxes.list(limit=10)
            inboxes = list(pager)
            assert len(inboxes) >= 1, "Expected at least one inbox"

    runner.run_test("List inboxes", test_list_inboxes)

    # Test 5: List inboxes with pagination
    def test_list_inboxes_pagination() -> None:
        with NornWeave(base_url=runner.base_url) as client:
            pager = client.inboxes.list(limit=1)
            # Check we can access count
            count = pager.count
            assert count >= 1, "Expected at least one inbox"
            # Check we can iterate pages
            pages = list(pager.iter_pages())
            assert len(pages) >= 1, "Expected at least one page"

    runner.run_test("List inboxes with pagination", test_list_inboxes_pagination)

    # Test 6: Send message
    message_id: str | None = None
    thread_id: str | None = None

    def test_send_message() -> None:
        nonlocal message_id, thread_id
        assert inbox_id is not None, "No inbox created"
        with NornWeave(base_url=runner.base_url) as client:
            response = client.messages.send(
                inbox_id=inbox_id,
                to=["recipient@example.com"],
                subject=f"Test Message {unique_suffix}",
                body="This is a **test** message from the SDK validation script.",
            )
            message_id = response.id
            thread_id = response.thread_id
            assert response.id is not None
            assert response.thread_id is not None

    runner.run_test("Send message", test_send_message)

    # Test 7: Get message
    def test_get_message() -> None:
        assert message_id is not None, "No message sent"
        with NornWeave(base_url=runner.base_url) as client:
            message = client.messages.get(message_id)
            assert message.id == message_id
            assert message.direction == "outbound"

    runner.run_test("Get message by ID", test_get_message)

    # Test 8: List messages
    def test_list_messages() -> None:
        assert inbox_id is not None, "No inbox created"
        with NornWeave(base_url=runner.base_url) as client:
            pager = client.messages.list(inbox_id=inbox_id)
            messages = list(pager)
            assert len(messages) >= 1, "Expected at least one message"

    runner.run_test("List messages", test_list_messages)

    # Test 9: List threads
    def test_list_threads() -> None:
        assert inbox_id is not None, "No inbox created"
        with NornWeave(base_url=runner.base_url) as client:
            pager = client.threads.list(inbox_id=inbox_id)
            threads = list(pager)
            assert len(threads) >= 1, "Expected at least one thread"

    runner.run_test("List threads", test_list_threads)

    # Test 10: Get thread
    def test_get_thread() -> None:
        assert thread_id is not None, "No thread created"
        with NornWeave(base_url=runner.base_url) as client:
            thread = client.threads.get(thread_id)
            assert thread.id == thread_id
            assert len(thread.messages) >= 1

    runner.run_test("Get thread with messages", test_get_thread)

    # Test 11: Search messages
    def test_search_messages() -> None:
        assert inbox_id is not None, "No inbox created"
        with NornWeave(base_url=runner.base_url) as client:
            pager = client.search.query(query="test", inbox_id=inbox_id)
            results = list(pager)
            # May or may not find results depending on content
            assert isinstance(results, list)

    runner.run_test("Search messages", test_search_messages)

    # Test 12: Raw response access
    def test_raw_response() -> None:
        assert inbox_id is not None, "No inbox created"
        with NornWeave(base_url=runner.base_url) as client:
            response = client.inboxes.with_raw_response.get(inbox_id)
            assert response.status_code == 200
            assert response.data.id == inbox_id
            assert "content-type" in response.headers

    runner.run_test("Raw response access", test_raw_response)

    # Test 13: Request options (timeout)
    def test_request_options() -> None:
        with NornWeave(base_url=runner.base_url, timeout=5.0) as client:
            response = client.health(request_options={"timeout": 2.0})
            assert response.status == "ok"

    runner.run_test("Request options (timeout)", test_request_options)

    # Test 14: Not found error
    def test_not_found_error() -> None:
        with NornWeave(base_url=runner.base_url) as client:
            try:
                client.inboxes.get("nonexistent-inbox-id")
                raise AssertionError("Expected NotFoundError")
            except NotFoundError as e:
                assert e.status_code == 404

    runner.run_test("NotFoundError handling", test_not_found_error)

    # Test 15: Validation error
    def test_validation_error() -> None:
        with NornWeave(base_url=runner.base_url) as client:
            try:
                # Empty name should cause validation error
                client.inboxes.create(name="", email_username="")
                raise AssertionError("Expected ValidationError")
            except ValidationError as e:
                assert e.status_code == 422
            except ApiError as e:
                # Some validation errors might come as different status codes
                assert e.status_code >= 400

    runner.run_test("ValidationError handling", test_validation_error)

    # Test 16: Delete inbox
    def test_delete_inbox() -> None:
        # Create a new inbox to delete
        with NornWeave(base_url=runner.base_url) as client:
            delete_suffix = uuid.uuid4().hex[:8]
            inbox = client.inboxes.create(
                name=f"Delete Test {delete_suffix}",
                email_username=f"delete-{delete_suffix}",
            )
            delete_id = inbox.id

            # Delete it
            client.inboxes.delete(delete_id)

            # Verify it's gone
            try:
                client.inboxes.get(delete_id)
                raise AssertionError("Inbox should have been deleted")
            except NotFoundError:
                pass  # Expected

    runner.run_test("Delete inbox", test_delete_inbox)


async def run_async_tests(runner: ValidationRunner) -> None:
    """Run asynchronous client tests."""
    print("\n--- Async Client Tests ---")

    unique_suffix = uuid.uuid4().hex[:8]
    inbox_id: str | None = None

    # Test 1: Async health check
    async def test_async_health() -> None:
        async with AsyncNornWeave(base_url=runner.base_url) as client:
            response = await client.health()
            assert response.status == "ok"

    await runner.run_async_test("Async health check", test_async_health)

    # Test 2: Async create inbox
    async def test_async_create_inbox() -> None:
        nonlocal inbox_id
        async with AsyncNornWeave(base_url=runner.base_url) as client:
            inbox = await client.inboxes.create(
                name=f"Async Test {unique_suffix}",
                email_username=f"async-{unique_suffix}",
            )
            inbox_id = inbox.id
            runner.created_inbox_ids.append(inbox_id)
            assert inbox.name == f"Async Test {unique_suffix}"

    await runner.run_async_test("Async create inbox", test_async_create_inbox)

    # Test 3: Async list inboxes
    async def test_async_list_inboxes() -> None:
        async with AsyncNornWeave(base_url=runner.base_url) as client:
            pager = client.inboxes.list()
            inboxes = await pager.to_list()
            assert len(inboxes) >= 1

    await runner.run_async_test("Async list inboxes", test_async_list_inboxes)

    # Test 4: Async send message
    async def test_async_send_message() -> None:
        assert inbox_id is not None, "No inbox created"
        async with AsyncNornWeave(base_url=runner.base_url) as client:
            response = await client.messages.send(
                inbox_id=inbox_id,
                to=["async-recipient@example.com"],
                subject=f"Async Test Message {unique_suffix}",
                body="Async **test** message.",
            )
            assert response.id is not None

    await runner.run_async_test("Async send message", test_async_send_message)

    # Test 5: Async list threads with pagination
    async def test_async_list_threads_pagination() -> None:
        assert inbox_id is not None, "No inbox created"
        async with AsyncNornWeave(base_url=runner.base_url) as client:
            pager = client.threads.list(inbox_id=inbox_id)
            threads = []
            async for thread in pager:
                threads.append(thread)
            assert len(threads) >= 1

    await runner.run_async_test("Async list threads with iteration", test_async_list_threads_pagination)

    # Test 6: Async search
    async def test_async_search() -> None:
        assert inbox_id is not None, "No inbox created"
        async with AsyncNornWeave(base_url=runner.base_url) as client:
            result = await client.search.query_raw(query="async", inbox_id=inbox_id)
            assert isinstance(result.items, list)

    await runner.run_async_test("Async search", test_async_search)


def main() -> None:
    """Run all validation tests."""
    parser = argparse.ArgumentParser(
        description="Validate NornWeave Python SDK against a local installation"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the NornWeave API (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--skip-cleanup",
        action="store_true",
        help="Skip cleanup of created resources",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("NornWeave Python SDK Validation")
    print(f"Base URL: {args.base_url}")
    print("=" * 60)

    runner = ValidationRunner(args.base_url)

    try:
        # Run sync tests
        run_sync_tests(runner)

        # Run async tests
        asyncio.run(run_async_tests(runner))

    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user.")
    except Exception as e:
        print(f"\n\nValidation failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if not args.skip_cleanup:
            runner.cleanup()

    # Print summary and exit with appropriate code
    success = runner.print_summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
