"""Statistics service for tracking and aggregating metrics."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from database.repositories.ban_repo import ban_repo
from database.repositories.broadcast_repo import broadcast_repo
from database.repositories.credit_log_repo import credit_log_repo
from database.repositories.search_repo import search_repo
from database.repositories.statistics_repo import statistics_repo
from database.repositories.user_repo import user_repo
from utils.logging_setup import get_logger

logger = get_logger("services.statistics")


class StatisticsService:
    """Service for collecting and reporting statistics."""

    async def increment(self, stat_type: str, amount: int = 1) -> None:
        """Increment a daily statistic.

        Args:
            stat_type: Type of statistic.
            amount: Amount to increment.
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        await statistics_repo.increment(today, stat_type, amount)

    async def record_daily_stats(self) -> None:
        """Record daily aggregate statistics from other repositories."""
        today = datetime.utcnow().strftime("%Y-%m-%d")

        user_count = await user_repo.count_users()
        await statistics_repo.increment(today, "total_users", user_count)

        search_count = await search_repo.count_all()
        await statistics_repo.increment(today, "total_searches", search_count)

        credit_log_count = await credit_log_repo.count_all()
        await statistics_repo.increment(today, "total_credit_ops", credit_log_count)

        broadcast_count = await broadcast_repo.count_all()
        await statistics_repo.increment(today, "total_broadcasts", broadcast_count)

        ban_count = await ban_repo.count_all()
        await statistics_repo.increment(today, "total_bans", ban_count)

        logger.info("Daily statistics recorded", date=today)

    async def get_global_stats(self) -> dict[str, Any]:
        """Get global statistics.

        Returns:
            Dictionary of global statistics.
        """
        stats = await statistics_repo.get_global_stats()

        stats["total_users"] = await user_repo.count_users()
        stats["total_banned"] = await ban_repo.count_all()

        return stats

    async def get_daily_stats(self, days: int = 7) -> dict[str, Any]:
        """Get daily statistics for the past N days.

        Args:
            days: Number of days.

        Returns:
            Dictionary of daily statistics.
        """
        return await statistics_repo.get_daily_stats(days)

    async def get_monthly_stats(self, year: int, month: int) -> dict[str, Any]:
        """Get monthly statistics.

        Args:
            year: Year.
            month: Month.

        Returns:
            Dictionary of monthly statistics.
        """
        return await statistics_repo.get_monthly_stats(year, month)

    async def get_top_users(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top users by referral count.

        Args:
            limit: Maximum number of users.

        Returns:
            List of top users.
        """
        return await user_repo.get_top_users(limit)

    async def get_dashboard_stats(self) -> dict[str, Any]:
        """Get a dashboard summary of all statistics.

        Returns:
            Dashboard statistics dictionary.
        """
        global_stats = await self.get_global_stats()

        return {
            "total_users": global_stats.get("total_users", 0),
            "total_banned": global_stats.get("total_banned", 0),
            "total_searches": global_stats.get("total_searches", 0),
            "total_credits_added": global_stats.get("total_credits_added", 0),
            "total_credit_operations": global_stats.get("total_credit_ops", 0),
            "total_broadcasts": global_stats.get("total_broadcasts", 0),
        }


statistics_service = StatisticsService()
