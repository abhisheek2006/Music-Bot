"""Rate limiter middleware using an in-memory store with optional Redis backend."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from config.config import settings
from utils.logging_setup import get_logger

logger = get_logger("middlewares.rate_limiter")


class RateLimiterMiddleware:
    """Rate limiting middleware using a sliding window approach.

    Uses in-memory storage by default. Falls back gracefully if Redis is unavailable.
    """

    def __init__(self) -> None:
        self._requests: dict[int, list[float]] = {}
        self._lock = asyncio.Lock()
        self._window = settings.RATE_LIMIT_WINDOW
        self._max_requests = settings.RATE_LIMIT_MAX_REQUESTS

    async def _check_rate_limit(self, user_id: int) -> tuple[bool, int]:
        """Check if a user has exceeded the rate limit.

        Args:
            user_id: Telegram user ID.

        Returns:
            Tuple of (is_allowed, remaining_requests).
        """
        now = time.time()
        cutoff = now - self._window

        async with self._lock:
            if user_id not in self._requests:
                self._requests[user_id] = []

            self._requests[user_id] = [ts for ts in self._requests[user_id] if ts > cutoff]

            if len(self._requests[user_id]) >= self._max_requests:
                retry_after = int(self._window - (now - self._requests[user_id][0]))
                logger.warning(
                    "Rate limit exceeded",
                    user_id=user_id,
                    retry_after=retry_after,
                )
                return False, 0

            self._requests[user_id].append(now)
            remaining = self._max_requests - len(self._requests[user_id])
            return True, remaining

    async def _cleanup(self) -> None:
        """Periodically clean up old rate limit entries."""
        while True:
            await asyncio.sleep(60)
            now = time.time()
            cutoff = now - self._window
            async with self._lock:
                keys_to_remove = []
                for user_id, timestamps in self._requests.items():
                    self._requests[user_id] = [ts for ts in timestamps if ts > cutoff]
                    if not self._requests[user_id]:
                        keys_to_remove.append(user_id)
                for key in keys_to_remove:
                    del self._requests[key]

    async def on_message(self, client: Any, message: Any, nxt: Any) -> None:
        """Handle message rate limiting."""
        if not message.from_user:
            await nxt(client, message)
            return

        allowed, remaining = await self._check_rate_limit(message.from_user.id)
        if not allowed:
            try:
                await message.reply_text(
                    f"🚫 Rate limit exceeded. Please wait before sending more requests.\n"
                    f"Limit: {self._max_requests} requests per {self._window} seconds."
                )
            except Exception:
                pass
            return

        await nxt(client, message)

    async def on_callback_query(self, client: Any, query: Any, nxt: Any) -> None:
        """Handle callback query rate limiting."""
        if not query.from_user:
            await nxt(client, query)
            return

        allowed, remaining = await self._check_rate_limit(query.from_user.id)
        if not allowed:
            await query.answer(
                "🚫 Rate limit exceeded. Please wait.",
                show_alert=True,
            )
            return

        await nxt(client, query)


rate_limiter = RateLimiterMiddleware()
