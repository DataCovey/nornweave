"""Content extraction: quote/signature removal using Talon.

NornWeave uses Mailgun's Talon library to extract clean reply content
from emails, removing quoted text and signatures. This powers the
extracted_text and extracted_html fields in the Message model.

Reference: https://github.com/mailgun/talon
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Flag to track if Talon has been initialized
_talon_initialized = False


def init_talon() -> bool:
    """
    Initialize Talon with ML classifiers for signature extraction.

    Should be called once on application startup.

    Returns:
        True if initialization succeeded, False otherwise
    """
    global _talon_initialized

    if _talon_initialized:
        return True

    try:
        import talon

        talon.init()
        _talon_initialized = True
        logger.info("Talon ML classifiers initialized successfully")
        return True
    except ImportError:
        logger.warning(
            "Talon library not installed. Quote/signature extraction will be limited. "
            "Install with: pip install talon"
        )
        return False
    except Exception as e:
        logger.warning(f"Failed to initialize Talon: {e}")
        return False


@dataclass
class ExtractedContent:
    """Result of content extraction."""

    extracted_text: str
    extracted_html: str | None
    signature: str | None
    preview: str


def extract_reply_text(body_plain: str) -> str:
    """
    Extract new reply content from plain text email.

    Removes quoted text like "On Jan 31, 2026, Bob wrote: ..."

    Args:
        body_plain: Raw plain text email body

    Returns:
        The new content without quoted replies
    """
    if not body_plain:
        return ""

    try:
        from talon import quotations

        reply = quotations.extract_from_plain(body_plain)
        return reply.strip() if reply else body_plain
    except ImportError:
        # Fallback: basic quote removal
        return _basic_quote_removal(body_plain)
    except Exception as e:
        logger.warning(f"Quote extraction failed: {e}")
        return body_plain


def extract_reply_html(body_html: str) -> str:
    """
    Extract new reply content from HTML email.

    Removes quoted blocks from HTML structure.

    Args:
        body_html: Raw HTML email body

    Returns:
        The new HTML content without quoted replies
    """
    if not body_html:
        return ""

    try:
        from talon import quotations

        reply = quotations.extract_from_html(body_html)
        return reply.strip() if reply else body_html
    except ImportError:
        # No fallback for HTML - return original
        return body_html
    except Exception as e:
        logger.warning(f"HTML quote extraction failed: {e}")
        return body_html


def extract_reply(body: str, content_type: str = "text/plain") -> str:
    """
    Extract reply content based on content type.

    Args:
        body: Email body content
        content_type: MIME content type ("text/plain" or "text/html")

    Returns:
        Extracted reply content
    """
    try:
        from talon import quotations

        return quotations.extract_from(body, content_type)
    except ImportError:
        if "html" in content_type.lower():
            return body
        return _basic_quote_removal(body)
    except Exception as e:
        logger.warning(f"Content extraction failed: {e}")
        return body


def remove_signature_bruteforce(text: str) -> tuple[str, str | None]:
    """
    Remove signature using brute-force method (~90% accuracy).

    Fast and doesn't require ML models. Works by looking for
    common signature delimiters like "--", "Best regards", etc.

    Args:
        text: Plain text email body

    Returns:
        Tuple of (text_without_signature, signature_if_found)
    """
    if not text:
        return "", None

    try:
        from talon.signature.bruteforce import extract_signature

        clean_text, sig = extract_signature(text)
        return clean_text or text, sig
    except ImportError:
        # Fallback: look for common signature markers
        return _basic_signature_removal(text)
    except Exception as e:
        logger.warning(f"Bruteforce signature extraction failed: {e}")
        return text, None


def remove_signature_ml(text: str, sender_email: str | None = None) -> tuple[str, str | None]:
    """
    Remove signature using ML classifier (~98% accuracy).

    Requires talon.init() to be called first.

    Args:
        text: Plain text email body
        sender_email: Optional sender email for better accuracy

    Returns:
        Tuple of (text_without_signature, signature_if_found)
    """
    if not text:
        return "", None

    try:
        from talon import signature as ml_signature

        clean_text, sig = ml_signature.extract(text, sender=sender_email)
        return clean_text or text, sig
    except ImportError:
        logger.warning("Talon ML signature extraction not available, using bruteforce")
        return remove_signature_bruteforce(text)
    except Exception as e:
        logger.warning(f"ML signature extraction failed: {e}")
        return remove_signature_bruteforce(text)


def extract_content(
    body_plain: str,
    body_html: str | None = None,
    sender_email: str | None = None,
    *,
    use_ml_signature: bool = True,
    preview_max_length: int = 100,
    fallback_to_original: bool = True,
) -> ExtractedContent:
    """
    Full content extraction pipeline.

    Steps:
    1. Extract reply (remove quoted text)
    2. Remove signature
    3. Generate preview

    Args:
        body_plain: Plain text body
        body_html: Optional HTML body
        sender_email: Sender email for ML signature detection
        use_ml_signature: Use ML-based signature extraction (more accurate)
        preview_max_length: Maximum length for preview text
        fallback_to_original: Return original content if extraction fails

    Returns:
        ExtractedContent with all processed fields
    """
    # Step 1: Extract reply from plain text
    try:
        reply_text = extract_reply_text(body_plain)
    except Exception as e:
        logger.warning(f"Reply extraction failed: {e}")
        reply_text = body_plain if fallback_to_original else ""

    # Step 2: Remove signature
    try:
        if use_ml_signature and sender_email:
            clean_text, signature = remove_signature_ml(reply_text, sender_email)
        else:
            clean_text, signature = remove_signature_bruteforce(reply_text)
    except Exception as e:
        logger.warning(f"Signature removal failed: {e}")
        clean_text = reply_text
        signature = None

    # Step 3: Extract reply from HTML (if present)
    extracted_html = None
    if body_html:
        try:
            extracted_html = extract_reply_html(body_html)
        except Exception as e:
            logger.warning(f"HTML extraction failed: {e}")
            extracted_html = body_html if fallback_to_original else None

    # Step 4: Generate preview
    preview = generate_preview(clean_text, max_length=preview_max_length)

    return ExtractedContent(
        extracted_text=clean_text,
        extracted_html=extracted_html,
        signature=signature,
        preview=preview,
    )


def generate_preview(text: str, max_length: int = 100) -> str:
    """
    Generate a short preview of the message.

    Args:
        text: Clean text content
        max_length: Maximum preview length

    Returns:
        Preview string, truncated with "..." if needed
    """
    if not text:
        return ""

    # Collapse whitespace
    preview = " ".join(text.split())

    if len(preview) <= max_length:
        return preview

    # Truncate at word boundary
    truncated = preview[:max_length]
    # Find last space to avoid cutting words
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.5:  # Only if we'd keep at least half
        truncated = truncated[:last_space]

    return truncated + "..."


def calculate_message_size(
    text: str | None = None,
    html: str | None = None,
    headers: dict[str, str] | None = None,
    attachments_size: int = 0,
) -> int:
    """
    Calculate approximate message size in bytes.

    Args:
        text: Plain text body
        html: HTML body
        headers: Message headers
        attachments_size: Total size of attachments

    Returns:
        Approximate message size in bytes
    """
    size = 0

    if text:
        size += len(text.encode("utf-8", errors="replace"))

    if html:
        size += len(html.encode("utf-8", errors="replace"))

    if headers:
        for key, value in headers.items():
            size += len(key.encode("utf-8", errors="replace"))
            size += len(value.encode("utf-8", errors="replace"))

    size += attachments_size

    return size


# -------------------------------------------------------------------------
# Fallback implementations (when Talon is not available)
# -------------------------------------------------------------------------


def _basic_quote_removal(text: str) -> str:
    """
    Basic quote removal without Talon.

    Removes lines starting with > and common "On ... wrote:" patterns.
    """
    if not text:
        return ""

    lines = text.split("\n")
    result_lines = []
    in_quote = False

    for line in lines:
        # Check for "On ... wrote:" pattern
        if _is_quote_header(line):
            in_quote = True
            continue

        # Check for > quoted lines
        stripped = line.strip()
        if stripped.startswith(">"):
            in_quote = True
            continue

        # Check for "-----Original Message-----"
        if "-----Original Message-----" in line:
            in_quote = True
            continue

        if not in_quote:
            result_lines.append(line)
        elif stripped and not stripped.startswith(">"):
            # Non-empty, non-quoted line after quote section
            # This might be a signature or footer, keep for now
            result_lines.append(line)

    return "\n".join(result_lines).strip()


def _is_quote_header(line: str) -> bool:
    """Check if line is a quote header like 'On Jan 31, 2026, Bob wrote:'."""
    line_lower = line.lower().strip()

    # Gmail style: "On Mon, Jan 31, 2026 at 10:00 AM Bob wrote:"
    if line_lower.startswith("on ") and "wrote:" in line_lower:
        return True

    # Outlook style (beginning of separator)
    return bool(line.strip().startswith("From:") or line.strip().startswith("Sent:"))


def _basic_signature_removal(text: str) -> tuple[str, str | None]:
    """
    Basic signature removal without Talon.

    Looks for common signature delimiters.
    """
    if not text:
        return "", None

    # Common signature delimiters
    delimiters = [
        "\n-- \n",  # Standard signature delimiter
        "\n--\n",
        "\n___",
        "\nBest regards",
        "\nBest,",
        "\nRegards,",
        "\nThanks,",
        "\nCheers,",
        "\nSent from my iPhone",
        "\nSent from my Android",
    ]

    for delimiter in delimiters:
        if delimiter in text:
            parts = text.split(delimiter, 1)
            clean = parts[0].strip()
            # Include the delimiter (without leading newline) in the signature
            sig_content = delimiter.lstrip("\n") + (parts[1] if len(parts) > 1 else "")
            return clean, sig_content.strip() if sig_content.strip() else None

    return text, None
