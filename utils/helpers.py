"""Helper utilities for the bot."""

from __future__ import annotations

import html
import re
from datetime import datetime, timedelta
from typing import Any

from config.constants import RegexPatterns


def format_user_mention(user_id: int, first_name: str | None = None) -> str:
    """Format a user mention in HTML.

    Args:
        user_id: Telegram user ID.
        first_name: User's first name.

    Returns:
        HTML-formatted mention.
    """
    name = html.escape(first_name or str(user_id))
    return f'<a href="tg://user?id={user_id}">{name}</a>'


def format_datetime(dt: datetime | None) -> str:
    """Format a datetime string.

    Args:
        dt: Datetime to format.

    Returns:
        Formatted string.
    """
    if dt is None:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def parse_callback_data(data: str, delimiter: str = ":") -> list[str]:
    """Parse callback data into parts.

    Args:
        data: Callback data string.
        delimiter: Delimiter to split on.

    Returns:
        List of parts.
    """
    return data.split(delimiter)


def validate_phone_number(value: str) -> bool:
    """Validate a phone number.

    Args:
        value: Phone number string.

    Returns:
        True if valid.
    """
    return bool(re.match(RegexPatterns.PHONE_NUMBER, value))


def validate_user_id(value: str) -> int | None:
    """Validate and parse a user ID.

    Args:
        value: User ID string.

    Returns:
        Integer user ID or None.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def validate_credit_amount(value: str) -> int | None:
    """Validate and parse a credit amount.

    Args:
        value: Amount string.

    Returns:
        Integer amount or None.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def sanitize_text(text: str, max_length: int = 4096) -> str:
    """Sanitize text input.

    Args:
        text: Input text.
        max_length: Maximum length.

    Returns:
        Sanitized text.
    """
    text = text.strip()
    text = html.escape(text)
    if len(text) > max_length:
        text = text[:max_length]
    return text


def truncate(text: str, max_length: int = 100) -> str:
    """Truncate text to a maximum length.

    Args:
        text: Input text.
        max_length: Maximum length.

    Returns:
        Truncated text with ellipsis if needed.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def format_credits(credits: int) -> str:
    """Format a credit count with appropriate emoji.

    Args:
        credits: Number of credits.

    Returns:
        Formatted string.
    """
    if credits == 0:
        return "0 💳"
    if credits < 0:
        return f"-{abs(credits)} 💳"
    return f"{credits} 💳"


def get_date_range(period: str = "daily") -> tuple[str, str]:
    """Get date range for statistics.

    Args:
        period: Period type (daily, weekly, monthly).

    Returns:
        Tuple of (start_date, end_date) as YYYY-MM-DD strings.
    """
    now = datetime.utcnow()

    if period == "daily":
        return now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")

    if period == "weekly":
        start = now - timedelta(days=7)
        return start.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")

    if period == "monthly":
        start = now - timedelta(days=30)
        return start.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")

    return now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")


def format_size(size_bytes: int) -> str:
    """Format a byte size into human-readable string.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Human-readable size string.
    """
    if size_bytes == 0:
        return "0B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.1f}{units[i]}"


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries.

    Args:
        base: Base dictionary.
        override: Override dictionary.

    Returns:
        Merged dictionary.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
