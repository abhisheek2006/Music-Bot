"""Cleanup service for removing old data."""

from __future__ import annotations

import asyncio
from datetime import datetime

from database.repositories.admin_repo import admin_repo
from database.repositories.search_repo import search_repo
from utils.logging_setup import get_logger

logger = get_logger("services.cleanup")


class CleanupService:
    """Service for cleaning up old data."""

    def __init__(self) -> None:
        self._running = False

    async def start(self, interval: int = 3600) -> None:
        """Start the cleanup scheduler.

        Args:
            interval: Cleanup interval in seconds.
        """
        self._running = True
        logger.info("Cleanup scheduler started", interval=interval)

        while self._running:
            try:
                await self._run_cleanup()
            except Exception as exc:
                logger.error("Cleanup task error", error=str(exc), exc_info=True)
            await asyncio.sleep(interval)

    async def stop(self) -> None:
        """Stop the cleanup scheduler."""
        self._running = False
        logger.info("Cleanup scheduler stopped")

    async def _run_cleanup(self) -> None:
        """Run a single cleanup cycle."""
        from config.config import settings

        logger.info("Running cleanup cycle")

        deleted_searches = await search_repo.delete_old_logs(
            settings.CLEANUP_DELETE_SEARCH_LOGS_DAYS
        )
        logger.info("Cleaned up old search logs", deleted=deleted_searches)

        cutoff = datetime.utcnow()
        from datetime import timedelta

        admin_cutoff = cutoff - timedelta(days=settings.CLEANUP_DELETE_OLD_LOGS_DAYS)
        from database.connection import get_collection

        admin_collection = get_collection("admin_logs")
        result = await admin_collection.delete_many({"created_at": {"$lt": admin_cutoff}})
        logger.info("Cleaned up old admin logs", deleted=result.deleted_count)

        await admin_repo.clear_old_logs(settings.CLEANUP_DELETE_OLD_LOGS_DAYS)


cleanup_service = CleanupService()
