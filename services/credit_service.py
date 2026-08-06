"""Credit management service."""

from __future__ import annotations

from typing import Any

from config.constants import Statuses
from database.repositories.credit_log_repo import credit_log_repo
from database.repositories.user_repo import user_repo
from utils.logging_setup import get_logger

logger = get_logger("services.credit")


class CreditService:
    """Service for managing user credits."""

    async def get_balance(self, user_id: int) -> int:
        """Get a user's credit balance.

        Args:
            user_id: Telegram user ID.

        Returns:
            Credit balance.
        """
        return await user_repo.get_credits(user_id)

    async def check_balance(self, user_id: int) -> bool:
        """Check if a user has enough credits.

        Args:
            user_id: Telegram user ID.

        Returns:
            True if user has at least 1 credit.
        """
        balance = await self.get_balance(user_id)
        return balance >= 1

    async def deduct(self, user_id: int, amount: int = 1) -> int | None:
        """Deduct credits from a user.

        Args:
            user_id: Telegram user ID.
            amount: Amount to deduct.

        Returns:
            New balance or None if insufficient.
        """
        balance = await user_repo.deduct_credits(user_id, amount)
        if balance is None:
            logger.warning("Insufficient credits for deduction", user_id=user_id, amount=amount)
            return None

        await credit_log_repo.log_transaction(
            user_id=user_id,
            admin_id=0,
            amount=-amount,
            action=Statuses.CREDIT_DEDUCTED,
            balance_after=balance,
            reason="search_lookup",
        )
        logger.info(
            "Credits deducted",
            user_id=user_id,
            amount=amount,
            balance_after=balance,
        )
        return balance

    async def add(
        self,
        user_id: int,
        amount: int,
        admin_id: int,
        reason: str | None = None,
    ) -> int:
        """Add credits to a user.

        Args:
            user_id: Telegram user ID.
            amount: Amount to add.
            admin_id: Admin performing the action.
            reason: Optional reason.

        Returns:
            New balance.
        """
        balance = await user_repo.add_credits(user_id, amount)
        await credit_log_repo.log_transaction(
            user_id=user_id,
            admin_id=admin_id,
            amount=amount,
            action=Statuses.CREDIT_ADDED,
            balance_after=balance,
            reason=reason,
        )
        logger.info(
            "Credits added",
            user_id=user_id,
            amount=amount,
            admin_id=admin_id,
            balance_after=balance,
        )
        return balance

    async def remove(
        self,
        user_id: int,
        amount: int,
        admin_id: int,
        reason: str | None = None,
    ) -> int | None:
        """Remove credits from a user.

        Args:
            user_id: Telegram user ID.
            amount: Amount to remove.
            admin_id: Admin performing the action.
            reason: Optional reason.

        Returns:
            New balance or None if insufficient.
        """
        balance = await user_repo.add_credits(user_id, -amount)

        if balance < 0:
            await user_repo.update(user_id, {"credits": 0})
            balance = 0

        await credit_log_repo.log_transaction(
            user_id=user_id,
            admin_id=admin_id,
            amount=-amount,
            action=Statuses.CREDIT_REMOVED,
            balance_after=balance,
            reason=reason,
        )
        logger.info(
            "Credits removed",
            user_id=user_id,
            amount=amount,
            admin_id=admin_id,
            balance_after=balance,
        )
        return balance

    async def set(
        self,
        user_id: int,
        amount: int,
        admin_id: int,
        reason: str | None = None,
    ) -> int:
        """Set a user's credit balance.

        Args:
            user_id: Telegram user ID.
            amount: Amount to set.
            admin_id: Admin performing the action.
            reason: Optional reason.

        Returns:
            New balance.
        """
        old_balance = await user_repo.get_credits(user_id)
        await user_repo.update(user_id, {"credits": amount})

        await credit_log_repo.log_transaction(
            user_id=user_id,
            admin_id=admin_id,
            amount=amount - old_balance,
            action=Statuses.CREDIT_SET,
            balance_after=amount,
            reason=reason,
        )
        logger.info(
            "Credits set",
            user_id=user_id,
            amount=amount,
            admin_id=admin_id,
            balance_after=amount,
            old_balance=old_balance,
        )
        return amount

    async def get_log(
        self,
        user_id: int,
        limit: int = 50,
        skip: int = 0,
    ) -> list[Any]:
        """Get credit transaction log for a user.

        Args:
            user_id: Telegram user ID.
            limit: Maximum number of records.
            skip: Number of records to skip.

        Returns:
            List of credit transactions.
        """
        return await credit_log_repo.get_user_log(user_id, limit, skip)

    async def get_all_logs(self, limit: int = 100, skip: int = 0) -> list[Any]:
        """Get all credit transactions.

        Args:
            limit: Maximum number of records.
            skip: Number of records to skip.

        Returns:
            List of all credit transactions.
        """
        return await credit_log_repo.get_all(limit, skip)


credit_service = CreditService()
