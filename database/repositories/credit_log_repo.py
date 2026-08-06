"""Credit log repository for MongoDB operations."""

from __future__ import annotations

from typing import Any

from motor.core import AgnosticCollection

from database.connection import get_collection
from models import CreditTransaction
from utils.logging_setup import get_logger

logger = get_logger("database.credit_log_repo")


class CreditLogRepository:
    """Repository for credit transaction log operations."""

    def __init__(self) -> None:
        self._collection_name = "credit_logs"

    @property
    def collection(self) -> AgnosticCollection:
        """Get the credit_logs collection."""
        return get_collection(self._collection_name)

    async def log_transaction(
        self,
        user_id: int,
        admin_id: int,
        amount: int,
        action: str,
        balance_after: int,
        reason: str | None = None,
    ) -> CreditTransaction:
        """Log a credit transaction.

        Args:
            user_id: Target user ID.
            admin_id: Admin who performed the action.
            amount: Amount changed.
            action: Type of action (added, removed, set, deducted).
            balance_after: Balance after transaction.
            reason: Optional reason.

        Returns:
            CreditTransaction model.
        """
        transaction = CreditTransaction(
            user_id=user_id,
            admin_id=admin_id,
            amount=amount,
            action=action,
            balance_after=balance_after,
            reason=reason,
        )
        doc = transaction.model_dump()
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        logger.info(
            "Credit transaction logged",
            user_id=user_id,
            admin_id=admin_id,
            amount=amount,
            action=action,
            balance_after=balance_after,
        )
        return transaction

    async def get_user_log(
        self, user_id: int, limit: int = 50, skip: int = 0
    ) -> list[CreditTransaction]:
        """Get credit transaction log for a user.

        Args:
            user_id: Telegram user ID.
            limit: Maximum number of records.
            skip: Number of records to skip.

        Returns:
            List of CreditTransaction models.
        """
        cursor = (
            self.collection.find({"user_id": user_id})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [self._document_to_model(doc) for doc in docs]

    async def count_user_log(self, user_id: int) -> int:
        """Count credit transactions for a user.

        Args:
            user_id: Telegram user ID.

        Returns:
            Number of transactions.
        """
        return await self.collection.count_documents({"user_id": user_id})

    async def get_all(self, limit: int = 100, skip: int = 0) -> list[CreditTransaction]:
        """Get all credit transactions.

        Args:
            limit: Maximum number of records.
            skip: Number of records to skip.

        Returns:
            List of CreditTransaction models.
        """
        cursor = self.collection.find({}).sort("created_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._document_to_model(doc) for doc in docs]

    async def count_all(self) -> int:
        """Count all credit transactions.

        Returns:
            Number of transactions.
        """
        return await self.collection.count_documents({})

    @staticmethod
    def _document_to_model(doc: dict[str, Any]) -> CreditTransaction:
        """Convert a MongoDB document to a CreditTransaction model."""
        doc.pop("_id", None)
        return CreditTransaction(**doc)


credit_log_repo = CreditLogRepository()
