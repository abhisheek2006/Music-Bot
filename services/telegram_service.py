"""Telegram service for bot operations."""

from __future__ import annotations

from typing import Any

from kurigram import AsyncClient, errors

from utils.logging_setup import get_logger

logger = get_logger("services.telegram")


class TelegramService:
    """Service for Telegram API operations."""

    def __init__(self) -> None:
        self._connected = False
        self._me: Any = None

    async def initialize(self, client: AsyncClient) -> bool:
        """Initialize the Telegram service.

        Args:
            client: Kurigram client.

        Returns:
            True if initialization successful.
        """
        try:
            self._me = await client.get_me()
            self._connected = True
            logger.info(
                "Telegram service initialized",
                bot_username=self._me.username,
                bot_id=self._me.id,
            )
            return True
        except Exception as exc:
            logger.error("Telegram service initialization failed", error=str(exc))
            self._connected = False
            return False

    async def check_connection(self, client: AsyncClient) -> bool:
        """Check if the bot is connected.

        Args:
            client: Kurigram client.

        Returns:
            True if connected.
        """
        try:
            await client.get_me()
            self._connected = True
            return True
        except Exception as exc:
            logger.warning("Telegram connection check failed", error=str(exc))
            self._connected = False
            return False

    async def reconnect(self, client: AsyncClient) -> bool:
        """Attempt to reconnect to Telegram.

        Args:
            client: Kurigram client.

        Returns:
            True if reconnection successful.
        """
        from utils.retry import RetryError, retry_async

        async def _reconnect() -> bool:
            try:
                self._me = await client.get_me()
                self._connected = True
                logger.info("Telegram reconnected successfully")
                return True
            except Exception:
                raise

        try:
            return await retry_async(
                _reconnect,
                max_retries=3,
                base_delay=2.0,
                max_delay=30.0,
                exceptions=(Exception,),
                context="telegram_reconnect",
            )
        except RetryError:
            logger.error("Telegram reconnection failed after retries")
            self._connected = False
            return False

    async def send_message_safe(
        self,
        client: AsyncClient,
        chat_id: int,
        text: str,
        **kwargs: Any,
    ) -> bool:
        """Safely send a message, handling errors gracefully.

        Args:
            client: Kurigram client.
            chat_id: Target chat ID.
            text: Message text.
            **kwargs: Additional message parameters.

        Returns:
            True if message sent successfully.
        """
        try:
            await client.send_message(chat_id=chat_id, text=text, **kwargs)
            return True
        except (errors.UserIsBlocked, errors.PeerIdInvalid) as exc:
            logger.warning("User blocked/not found", chat_id=chat_id, error=str(exc))
            return False
        except Exception as exc:
            logger.error("Failed to send message", chat_id=chat_id, error=str(exc))
            return False

    async def get_user_info(self, client: AsyncClient, user_id: int) -> dict[str, Any] | None:
        """Get user information from Telegram.

        Args:
            client: Kurigram client.
            user_id: Telegram user ID.

        Returns:
            User info dictionary or None.
        """
        try:
            user = await client.get_users(user_id)
            if user:
                return {
                    "user_id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username,
                    "language_code": user.language_code if hasattr(user, "language_code") else None,
                    "is_bot": user.is_bot,
                    "is_verified": getattr(user, "is_verified", False),
                }
        except errors.PeerIdInvalid:
            logger.warning("Peer ID invalid", user_id=user_id)
        except Exception as exc:
            logger.warning("Failed to get user info", user_id=user_id, error=str(exc))
        return None

    async def get_channel_info(self, client: AsyncClient, channel: str) -> dict[str, Any] | None:
        """Get channel/channel info from Telegram.

        Args:
            client: Kurigram client.
            channel: Channel username.

        Returns:
            Channel info dictionary or None.
        """
        try:
            chat = await client.get_chat(channel)
            return {
                "id": chat.id,
                "title": chat.title,
                "username": chat.username,
                "members_count": getattr(chat, "members_count", 0),
                "is_channel": getattr(chat, "is_channel", False),
            }
        except Exception as exc:
            logger.warning("Failed to get channel info", channel=channel, error=str(exc))
            return None

    async def get_forceshow_link(self, channel: str) -> str:
        """Get an invite link for a channel.

        Args:
            channel: Channel username.

        Returns:
            Invite link.
        """

        clean_channel = channel.lstrip("@")
        if clean_channel.startswith("t.me") or clean_channel.startswith("https"):
            return channel
        return f"https://t.me/{clean_channel}"


telegram_service = TelegramService()
