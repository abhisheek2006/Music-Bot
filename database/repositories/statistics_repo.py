"""Statistics repository for MongoDB operations."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from motor.core import AgnosticCollection

from database.connection import get_collection
from models import DailyStat
from utils.logging_setup import get_logger

logger = get_logger("database.statistics_repo")


class StatisticsRepository:
    """Repository for statistics operations."""

    def __init__(self) -> None:
        self._collection_name = "statistics"

    @property
    def collection(self) -> AgnosticCollection:
        """Get the statistics collection."""
        return get_collection(self._collection_name)

    async def increment(self, date: str, stat_type: str, amount: int = 1) -> None:
        """Increment a daily statistic.

        Args:
            date: Date string (YYYY-MM-DD).
            stat_type: Type of statistic.
            amount: Amount to increment.
        """
        await self.collection.find_one_and_update(
            {"date": date, "type": stat_type},
            {"$inc": {"value": amount}},
            upsert=True,
        )

    async def get_global_stats(self) -> dict[str, Any]:
        """Get global statistics.

        Returns:
            Dictionary of statistics.
        """
        pipeline = [
            {"$group": {"_id": None, "total": {"$sum": "$value"}}},
            {"$sort": {"total": -1}},
        ]
        cursor = self.collection.aggregate(pipeline)
        await cursor.to_list(length=None)

        stats = {
            "total_searches": 0,
            "total_users": 0,
            "total_credits_added": 0,
            "total_credits_deducted": 0,
            "total_broadcasts": 0,
        }

        cursor_types = self.collection.find({"type": "daily_searches"})
        docs = await cursor_types.to_list(length=None)
        for doc in docs:
            stats["total_searches"] += doc.get("value", 0)

        cursor_users = self.collection.find({"type": "daily_new_users"})
        docs = await cursor_users.to_list(length=None)
        for doc in docs:
            stats["total_users"] += doc.get("value", 0)

        cursor_credits = self.collection.find({"type": "daily_credits_added"})
        docs = await cursor_credits.to_list(length=None)
        for doc in docs:
            stats["total_credits_added"] += doc.get("value", 0)

        cursor_deducted = self.collection.find({"type": "daily_credits_deducted"})
        docs = await cursor_deducted.to_list(length=None)
        for doc in docs:
            stats["total_credits_deducted"] += doc.get("value", 0)

        cursor_broadcasts = self.collection.find({"type": "daily_broadcasts"})
        docs = await cursor_broadcasts.to_list(length=None)
        for doc in docs:
            stats["total_broadcasts"] += doc.get("value", 0)

        return stats

    async def get_daily_stats(self, days: int = 7) -> dict[str, list[dict[str, Any]]]:
        """Get daily statistics for the past N days.

        Args:
            days: Number of days.

        Returns:
            Dictionary of daily statistics.
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

        pipeline = [
            {"$match": {"date": {"$gte": cutoff_date}}},
            {"$sort": {"date": 1}},
            {
                "$group": {
                    "_id": "$type",
                    "data": {"$push": {"date": "$date", "value": "$value"}},
                }
            },
        ]
        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)

        return {doc["_id"]: doc["data"] for doc in results}

    async def get_monthly_stats(self, year: int, month: int) -> dict[str, Any]:
        """Get monthly statistics.

        Args:
            year: Year.
            month: Month.

        Returns:
            Dictionary of monthly statistics.
        """
        from calendar import monthrange

        _, last_day = monthrange(year, month)
        start_date = f"{year:04d}-{month:02d}-01"
        end_date = f"{year:04d}-{month:02d}-{last_day:02d}"

        pipeline = [
            {"$match": {"date": {"$gte": start_date, "$lte": end_date}}},
            {"$sort": {"date": 1}},
            {
                "$group": {
                    "_id": "$type",
                    "data": {"$push": {"date": "$date", "value": "$value"}},
                    "total": {"$sum": "$value"},
                }
            },
        ]
        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)

        return {doc["_id"]: {"total": doc["total"], "data": doc["data"]} for doc in results}

    @staticmethod
    def _document_to_model(doc: dict[str, Any]) -> DailyStat:
        """Convert a MongoDB document to a DailyStat model."""
        doc.pop("_id", None)
        return DailyStat(**doc)


statistics_repo = StatisticsRepository()
