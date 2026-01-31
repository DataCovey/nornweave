"""Remove reply cruft (e.g. 'On Date wrote:') from email content."""


def remove_reply_cruft(content: str) -> str:
    """Strip common reply signatures and quoted blocks. Placeholder."""
    if not content:
        return ""
    # TODO: regex for "On ... wrote:" etc.
    return content.strip()
