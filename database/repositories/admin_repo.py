"""Admin repository for MongoDB operations."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from motor.core import AgnosticCollection

from database.connection import get_collection
from models import AdminAction
from utils.logging_setup import get_logger

logger = get_logger("database.admin_repo")


class AdminRepository:
    """Repository for admin action logging."""

    def __init__(self) -> None:
        self._collection_name = "admin_logs"

    @property
    def collection(self) -> AgnosticCollection:
        """Get the admin_logs collection."""
        return get_collection(self._collection_name)

    async def log_action(
        self,
        admin_id: int,
        action: str,
        target_id: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> AdminAction:
        """Log an admin action.

        Args:
            admin_id: Admin user ID.
            action: Action name.
            target_id: Target user ID.
            details: Additional details.

        Returns:
            AdminAction model.
        """
        action_log = AdminAction(
            admin_id=admin_id,
            action=action,
            target_id=target_id,
            details=details,
            created_at=datetime.utcnow(),
        )
        doc = action_log.model_dump()
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        logger.info(
            "Admin action logged",
            admin_id=admin_id,
            action=action,
            target_id=target_id,
        )
        return action_log

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        """Get all admin logs.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records.

        Returns:
            List of admin log documents.
        """
        cursor = self.collection.find({}).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def count_all(self) -> int:
        """Count all admin logs.

        Returns:
            Number of admin logs.
        """
        return await self.collection.count_documents({})

    async def clear_old_logs(self, days: int) -> int:
        """Delete admin logs older than X days.

        Args:
            days: Number of days.

        Returns:
            Number of deleted records.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.collection.delete_many({"created_at": {"$lt": cutoff}})
        return result.deleted_count

    @staticmethod
    def _document_to_model(doc: dict[str, Any]) -> AdminAction:
        """Convert a MongoDB document to an AdminAction model."""
        doc.pop("_id", None)
        return AdminAction(**doc)


admin_repo = AdminRepository()
