"""Logging middleware for request/response tracking."""

from __future__ import annotations

import time
from typing import Any

from utils.logging_setup import get_logger

logger = get_logger("middlewares.logging")


class LoggingMiddleware:
    """Middleware for logging all incoming requests and responses."""

    async def on_message(self, client: Any, message: Any, nxt: Any) -> None:
        """Log message processing.

        Args:
            client: Kurigram client.
            message: Message object.
            nxt: Next handler.
        """
        start_time = time.time()

        user_id = message.from_user.id if message.from_user else None
        username = message.from_user.username if message.from_user else None
        chat_id = message.chat.id if message.chat else None
        text_preview = message.text[:50] if message.text else "(media/empty)"

        logger.info(
            "Incoming message",
            user_id=user_id,
            username=username,
            chat_id=chat_id,
            content_preview=text_preview,
            is_bot=message.from_user.is_bot if message.from_user else None,
        )

        try:
            await nxt(client, message)
        except Exception as exc:
            logger.error(
                "Error processing message",
                user_id=user_id,
                error=str(exc),
                input=text_preview,
                exc_info=True,
            )
            raise

        duration = time.time() - start_time
        logger.info(
            "Message processed",
            user_id=user_id,
            duration_ms=round(duration * 1000, 2),
            content_preview=text_preview,
        )

    async def on_callback_query(self, client: Any, query: Any, nxt: Any) -> None:
        """Log callback query processing.

        Args:
            client: Kurigram client.
            query: CallbackQuery object.
            nxt: Next handler.
        """
        start_time = time.time()

        user_id = query.from_user.id if query.from_user else None
        username = query.from_user.username if query.from_user else None
        data = query.data

        logger.info(
            "Incoming callback query",
            user_id=user_id,
            username=username,
            callback_data=data,
        )

        try:
            await nxt(client, query)
        except Exception as exc:
            logger.error(
                "Error processing callback query",
                user_id=user_id,
                error=str(exc),
                callback_data=data,
                exc_info=True,
            )
            raise

        duration = time.time() - start_time
        logger.info(
            "Callback processed",
            user_id=user_id,
            callback_data=data,
            duration_ms=round(duration * 1000, 2),
        )


logging_middleware = LoggingMiddleware()
