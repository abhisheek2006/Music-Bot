"""Command cooldown middleware."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from config.config import settings
from utils.logging_setup import get_logger

logger = get_logger("middlewares.cooldown")


class CooldownMiddleware:
    """Command cooldown middleware to prevent spam of the same command."""

    def __init__(self) -> None:
        self._user_cooldowns: dict[tuple[int, str], float] = {}
        self._lock = asyncio.Lock()
        self._cooldown_duration = settings.COMMAND_COOLDOWN

    async def _get_cooldown_key(self, user_id: int, command: str) -> tuple[int, str]:
        """Get the cooldown key for a user+command pair.

        Args:
            user_id: Telegram user ID.
            command: Command string.

        Returns:
            Cooldown key tuple.
        """
        return (user_id, command)

    async def _check_cooldown(self, client: Any, message: Any) -> bool:
        """Check if a command is on cooldown.

        Args:
            client: Kurigram client.
            message: Message object.

        Returns:
            True if command is on cooldown.
        """
        if not message.from_user or not message.text:
            return False

        command = message.text.split()[0].lower() if message.text else ""
        if not command:
            return False

        key = await self._get_cooldown_key(message.from_user.id, command)
        now = time.time()

        async with self._lock:
            last_time = self._user_cooldowns.get(key, 0)
            if now - last_time < self._cooldown_duration:
                remaining = int(self._cooldown_duration - (now - last_time))
                if remaining > 0:
                    try:
                        await message.reply_text(
                            f"⏳ Please wait {remaining} seconds before using this command again."
                        )
                    except Exception:
                        pass
                    logger.debug(
                        "Command on cooldown",
                        user_id=message.from_user.id,
                        command=command,
                        remaining=remaining,
                    )
                    return True

            self._user_cooldowns[key] = now
            return False

    async def _check_cooldown_callback(self, client: Any, query: Any) -> bool:
        """Check cooldown for callback queries.

        Args:
            client: Kurigram client.
            query: CallbackQuery object.

        Returns:
            True if action is on cooldown.
        """
        if not query.from_user or not query.data:
            return False

        action = query.data.split(":")[0] if ":" in query.data else query.data

        key = await self._get_cooldown_key(query.from_user.id, f"callback:{action}")
        now = time.time()

        async with self._lock:
            last_time = self._user_cooldowns.get(key, 0)
            if now - last_time < self._cooldown_duration:
                remaining = int(self._cooldown_duration - (now - last_time))
                if remaining > 0:
                    await query.answer(
                        f"⏳ Wait {remaining}s...",
                        show_alert=True,
                    )
                    return True

            self._user_cooldowns[key] = now
            return False

    async def on_message(self, client: Any, message: Any, nxt: Any) -> None:
        """Handle message cooldown."""
        if await self._check_cooldown(client, message):
            return

        await nxt(client, message)

    async def on_callback_query(self, client: Any, query: Any, nxt: Any) -> None:
        """Handle callback query cooldown."""
        if await self._check_cooldown_callback(client, query):
            return

        await nxt(client, query)

    async def cleanup(self) -> None:
        """Clean up expired cooldown entries."""
        now = time.time()
        async with self._lock:
            expired_keys = [
                key
                for key, timestamp in self._user_cooldowns.items()
                if now - timestamp > self._cooldown_duration * 10
            ]
            for key in expired_keys:
                del self._user_cooldowns[key]


cooldown_middleware = CooldownMiddleware()
