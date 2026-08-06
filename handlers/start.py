"""User start handler."""

from __future__ import annotations

from kurigram import AsyncClient, filters
from kurigram.types import Message

from config.config import settings
from database.repositories.user_repo import user_repo
from utils.helpers import format_user_mention
from utils.keyboards import keyboards
from utils.logging_setup import get_logger
from utils.referral import parse_referral_args, record_referral

logger = get_logger("handlers.start")


def register_handlers(client: AsyncClient) -> None:
    """Register start command handlers.

    Args:
        client: Kurigram client.
    """

    @client.on_message(filters.command("start") & filters.private)
    async def start_command(client: AsyncClient, message: Message) -> None:
        """Handle /start command."""
        user = message.from_user
        if user is None:
            return

        referrer_id = parse_referral_args(message)

        user_data = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language_code": user.language_code,
            "is_admin": user.id in settings.ADMIN_IDS,
            "credits": settings.DEFAULT_CREDITS,
            "referrer_id": referrer_id,
        }

        db_user = await user_repo.create_or_update(user_data)

        if referrer_id and referrer_id != user.id:
            await record_referral(client, referrer_id, user.id)

        welcome_text = (
            f"👋 Hello {format_user_mention(user.id, user.first_name)}!\n\n"
            f"{settings.WELCOME_MESSAGE}\n\n"
            f"💳 Your credit balance: {db_user.credits or 0} credits\n"
            f"🔍 Each search costs 1 credit.\n\n"
            f"Use the buttons below to navigate:"
        )

        await message.reply_text(
            welcome_text,
            reply_markup=keyboards.main_menu(),
        )
        logger.info("User started bot", user_id=user.id, username=user.username)

    @client.on_callback_query(filters.regex(r"^menu:back$"))
    async def back_to_menu(client: AsyncClient, query) -> None:
        """Handle back to main menu."""
        await query.edit_message_text(
            "🏠 <b>Main Menu</b>\n\nChoose an option below:",
            reply_markup=keyboards.main_menu(),
        )
        await query.answer()

    @client.on_callback_query(filters.regex(r"^menu:close$"))
    async def close_message(client: AsyncClient, query) -> None:
        """Handle close button."""
        await query.message.delete()
        await query.answer()
