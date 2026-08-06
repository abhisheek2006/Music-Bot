"""Input sanitization middleware."""

from __future__ import annotations

from typing import Any

from utils.logging_setup import get_logger
from utils.validators import is_safe_text, sanitize_string

logger = get_logger("middlewares.sanitization")


class SanitizationMiddleware:
    """Middleware for input sanitization and security checks."""

    MAX_TEXT_LENGTH = 4096
    MAX_CAPTION_LENGTH = 1024

    async def on_message(self, client: Any, message: Any, nxt: Any) -> None:
        """Handle message sanitization.

        Args:
            client: Kurigram client.
            message: Message object.
            nxt: Next handler.
        """
        if message.text:
            if len(message.text) > self.MAX_TEXT_LENGTH:
                try:
                    await message.reply_text(
                        f"❌ Message too long. Maximum {self.MAX_TEXT_LENGTH} characters."
                    )
                except Exception:
                    pass
                return

            if not is_safe_text(message.text):
                logger.warning(
                    "Unsafe content detected",
                    user_id=message.from_user.id if message.from_user else None,
                    text_preview=message.text[:100],
                )
                try:
                    await message.reply_text(
                        "❌ Your message contains suspicious content and was blocked."
                    )
                except Exception:
                    pass
                return

            message.text = sanitize_string(message.text, self.MAX_TEXT_LENGTH)

        await nxt(client, message)

    async def on_callback_query(self, client: Any, query: Any, nxt: Any) -> None:
        """Handle callback query sanitization.

        Args:
            client: Kurigram client.
            query: CallbackQuery object.
            nxt: Next handler.
        """
        if query.data:
            query.data = sanitize_string(query.data, 256)

        await nxt(client, query)


sanitization_middleware = SanitizationMiddleware()
