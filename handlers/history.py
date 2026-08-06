"""History handler for viewing search history."""

from __future__ import annotations

from kurigram import AsyncClient, filters

from config.constants import Messages
from database.repositories.search_repo import search_repo
from utils.helpers import format_datetime, truncate
from utils.keyboards import keyboards
from utils.logging_setup import get_logger

logger = get_logger("handlers.history")

PAGE_SIZE = 10


def register_handlers(client: AsyncClient) -> None:
    """Register history handlers.

    Args:
        client: Kurigram client.
    """

    @client.on_message(filters.command("history") & filters.private)
    async def history_command(client: AsyncClient, message) -> None:
        """Handle /history command."""
        user_id = message.from_user.id
        await _show_history(client, message, user_id, page=0)

    @client.on_callback_query(filters.regex(r"^menu:history$"))
    async def history_callback(client: AsyncClient, query) -> None:
        """Handle history button."""
        await _show_history(client, query.message, query.from_user.id, page=0)
        await query.answer()

    @client.on_callback_query(filters.regex(r"^history:page:(\d+)$"))
    async def history_page_callback(client: AsyncClient, query) -> None:
        """Handle history pagination."""
        match_parts = query.data.split(":")
        page = int(match_parts[2]) if len(match_parts) > 2 else 0
        await _show_history(client, query.message, query.from_user.id, page=page)
        await query.answer()


async def _show_history(client: AsyncClient, msg, user_id: int, page: int = 0) -> None:
    """Show search history with pagination.

    Args:
        client: Kurigram client.
        msg: Message or Query (has edit_message_text).
        user_id: User ID.
        page: Page number (0-indexed).
    """
    skip = page * PAGE_SIZE
    searches = await search_repo.get_user_history(user_id, limit=PAGE_SIZE, skip=skip)
    total = await search_repo.count_user_history(user_id)

    if not searches:
        text = (
            "📜 <b>Search History</b>\n\n"
            f"{Messages.NO_HISTORY}\n\n"
            "💡 Use /search to start searching!"
        )
        await msg.edit_message_text(text, reply_markup=keyboards.back_to_main())
        return

    lines = [f"📜 <b>Search History</b> (<b>{total}</b> results)\n"]
    for i, search in enumerate(searches, skip + 1):
        result_preview = truncate(str(search.result or "No result"), 80) if search.result else "❓"
        status_emoji = "✅" if search.success else "❌"
        lines.append(
            f"{i}. {status_emoji} <code>{search.query}</code>\n"
            f"   📅 {format_datetime(search.created_at)}\n"
            f"   📋 {result_preview}"
        )

    text = "\n".join(lines)
    markup = keyboards.history_pagination(total, page, PAGE_SIZE)

    try:
        await msg.edit_message_text(text, reply_markup=markup)
    except Exception:
        await msg.reply_text(text, reply_markup=markup)
