"""HTML to Markdown conversion (Verdandi)."""

import html2text


def html_to_markdown(html: str) -> str:
    """Convert HTML email body to clean Markdown.

    Uses html2text to convert HTML to Markdown with email-friendly settings.
    """
    if not html or not html.strip():
        return ""

    h = html2text.HTML2Text()
    # Configure for email content
    h.ignore_links = False
    h.ignore_images = False
    h.ignore_emphasis = False
    h.body_width = 0  # Don't wrap lines
    h.unicode_snob = True  # Use unicode characters
    h.skip_internal_links = True
    h.inline_links = True
    h.protect_links = True

    return h.handle(html).strip()
