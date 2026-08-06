"""Admin middleware to check admin permissions."""

from __future__ import annotations

import asyncio
from typing import Any

from config.config import settings
from database.repositories.ban_repo import ban_repo
from database.repositories.user_repo import user_repo
from utils.logging_setup import get_logger

logger = get_logger("middlewares.admin")


class AdminMiddleware:
    """Middleware to check admin status and ban status for commands."""

    def __init__(self) -> None:
        self.admin_ids: set[int] = set(settings.ADMIN_IDS)
        self._lock = asyncio.Lock()

    async def _is_admin(self, user_id: int) -> bool:
        """Check if a user is an admin.

        Args:
            user_id: Telegram user ID.

        Returns:
            True if user is an admin.
        """
        if user_id in self.admin_ids:
            return True

        async with self._lock:
            if user_id in self.admin_ids:
                return True

            user = await user_repo.get_by_id(user_id)
            if user and user.is_admin:
                self.admin_ids.add(user_id)
                return True

            return False

    async def _is_banned(self, user_id: int) -> bool:
        """Check if a user is banned.

        Args:
            user_id: Telegram user ID.

        Returns:
            True if user is banned.
        """
        return await ban_repo.is_banned(user_id)

    async def on_message(self, client: Any, message: Any, nxt: Any) -> None:
        """Handle message middleware.

        Args:
            client: Kurigram client.
            message: Message object.
            nxt: Next handler.
        """
        if not message.from_user:
            await nxt(client, message)
            return

        user_id = message.from_user.id

        if await self._is_banned(user_id):
            logger.warning("Banned user attempted to interact", user_id=user_id)
            try:
                await message.reply_text("❌ You are banned from using this bot.")
            except Exception:
                pass
            return

        from config.constants import Messages
        from database.repositories.setting_repo import setting_repo

        maintenance = await setting_repo.get_maintenance_mode()
        if maintenance and not await self._is_admin(user_id):
            try:
                await message.reply_text(
                    "🔧 The bot is currently under maintenance. Please try again later."
                )
            except Exception:
                pass
            return

        message.is_admin = await self._is_admin(user_id)
        message.requires_admin = False

        admin_commands = ["/addcredit", "/removecredit", "/setcredit", "/creditlog"]
        if message.text and any(message.text.startswith(cmd) for cmd in admin_commands):
            message.requires_admin = True
            if not message.is_admin:
                await message.reply_text(Messages.NOT_ADMIN)
                return

        await nxt(client, message)

    async def on_callback_query(self, client: Any, query: Any, nxt: Any) -> None:
        """Handle callback query middleware.

        Args:
            client: Kurigram client.
            query: CallbackQuery object.
            nxt: Next handler.
        """
        if not query.from_user:
            await nxt(client, query)
            return

        user_id = query.from_user.id

        if await self._is_banned(user_id):
            await query.answer("❌ You are banned.", show_alert=True)
            return

        query.is_admin = await self._is_admin(user_id)
        query.requires_admin = False

        if query.data and query.data.startswith("admin:"):
            query.requires_admin = True
            if not query.is_admin:
                await query.answer("❌ Admin only.", show_alert=True)
                return

        await nxt(client, query)

    async def reload_admins(self) -> None:
        """Reload admin IDs from the environment."""
        self.admin_ids = set(settings.ADMIN_IDS)


admin_middleware = AdminMiddleware()
