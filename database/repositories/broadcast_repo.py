"""Broadcast repository for MongoDB operations."""

from __future__ import annotations

from typing import Any

from motor.core import AgnosticCollection

from database.connection import get_collection
from models import Broadcast
from utils.logging_setup import get_logger

logger = get_logger("database.broadcast_repo")


class BroadcastRepository:
    """Repository for broadcast message operations."""

    def __init__(self) -> None:
        self._collection_name = "broadcasts"

    @property
    def collection(self) -> AgnosticCollection:
        """Get the broadcasts collection."""
        return get_collection(self._collection_name)

    async def create(self, admin_id: int, message: str) -> Broadcast:
        """Create a broadcast record.

        Args:
            admin_id: Admin who initiated the broadcast.
            message: Message content.

        Returns:
            Broadcast model.
        """
        broadcast = Broadcast(admin_id=admin_id, message=message)
        doc = broadcast.model_dump()
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return broadcast

    async def update_status(
        self,
        broadcast_id: Any,
        status: str,
        recipient_count: int = 0,
        error_count: int = 0,
    ) -> None:
        """Update broadcast status.

        Args:
            broadcast_id: Broadcast document ID.
            status: New status.
            recipient_count: Number of successful recipients.
            error_count: Number of errors.
        """
        from datetime import datetime

        await self.collection.update_one(
            {"_id": broadcast_id},
            {
                "$set": {
                    "status": status,
                    "recipient_count": recipient_count,
                    "error_count": error_count,
                    "completed_at": datetime.utcnow() if status == "completed" else None,
                }
            },
        )

    async def get_all(self, skip: int = 0, limit: int = 50) -> list[dict[str, Any]]:
        """Get all broadcast records.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records.

        Returns:
            List of broadcast documents.
        """
        cursor = self.collection.find({}).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def count_all(self) -> int:
        """Count all broadcast messages.

        Returns:
            Number of broadcast records.
        """
        return await self.collection.count_documents({})

    @staticmethod
    def _document_to_model(doc: dict[str, Any]) -> Broadcast:
        """Convert a MongoDB document to a Broadcast model."""
        doc.pop("_id", None)
        return Broadcast(**doc)


broadcast_repo = BroadcastRepository()
