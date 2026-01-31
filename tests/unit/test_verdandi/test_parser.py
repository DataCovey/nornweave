"""Tests for Verdandi parser."""

from nornweave.verdandi.parser import html_to_markdown


def test_html_to_markdown_empty() -> None:
    assert html_to_markdown("") == ""
    assert html_to_markdown("   ") == ""


def test_html_to_markdown_strips_whitespace() -> None:
    assert html_to_markdown("  hello  ") == "hello"
