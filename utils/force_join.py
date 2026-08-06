"""Force-join channel check utilities."""

from __future__ import annotations

from kurigram import AsyncClient

from database.repositories.setting_repo import setting_repo
from utils.keyboards import keyboards
from utils.logging_setup import get_logger

logger = get_logger("utils.force_join")


async def check_force_join(client: AsyncClient, user_id: int) -> bool:
    """Check if a user has joined the required channel.

    Args:
        client: Kurigram client.
        user_id: Telegram user ID.

    Returns:
        True if user has joined (or no channel is configured).
    """
    channel = await setting_repo.get_force_join_channel()
    if not channel:
        from config.config import settings

        channel = settings.FORCE_JOIN_CHANNEL or ""

    if not channel:
        return True

    try:
        member = await client.get_chat_member(channel.lstrip("@"), user_id)
        from kurigram import enums

        status = member.status if hasattr(member, "status") else None
        if status == enums.ChatMemberStatus.ADMINISTRATOR:
            return True
        if status == enums.ChatMemberStatus.OWNER:
            return True
        if status == enums.ChatMemberStatus.MEMBER:
            return True
        return False
    except Exception as exc:
        logger.warning(
            "Failed to check force-join", user_id=user_id, channel=channel, error=str(exc)
        )
        return False


async def send_force_join_message(
    client: AsyncClient,
    user_id: int,
    channel: str,
) -> None:
    """Send a force-join reminder to a user.

    Args:
        client: Kurigram client.
        user_id: Telegram user ID.
        channel: Channel username.
    """
    channel_clean = channel.lstrip("@")
    invite_link = f"https://t.me/{channel_clean}"

    text = (
        "🔒 <b>Channel Verification Required</b>\n\n"
        f"Please join our channel to use the bot:\n"
        f"<b>@{channel_clean}</b>\n\n"
        "Click the button below after joining."
    )

    await client.send_message(
        chat_id=user_id,
        text=text,
        reply_markup=keyboards.force_join_confirm(invite_link),
    )
