"""Ban repository for MongoDB operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from motor.core import AgnosticCollection

from database.connection import get_collection
from models import Ban
from utils.logging_setup import get_logger

logger = get_logger("database.ban_repo")


class BanRepository:
    """Repository for ban operations."""

    def __init__(self) -> None:
        self._collection_name = "bans"

    @property
    def collection(self) -> AgnosticCollection:
        """Get the bans collection."""
        return get_collection(self._collection_name)

    async def ban_user(self, user_id: int, admin_id: int, reason: str | None = None) -> Ban:
        """Ban a user.

        Args:
            user_id: User to ban.
            admin_id: Admin who banned.
            reason: Ban reason.

        Returns:
            Ban model.
        """
        ban = Ban(
            user_id=user_id,
            admin_id=admin_id,
            reason=reason,
            created_at=datetime.utcnow(),
        )
        doc = ban.model_dump()
        await self.collection.update_one(
            {"user_id": user_id},
            {"$set": doc},
            upsert=True,
        )
        from database.repositories.user_repo import user_repo

        await user_repo.ban_user(user_id)
        logger.info("User banned in repository", user_id=user_id, admin_id=admin_id)
        return ban

    async def unban_user(self, user_id: int) -> bool:
        """Unban a user.

        Args:
            user_id: User to unban.

        Returns:
            True if user was banned and is now unbanned.
        """
        result = await self.collection.delete_one({"user_id": user_id})
        from database.repositories.user_repo import user_repo

        await user_repo.unban_user(user_id)
        logger.info("User unbanned in repository", user_id=user_id)
        return result.deleted_count > 0

    async def is_banned(self, user_id: int) -> bool:
        """Check if a user is banned.

        Args:
            user_id: Telegram user ID.

        Returns:
            True if banned.
        """
        doc = await self.collection.find_one({"user_id": user_id}, {"_id": 1})
        return doc is not None

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        """Get all bans.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records.

        Returns:
            List of ban documents.
        """
        cursor = self.collection.find({}).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def count_all(self) -> int:
        """Count all bans.

        Returns:
            Number of bans.
        """
        return await self.collection.count_documents({})

    @staticmethod
    def _document_to_model(doc: dict[str, Any]) -> Ban:
        """Convert a MongoDB document to a Ban model."""
        doc.pop("_id", None)
        return Ban(**doc)


ban_repo = BanRepository()
