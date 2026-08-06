"""User repository for MongoDB operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from motor.core import AgnosticCollection

from database.connection import get_collection
from models import User
from utils.logging_setup import get_logger

logger = get_logger("database.user_repo")


class UserRepository:
    """Repository for user-related database operations."""

    def __init__(self) -> None:
        self._collection_name = "users"

    @property
    def collection(self) -> AgnosticCollection:
        """Get the users collection."""
        return get_collection(self._collection_name)

    async def create_or_update(self, user_data: dict[str, Any]) -> User:
        """Create or update a user.

        Args:
            user_data: User data dictionary.

        Returns:
            User: Created or updated user.
        """
        filter_query = {"user_id": user_data["user_id"]}
        update_data = {
            "$set": {
                "username": user_data.get("username"),
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
                "last_seen": datetime.utcnow(),
                "language_code": user_data.get("language_code"),
            },
            "$setOnInsert": {
                "created_at": datetime.utcnow(),
                "credits": user_data.get("credits", 0),
                "is_admin": user_data.get("is_admin", False),
                "banned": False,
                "referrer_id": user_data.get("referrer_id"),
                "referral_count": 0,
            },
        }
        result = await self.collection.find_one_and_update(
            filter_query, update_data, upsert=True, return_document=True
        )
        return self._document_to_model(result)

    async def get_by_id(self, user_id: int) -> User | None:
        """Get a user by ID.

        Args:
            user_id: Telegram user ID.

        Returns:
            User or None.
        """
        doc = await self.collection.find_one({"user_id": user_id})
        if doc:
            return self._document_to_model(doc)
        return None

    async def update(self, user_id: int, update_data: dict[str, Any]) -> User | None:
        """Update a user.

        Args:
            user_id: Telegram user ID.
            update_data: Data to update.

        Returns:
            Updated User or None.
        """
        result = await self.collection.find_one_and_update(
            {"user_id": user_id}, {"$set": update_data}, return_document=True
        )
        if result:
            return self._document_to_model(result)
        return None

    async def add_credits(self, user_id: int, amount: int) -> int:
        """Add credits to a user.

        Args:
            user_id: Telegram user ID.
            amount: Amount to add.

        Returns:
            Updated credit balance.
        """
        result = await self.collection.find_one_and_update(
            {"user_id": user_id},
            {"$inc": {"credits": amount}},
            return_document=True,
        )
        if result:
            return result.get("credits", 0)
        return 0

    async def deduct_credits(self, user_id: int, amount: int = 1) -> int | None:
        """Deduct credits from a user.

        Args:
            user_id: Telegram user ID.
            amount: Amount to deduct.

        Returns:
            Updated credit balance or None if insufficient.
        """
        result = await self.collection.find_one_and_update(
            {"user_id": user_id, "credits": {"$gte": amount}},
            {"$inc": {"credits": -amount}},
            return_document=True,
        )
        if result:
            return result.get("credits", 0)
        return None

    async def get_credits(self, user_id: int) -> int:
        """Get a user's credit balance.

        Args:
            user_id: Telegram user ID.

        Returns:
            Credit balance.
        """
        doc = await self.collection.find_one({"user_id": user_id}, {"credits": 1, "_id": 0})
        if doc:
            return doc.get("credits", 0)
        return 0

    async def is_banned(self, user_id: int) -> bool:
        """Check if a user is banned.

        Args:
            user_id: Telegram user ID.

        Returns:
            True if banned.
        """
        doc = await self.collection.find_one({"user_id": user_id}, {"banned": 1, "_id": 0})
        return bool(doc and doc.get("banned", False))

    async def ban_user(self, user_id: int) -> None:
        """Ban a user.

        Args:
            user_id: Telegram user ID.
        """
        await self.collection.update_one({"user_id": user_id}, {"$set": {"banned": True}})
        logger.info("User banned", user_id=user_id)

    async def unban_user(self, user_id: int) -> None:
        """Unban a user.

        Args:
            user_id: Telegram user ID.
        """
        await self.collection.update_one({"user_id": user_id}, {"$set": {"banned": False}})
        logger.info("User unbanned", user_id=user_id)

    async def set_admin(self, user_id: int, is_admin: bool) -> None:
        """Set admin status for a user.

        Args:
            user_id: Telegram user ID.
            is_admin: Admin status.
        """
        await self.collection.update_one({"user_id": user_id}, {"$set": {"is_admin": is_admin}})

    async def get_admin_ids(self) -> list[int]:
        """Get all admin user IDs.

        Returns:
            List of admin user IDs.
        """
        cursor = self.collection.find({"is_admin": True}, {"user_id": 1, "_id": 0})
        docs = await cursor.to_list(length=None)
        return [doc["user_id"] for doc in docs]

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users with pagination.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records.

        Returns:
            List of users.
        """
        cursor = self.collection.find({}).sort("created_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._document_to_model(doc) for doc in docs]

    async def count_users(self) -> int:
        """Count all users.

        Returns:
            Number of users.
        """
        return await self.collection.count_documents({})

    async def count_banned(self) -> int:
        """Count banned users.

        Returns:
            Number of banned users.
        """
        return await self.collection.count_documents({"banned": True})

    async def add_referral_credit(self, referrer_id: int) -> None:
        """Add referral credit to a user.

        Args:
            referrer_id: Referrer's Telegram user ID.
        """
        await self.collection.update_one(
            {"user_id": referrer_id},
            {
                "$inc": {
                    "credits": 5,
                    "referral_count": 1,
                }
            },
        )

    async def get_top_users(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top users by referral count.

        Args:
            limit: Maximum number of users.

        Returns:
            List of top users.
        """
        cursor = (
            self.collection.find(
                {"referral_count": {"$gt": 0}},
                {"user_id": 1, "first_name": 1, "username": 1, "referral_count": 1},
            )
            .sort("referral_count", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    @staticmethod
    def _document_to_model(doc: dict[str, Any]) -> User:
        """Convert a MongoDB document to a User model.

        Args:
            doc: MongoDB document.

        Returns:
            User model.
        """
        doc.pop("_id", None)
        return User(**doc)


user_repo = UserRepository()
