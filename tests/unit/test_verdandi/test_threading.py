"""Unit tests for threading algorithm."""

from datetime import datetime, timedelta

import pytest

from nornweave.verdandi.threading import (
    SUBJECT_MATCH_WINDOW_DAYS,
    build_references_chain,
    compute_participant_hash,
    normalize_message_id,
    normalize_subject,
    parse_references_header,
    should_thread_together,
)


class TestNormalizeSubject:
    """Tests for subject normalization."""

    def test_simple_subject(self) -> None:
        """Test subject without prefixes."""
        assert normalize_subject("Hello World") == "hello world"

    def test_re_prefix(self) -> None:
        """Test Re: prefix removal."""
        assert normalize_subject("Re: Hello") == "hello"
        assert normalize_subject("RE: Hello") == "hello"
        assert normalize_subject("re: Hello") == "hello"

    def test_fwd_prefix(self) -> None:
        """Test Fwd: prefix removal."""
        assert normalize_subject("Fwd: Hello") == "hello"
        assert normalize_subject("FWD: Hello") == "hello"
        assert normalize_subject("Fw: Hello") == "hello"

    def test_multiple_prefixes(self) -> None:
        """Test multiple nested prefixes."""
        assert normalize_subject("Re: Fwd: Re: Meeting") == "meeting"
        assert normalize_subject("Fwd: Re: Fwd: Hello") == "hello"

    def test_german_prefixes(self) -> None:
        """Test German reply/forward prefixes."""
        assert normalize_subject("AW: Anfrage") == "anfrage"
        assert normalize_subject("WG: Anfrage") == "anfrage"

    def test_swedish_prefix(self) -> None:
        """Test Swedish reply prefix."""
        assert normalize_subject("SV: Förfrågan") == "förfrågan"

    def test_whitespace_handling(self) -> None:
        """Test whitespace normalization."""
        assert normalize_subject("  Re:   Hello   World  ") == "hello world"
        assert normalize_subject("Re:    Re:   Hello") == "hello"

    def test_empty_subject(self) -> None:
        """Test empty subject."""
        assert normalize_subject("") == ""
        assert normalize_subject("   ") == ""

    def test_prefix_only(self) -> None:
        """Test subject that is only a prefix."""
        assert normalize_subject("Re:") == ""
        assert normalize_subject("Re: ") == ""


class TestNormalizeMessageId:
    """Tests for Message-ID normalization."""

    def test_already_normalized(self) -> None:
        """Test already properly formatted Message-ID."""
        assert normalize_message_id("<abc@example.com>") == "<abc@example.com>"

    def test_missing_brackets(self) -> None:
        """Test Message-ID without angle brackets."""
        assert normalize_message_id("abc@example.com") == "<abc@example.com>"

    def test_missing_open_bracket(self) -> None:
        """Test Message-ID without opening bracket."""
        assert normalize_message_id("abc@example.com>") == "<abc@example.com>"

    def test_missing_close_bracket(self) -> None:
        """Test Message-ID without closing bracket."""
        assert normalize_message_id("<abc@example.com") == "<abc@example.com>"

    def test_whitespace(self) -> None:
        """Test Message-ID with whitespace."""
        assert normalize_message_id("  <abc@example.com>  ") == "<abc@example.com>"

    def test_malformed_without_at(self) -> None:
        """Test Message-ID without @ is still normalized (permissive).
        
        The function normalizes format but doesn't validate RFC 5322 compliance.
        This allows handling of malformed but usable IDs from real-world emails.
        """
        assert normalize_message_id("invalid") == "<invalid>"

    def test_empty(self) -> None:
        """Test empty Message-ID."""
        assert normalize_message_id("") is None
        assert normalize_message_id(None) is None


class TestParseReferencesHeader:
    """Tests for References header parsing."""

    def test_single_reference(self) -> None:
        """Test single reference."""
        refs = parse_references_header("<abc@example.com>")
        assert refs == ["<abc@example.com>"]

    def test_multiple_references(self) -> None:
        """Test multiple references."""
        refs = parse_references_header("<abc@example.com> <def@example.com> <ghi@example.com>")
        assert refs == ["<abc@example.com>", "<def@example.com>", "<ghi@example.com>"]

    def test_newlines(self) -> None:
        """Test references with newlines (folded header)."""
        refs = parse_references_header("<abc@example.com>\n<def@example.com>")
        assert refs == ["<abc@example.com>", "<def@example.com>"]

    def test_empty(self) -> None:
        """Test empty references."""
        assert parse_references_header("") == []
        assert parse_references_header(None) == []

    def test_invalid_refs_filtered(self) -> None:
        """Test that invalid refs are filtered out."""
        refs = parse_references_header("<valid@example.com> invalid <also-valid@test.com>")
        assert refs == ["<valid@example.com>", "<also-valid@test.com>"]


class TestComputeParticipantHash:
    """Tests for participant hash computation."""

    def test_simple_hash(self) -> None:
        """Test hash computation."""
        hash1 = compute_participant_hash(
            "alice@example.com",
            ["bob@example.com"],
        )
        assert len(hash1) == 16

    def test_order_independent(self) -> None:
        """Test that hash is order-independent."""
        hash1 = compute_participant_hash(
            "alice@example.com",
            ["bob@example.com", "carol@example.com"],
        )
        hash2 = compute_participant_hash(
            "bob@example.com",
            ["carol@example.com", "alice@example.com"],
        )
        assert hash1 == hash2

    def test_with_cc(self) -> None:
        """Test hash with CC addresses."""
        hash_no_cc = compute_participant_hash(
            "alice@example.com",
            ["bob@example.com"],
        )
        hash_with_cc = compute_participant_hash(
            "alice@example.com",
            ["bob@example.com"],
            cc_addresses=["carol@example.com"],
        )
        assert hash_no_cc != hash_with_cc

    def test_name_extraction(self) -> None:
        """Test that display names are stripped."""
        hash1 = compute_participant_hash(
            "alice@example.com",
            ["bob@example.com"],
        )
        hash2 = compute_participant_hash(
            "Alice <alice@example.com>",
            ["Bob <bob@example.com>"],
        )
        assert hash1 == hash2


class TestBuildReferencesChain:
    """Tests for building References chain."""

    def test_empty_parent(self) -> None:
        """Test with no parent references."""
        refs = build_references_chain(None, "<parent@example.com>")
        assert refs == ["<parent@example.com>"]

    def test_with_parent_refs(self) -> None:
        """Test with parent references."""
        refs = build_references_chain(
            ["<ref1@example.com>", "<ref2@example.com>"],
            "<parent@example.com>",
        )
        assert refs == ["<ref1@example.com>", "<ref2@example.com>", "<parent@example.com>"]

    def test_max_length_limit(self) -> None:
        """Test that chain is limited to max length."""
        parent_refs = [f"<ref{i}@example.com>" for i in range(25)]
        refs = build_references_chain(parent_refs, "<parent@example.com>", max_length=20)
        assert len(refs) == 20
        # Should keep the most recent refs
        assert refs[-1] == "<parent@example.com>"

    def test_no_duplicates(self) -> None:
        """Test that parent is not duplicated."""
        refs = build_references_chain(
            ["<parent@example.com>"],
            "<parent@example.com>",
        )
        assert refs == ["<parent@example.com>"]


class TestShouldThreadTogether:
    """Tests for subject-based threading decision."""

    def test_matching_subjects(self) -> None:
        """Test matching subjects."""
        assert should_thread_together("Hello", "Hello") is True
        assert should_thread_together("Re: Hello", "Hello") is True
        assert should_thread_together("Hello", "Re: Hello") is True

    def test_different_subjects(self) -> None:
        """Test different subjects."""
        assert should_thread_together("Hello", "Goodbye") is False

    def test_time_window_valid(self) -> None:
        """Test within time window."""
        assert should_thread_together(
            "Hello",
            "Re: Hello",
            time_diff=timedelta(days=3),
        ) is True

    def test_time_window_exceeded(self) -> None:
        """Test outside time window."""
        assert should_thread_together(
            "Hello",
            "Re: Hello",
            time_diff=timedelta(days=SUBJECT_MATCH_WINDOW_DAYS + 1),
        ) is False

    def test_empty_subject(self) -> None:
        """Test empty subjects."""
        assert should_thread_together("", "") is False
        assert should_thread_together("Hello", "") is False
