"""HTML to Markdown conversion (Verdandi)."""


def html_to_markdown(html: str) -> str:
    """Convert HTML email body to clean Markdown. Placeholder."""
    if not html or not html.strip():
        return ""
    # TODO: use html2text
    return html.strip()
