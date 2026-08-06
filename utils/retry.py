"""Retry utilities with exponential backoff."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from utils.logging_setup import get_logger

logger = get_logger("utils.retry")

T = TypeVar("T")


class RetryError(Exception):
    """Raised when retries are exhausted."""


def _exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    multiplier: float = 2.0,
) -> float:
    """Calculate exponential backoff delay.

    Args:
        attempt: Current attempt number (0-indexed).
        base_delay: Base delay in seconds.
        max_delay: Maximum delay in seconds.
        multiplier: Backoff multiplier.

    Returns:
        Delay in seconds.
    """
    delay = base_delay * (multiplier**attempt)
    return min(delay, max_delay)


async def retry_async(  # noqa: UP047
    func: Callable[..., Awaitable[T]],
    *args: Any,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    context: str = "",
) -> T:
    """Retry an async function with exponential backoff.

    Args:
        func: Async function to retry.
        *args: Arguments to pass to the function.
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds.
        max_delay: Maximum delay in seconds.
        exceptions: Exceptions to catch and retry.
        context: Context string for logging.

    Returns:
        Result of the function.

    Raises:
        RetryError: If all retries fail.
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args)
        except exceptions as exc:
            last_exception = exc
            if attempt >= max_retries:
                logger.error(
                    "Retry exhausted",
                    context=context,
                    attempts=attempt + 1,
                    error=str(exc),
                )
                raise RetryError(f"Failed after {max_retries + 1} attempts: {exc}") from exc

            delay = _exponential_backoff(attempt, base_delay, max_delay)
            logger.warning(
                "Retrying",
                context=context,
                attempt=attempt + 1,
                max_retries=max_retries,
                delay=delay,
                error=str(exc),
            )
            await asyncio.sleep(delay)

    raise RetryError(f"Unexpected state: {last_exception}")


def retry_decorator(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    context: str = "",
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator for retrying async functions.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds.
        max_delay: Maximum delay in seconds.
        exceptions: Exceptions to catch and retry.
        context: Context string for logging.

    Returns:
        Decorator function.
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_async(
                func,
                *args,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                exceptions=exceptions,
                context=context or func.__name__,
            )

        return wrapper

    return decorator
