"""Force-join callback handler."""

from __future__ import annotations

from kurigram import AsyncClient, filters

from config.config import settings
from database.repositories.setting_repo import setting_repo
from utils.force_join import check_force_join, send_force_join_message
from utils.keyboards import keyboards
from utils.logging_setup import get_logger

logger = get_logger("handlers.force_join")


def register_handlers(client: AsyncClient) -> None:
    """Register force-join handlers.

    Args:
        client: Kurigram client.
    """

    @client.on_callback_query(filters.regex(r"^force_join:done$"))
    async def force_join_done(client: AsyncClient, query) -> None:
        """Handle force-join confirmation."""
        user_id = query.from_user.id

        channel = await setting_repo.get_force_join_channel()
        if not channel:
            channel = settings.FORCE_JOIN_CHANNEL or ""

        if not channel:
            await query.edit_message_text(
                "✅ Verification not required.",
                reply_markup=keyboards.main_menu(),
            )
            await query.answer()
            return

        if await check_force_join(client, user_id):
            await query.edit_message_text(
                "✅ Thank you for joining! You can now use all bot features.",
                reply_markup=keyboards.main_menu(),
            )
            await query.answer()
            logger.info("User verified force-join", user_id=user_id)
        else:
            await query.answer(
                "❌ You haven't joined the channel yet!",
                show_alert=True,
            )


async def require_force_join(client: AsyncClient, user_id: int) -> bool:
    """Check force-join requirement and send message if needed.

    Args:
        client: Kurigram client.
        user_id: User ID.

    Returns:
        True if user has joined (or no channel configured).
    """
    channel = await setting_repo.get_force_join_channel()
    if not channel:
        channel = settings.FORCE_JOIN_CHANNEL or ""

    if not channel:
        return True

    if await check_force_join(client, user_id):
        return True

    await send_force_join_message(client, user_id, channel)
    return False
