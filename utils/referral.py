"""Referral system utilities."""

from __future__ import annotations

from kurigram import AsyncClient
from kurigram.types import Message

from config.config import settings
from database.repositories.user_repo import user_repo
from utils.logging_setup import get_logger

logger = get_logger("utils.referral")


def parse_referral_args(message: Message) -> int | None:
    """Parse referral ID from /start command arguments.

    Args:
        message: Start command message.

    Returns:
        Referrer's user ID or None.
    """
    if not message.text:
        return None

    parts = message.text.split()
    if len(parts) < 2:
        return None

    arg = parts[1]

    if arg.startswith("startapp"):
        return None

    if arg.startswith("ref_"):
        ref_str = arg[4:]
    elif arg.startswith("start_"):
        ref_str = arg[6:]
    else:
        ref_str = arg

    try:
        return int(ref_str)
    except (ValueError, TypeError):
        return None


async def record_referral(
    client: AsyncClient,
    referrer_id: int,
    referred_id: int,
) -> bool:
    """Record a referral and award credits.

    Args:
        client: Kurigram client.
        referrer_id: Referrer's user ID.
        referred_id: Referred user's ID.

    Returns:
        True if referral was recorded successfully.
    """
    referrer = await user_repo.get_by_id(referrer_id)
    if referrer is None:
        logger.warning("Referrer not found", referrer_id=referrer_id)
        return False

    try:
        await user_repo.add_referral_credit(referrer_id)
        logger.info(
            "Referral credit awarded",
            referrer_id=referrer_id,
            referred_id=referred_id,
            credits=settings.REFERRAL_CREDITS,
        )

        from config.constants import Statuses
        from database.repositories.credit_log_repo import credit_log_repo

        new_balance = await user_repo.get_credits(referrer_id)
        await credit_log_repo.log_transaction(
            user_id=referrer_id,
            admin_id=0,
            amount=settings.REFERRAL_CREDITS,
            action=Statuses.CREDIT_ADDED,
            balance_after=new_balance,
            reason="referral_bonus",
        )

        try:
            await client.send_message(
                chat_id=referrer_id,
                text=(
                    f"🎉 You received {settings.REFERRAL_CREDITS} credits "
                    f"for referring a new user!\n"
                    f"Your new balance: {new_balance} credits 💳"
                ),
            )
        except Exception:
            pass

        return True
    except Exception as exc:
        logger.error("Failed to record referral", referrer_id=referrer_id, error=str(exc))
        return False
