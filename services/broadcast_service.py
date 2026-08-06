"""Broadcast service for sending messages to all users."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from kurigram import AsyncClient, errors

from config.config import settings
from config.constants import Statuses
from database.repositories.broadcast_repo import broadcast_repo
from database.repositories.user_repo import user_repo
from utils.logging_setup import get_logger

logger = get_logger("services.broadcast")


class BroadcastService:
    """Service for broadcasting messages to users."""

    def __init__(self) -> None:
        self._paused = False

    async def send_broadcast(
        self,
        client: AsyncClient,
        admin_id: int,
        message: str,
        disable_web_page_preview: bool = True,
    ) -> dict[str, Any]:
        """Send a broadcast message to all users.

        Args:
            client: Kurigram client.
            admin_id: Admin sending the broadcast.
            message: Message to broadcast.
            disable_web_page_preview: Whether to disable web page preview.

        Returns:
            Broadcast statistics dictionary.
        """
        broadcast = await broadcast_repo.create(admin_id, message)
        broadcast_id = broadcast.model_dump().get("_id")

        users = await user_repo.get_all_users(limit=10000)
        total = len(users)
        success = 0
        failed = 0
        blocked = 0

        logger.info(
            "Broadcast started",
            admin_id=admin_id,
            total_users=total,
        )

        for i, user in enumerate(users):
            if self._paused:
                await asyncio.sleep(5)
                continue

            if user.banned:
                continue

            try:
                await client.send_message(
                    chat_id=user.user_id,
                    text=message,
                    disable_web_page_preview=disable_web_page_preview,
                )
                success += 1
            except (errors.UserIsBlocked, errors.UserNotMutualContact, errors.PeerIdInvalid):
                blocked += 1
                logger.debug("User blocked the bot", user_id=user.user_id)
            except Exception as exc:
                failed += 1
                logger.warning(
                    "Broadcast failed for user",
                    user_id=user.user_id,
                    error=str(exc),
                )

            if (i + 1) % 10 == 0:
                await asyncio.sleep(settings.BROADCAST_PAUSE)

        await broadcast_repo.update_status(
            broadcast_id,
            Statuses.BROADCAST_COMPLETED,
            success,
            failed + blocked,
        )

        stats = {
            "total": total,
            "success": success,
            "failed": failed,
            "blocked": blocked,
            "completed_at": datetime.utcnow(),
        }

        logger.info("Broadcast completed", **stats)
        return stats

    def pause(self) -> None:
        """Pause the broadcast."""
        self._paused = True
        logger.info("Broadcast paused")

    def resume(self) -> None:
        """Resume the broadcast."""
        self._paused = False
        logger.info("Broadcast resumed")

    async def get_stats(self) -> dict[str, Any]:
        """Get broadcast statistics.

        Returns:
            Statistics dictionary.
        """
        total = await broadcast_repo.count_all()
        return {"total_broadcasts": total}


broadcast_service = BroadcastService()
