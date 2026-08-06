"""Input validation utilities."""

from __future__ import annotations

import html
import re


def sanitize_string(value: str, max_length: int | None = None) -> str:
    """Sanitize a string value.

    Args:
        value: Input string.
        max_length: Maximum allowed length.

    Returns:
        Sanitized string.
    """
    value = str(value).strip()
    value = html.escape(value)
    if max_length is not None and len(value) > max_length:
        value = value[:max_length]
    return value


def validate_input(
    value: str,
    pattern: str | None = None,
    min_length: int = 1,
    max_length: int | None = None,
    allow_none: bool = False,
) -> str | None:
    """Validate user input against constraints.

    Args:
        value: Input value.
        pattern: Regex pattern to match.
        min_length: Minimum length.
        max_length: Maximum length.
        allow_none: Allow None/empty values.

    Returns:
        Sanitized value or None if invalid.
    """
    if value is None and allow_none:
        return None

    if value is None:
        return None

    sanitized = sanitize_string(value)

    if allow_none and not sanitized:
        return None

    if len(sanitized) < min_length:
        return None

    if max_length is not None and len(sanitized) > max_length:
        return None

    if pattern is not None and not re.match(pattern, sanitized):
        return None

    return sanitized


def validate_int(value: str, min_val: int | None = None, max_val: int | None = None) -> int | None:
    """Validate and parse an integer.

    Args:
        value: Input string.
        min_val: Minimum value.
        max_val: Maximum value.

    Returns:
        Integer or None if invalid.
    """
    try:
        num = int(str(value).strip())
        if min_val is not None and num < min_val:
            return None
        if max_val is not None and num > max_val:
            return None
        return num
    except (ValueError, TypeError):
        return None


def is_safe_text(value: str) -> bool:
    """Check if text is safe (no suspicious patterns).

    Args:
        value: Input text.

    Returns:
        True if text appears safe.
    """
    suspicious_patterns = [
        r"<script",
        r"javascript:",
        r"on\w+\s*=",
        r"data:text/html",
    ]
    for pattern in suspicious_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            return False
    return True


def strip_mentions(text: str) -> str:
    """Remove mentions from text.

    Args:
        text: Input text.

    Returns:
        Text with mentions removed.
    """
    return re.sub(r"@\w+", "", text)


def extract_urls(text: str) -> list[str]:
    """Extract URLs from text.

    Args:
        text: Input text.

    Returns:
        List of URLs found.
    """
    url_pattern = r"https?://[^\s]+"
    return re.findall(url_pattern, text)


def validate_search_query(query: str) -> tuple[bool, str]:
    """Validate a search query.

    Args:
        query: Search query string.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not query or not query.strip():
        return False, "Query cannot be empty."

    query = query.strip()

    if len(query) < 2:
        return False, "Query is too short. Minimum 2 characters."

    if len(query) > 100:
        return False, "Query is too long. Maximum 100 characters."

    if not is_safe_text(query):
        return False, "Query contains suspicious content."

    return True, ""
