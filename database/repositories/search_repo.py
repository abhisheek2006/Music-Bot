"""Search repository for MongoDB operations."""

from __future__ import annotations

from typing import Any

from motor.core import AgnosticCollection

from database.connection import get_collection
from models import Search
from utils.logging_setup import get_logger

logger = get_logger("database.search_repo")


class SearchRepository:
    """Repository for search log-related database operations."""

    def __init__(self) -> None:
        self._collection_name = "searches"

    @property
    def collection(self) -> AgnosticCollection:
        """Get the searches collection."""
        return get_collection(self._collection_name)

    async def create(self, search_data: dict[str, Any]) -> Search:
        """Create a search log entry.

        Args:
            search_data: Search log data.

        Returns:
            Search model.
        """
        search = Search(**search_data)
        doc = search.model_dump()
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return search

    async def get_user_history(self, user_id: int, limit: int = 10, skip: int = 0) -> list[Search]:
        """Get search history for a user.

        Args:
            user_id: Telegram user ID.
            limit: Maximum number of records.
            skip: Number of records to skip.

        Returns:
            List of Search models.
        """
        cursor = (
            self.collection.find({"user_id": user_id})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [self._document_to_model(doc) for doc in docs]

    async def count_user_history(self, user_id: int) -> int:
        """Count search history for a user.

        Args:
            user_id: Telegram user ID.

        Returns:
            Number of search records.
        """
        return await self.collection.count_documents({"user_id": user_id})

    async def get_recent(self, user_id: int, limit: int = 5) -> list[Search]:
        """Get recent searches for a user.

        Args:
            user_id: Telegram user ID.
            limit: Maximum number of records.

        Returns:
            List of Search models.
        """
        cursor = (
            self.collection.find({"user_id": user_id, "success": True})
            .sort("created_at", -1)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [self._document_to_model(doc) for doc in docs]

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Search]:
        """Get all search logs with pagination.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records.

        Returns:
            List of Search models.
        """
        cursor = self.collection.find({}).sort("created_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._document_to_model(doc) for doc in docs]

    async def count_all(self) -> int:
        """Count all search logs.

        Returns:
            Number of search records.
        """
        return await self.collection.count_documents({})

    async def get_by_user(self, user_id: int, limit: int = 50) -> list[Search]:
        """Get all searches by a specific user.

        Args:
            user_id: Telegram user ID.
            limit: Maximum number of records.

        Returns:
            List of Search models.
        """
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._document_to_model(doc) for doc in docs]

    async def clear_user_history(self, user_id: int) -> int:
        """Clear search history for a user.

        Args:
            user_id: Telegram user ID.

        Returns:
            Number of deleted records.
        """
        result = await self.collection.delete_many({"user_id": user_id})
        return result.deleted_count

    async def delete_old_logs(self, days: int) -> int:
        """Delete search logs older than X days.

        Args:
            days: Number of days.

        Returns:
            Number of deleted records.
        """
        from datetime import datetime, timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.collection.delete_many({"created_at": {"$lt": cutoff}})
        return result.deleted_count

    @staticmethod
    def _document_to_model(doc: dict[str, Any]) -> Search:
        """Convert a MongoDB document to a Search model."""
        doc.pop("_id", None)
        return Search(**doc)


search_repo = SearchRepository()
