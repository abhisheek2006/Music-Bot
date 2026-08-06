"""Welcome message handler for new chat members."""

from __future__ import annotations

from kurigram import AsyncClient, filters

from config.config import settings
from database.repositories.setting_repo import setting_repo
from utils.keyboards import keyboards
from utils.logging_setup import get_logger

logger = get_logger("handlers.welcome")


def register_handlers(client: AsyncClient) -> None:
    """Register welcome message handlers.

    Args:
        client: Kurigram client.
    """

    @client.on_message(filters.new_chat_members & filters.private)
    async def welcome_new_member(client: AsyncClient, message) -> None:
        """Send welcome message to new members in groups."""
        maintenance = await setting_repo.get_maintenance_mode()
        if maintenance:
            return

        for member in message.new_chat_members:
            welcome_text = (
                f"👋 <b>Welcome {member.first_name or member.first_name}!</b>\n\n"
                f"{settings.WELCOME_MESSAGE}\n\n"
                f"🤖 Use /start to begin using the bot."
            )
            await message.reply_text(welcome_text, reply_markup=keyboards.main_menu())

    @client.on_message(filters.command("start") & filters.group)
    async def start_in_group(client: AsyncClient, message) -> None:
        """Handle /start in groups."""
        await message.reply_text(
            f"👋 {settings.WELCOME_MESSAGE}\n\n"
            "Please use this bot in private messages.\n"
            f"Click: https://t.me/{settings.BOT_USERNAME}?start=start"
        )
