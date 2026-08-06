"""Credits handler for viewing and managing credit balance."""

from __future__ import annotations

from kurigram import AsyncClient, InlineKeyboardButton, InlineKeyboardMarkup, filters

from config.config import settings
from config.constants import Messages
from database.repositories.credit_log_repo import credit_log_repo
from services.credit_service import credit_service
from utils.helpers import format_credits, format_datetime
from utils.keyboards import keyboards
from utils.logging_setup import get_logger

logger = get_logger("handlers.credits")

PAGE_SIZE = 20


def register_handlers(client: AsyncClient) -> None:
    """Register credit handlers.

    Args:
        client: Kurigram client.
    """

    @client.on_message(filters.command("credits") & filters.private)
    async def credits_command(client: AsyncClient, message) -> None:
        """Handle /credits command."""
        user_id = message.from_user.id
        await _show_credits(client, message, user_id)

    @client.on_message(filters.command("creditlog") & filters.private)
    async def creditlog_command(client: AsyncClient, message) -> None:
        """Handle /creditlog command."""
        user_id = message.from_user.id
        await _show_credit_log(client, message, user_id, page=0)

    @client.on_callback_query(filters.regex(r"^menu:credits$"))
    async def credits_callback(client: AsyncClient, query) -> None:
        """Handle credits button."""
        await _show_credits(client, query.message, query.from_user.id)
        await query.answer()

    @client.on_callback_query(filters.regex(r"^creditlog:page:(\d+)$"))
    async def creditlog_page_callback(client: AsyncClient, query) -> None:
        """Handle credit log pagination."""
        match_parts = query.data.split(":")
        page = int(match_parts[2]) if len(match_parts) > 2 else 0
        await _show_credit_log(client, query.message, query.from_user.id, page=page)
        await query.answer()


async def _show_credits(client: AsyncClient, msg, user_id: int) -> None:
    """Show user's credit balance.

    Args:
        client: Kurigram client.
        msg: Message or Query.
        user_id: User ID.
    """
    balance = await credit_service.get_balance(user_id)
    transaction_count = await credit_log_repo.count_user_log(user_id)

    text = (
        f"💳 <b>My Credits</b>\n\n"
        f"💰 <b>Balance:</b> {format_credits(balance)}\n"
        f"📊 <b>Total Transactions:</b> {transaction_count}\n\n"
        f"💡 Use /search to search numbers (costs 1 credit per search).\n"
        f"🔐 New users receive {settings.DEFAULT_CREDITS} credits on signup."
    )

    try:
        await msg.edit_message_text(text, reply_markup=keyboards.back_to_main())
    except Exception:
        await msg.reply_text(text, reply_markup=keyboards.back_to_main())
    logger.info("Credits page viewed", user_id=user_id, balance=balance)


async def _show_credit_log(client: AsyncClient, msg, user_id: int, page: int = 0) -> None:
    """Show credit transaction log with pagination.

    Args:
        client: Kurigram client.
        msg: Message or Query.
        user_id: User ID.
        page: Page number (0-indexed).
    """
    skip = page * PAGE_SIZE
    logs = await credit_log_repo.get_user_log(user_id, limit=PAGE_SIZE, skip=skip)
    total = await credit_log_repo.count_user_log(user_id)

    if not logs:
        await msg.edit_message_text(
            "📜 <b>Credit Log</b>\n\n"
            f"{Messages.CREDIT_LOG_EMPTY}\n\n"
            f"💰 Your current balance: {format_credits(await credit_service.get_balance(user_id))}",
            reply_markup=keyboards.back_to_main(),
        )
        return

    lines = [f"📜 <b>Credit Transaction History</b> ({total} total)\n"]
    for i, log in enumerate(logs, skip + 1):
        action_emoji = "➕" if log.action == "added" else "➖" if log.action == "removed" else "⚙️"
        amount_str = f"{log.amount:+d}" if log.action != "set" else str(log.amount)
        admin_str = f"by user {log.admin_id}" if log.admin_id else ""
        reason_str = f" ({log.reason})" if log.reason else ""
        lines.append(
            f"{i}. {action_emoji} {amount_str} credits {admin_str}{reason_str}\n"
            f"   ⚖️ Balance: {log.balance_after} | 📅 {format_datetime(log.created_at)}"
        )

    text = "\n".join(lines)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Prev", callback_data=f"creditlog:page:{page - 1}")
        )

    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    nav_buttons.append(
        InlineKeyboardButton(
            f"📄 {page + 1}/{total_pages}",
            callback_data="creditlog:noop",
        )
    )

    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"creditlog:page:{page + 1}")
        )

    markup = InlineKeyboardMarkup(
        [
            nav_buttons,
            [InlineKeyboardButton("🔙 Back", callback_data="menu:credits")],
        ]
    )

    await msg.edit_message_text(text, reply_markup=markup)
