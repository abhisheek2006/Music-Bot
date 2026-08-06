"""Flood protection middleware."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Any

from config.config import settings
from utils.logging_setup import get_logger

logger = get_logger("middlewares.flood_protection")


class FloodProtectionMiddleware:
    """Flood protection middleware to prevent spam and abuse."""

    def __init__(self) -> None:
        self._user_timestamps: defaultdict[int, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._threshold = settings.FLOOD_THRESHOLD
        self._window = settings.FLOOD_WINDOW
        self._banned_users: set[int] = set()
        self._banned_duration = 300

    async def _check_flood(self, user_id: int) -> bool:
        """Check if user is flooding.

        Args:
            user_id: Telegram user ID.

        Returns:
            True if user is flooding.
        """
        now = time.time()
        cutoff = now - self._window

        async with self._lock:
            self._user_timestamps[user_id] = [
                ts for ts in self._user_timestamps[user_id] if ts > cutoff
            ]

            if len(self._user_timestamps[user_id]) >= self._threshold:
                self._banned_users.add(user_id)
                logger.warning(
                    "User blocked by flood protection",
                    user_id=user_id,
                    message_count=len(self._user_timestamps[user_id]),
                )
                return True

            self._user_timestamps[user_id].append(now)
            return False

    async def _is_flood_banned(self, user_id: int) -> bool:
        """Check if user is flood-banned.

        Args:
            user_id: Telegram user ID.

        Returns:
            True if user is flood-banned.
        """
        return user_id in self._banned_users

    async def _unban_after_delay(self, user_id: int) -> None:
        """Unban a flood-banned user after the ban duration.

        Args:
            user_id: Telegram user ID.
        """
        await asyncio.sleep(self._banned_duration)
        self._banned_users.discard(user_id)
        self._user_timestamps[user_id].clear()
        logger.info("Flood ban expired", user_id=user_id)

    async def on_message(self, client: Any, message: Any, nxt: Any) -> None:
        """Handle message flood protection."""
        if not message.from_user:
            await nxt(client, message)
            return

        user_id = message.from_user.id

        if await self._is_flood_banned(user_id):
            try:
                await message.reply_text(
                    "🚫 You are temporarily blocked due to flooding. Please try again later."
                )
            except Exception:
                pass
            return

        if await self._check_flood(user_id):
            asyncio.create_task(self._unban_after_delay(user_id))
            try:
                await message.reply_text(
                    "🚫 Flood protection activated! You are temporarily blocked."
                )
            except Exception:
                pass
            return

        await nxt(client, message)


flood_middleware = FloodProtectionMiddleware()
