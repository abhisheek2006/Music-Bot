"""Help command handler."""

from __future__ import annotations

from kurigram import AsyncClient, filters

from utils.keyboards import keyboards
from utils.logging_setup import get_logger

logger = get_logger("handlers.help")


def register_handlers(client: AsyncClient) -> None:
    """Register help command handlers.

    Args:
        client: Kurigram client.
    """

    @client.on_message(filters.command("help") & filters.private)
    async def help_command(client: AsyncClient, message) -> None:
        """Handle /help command."""
        help_text = _get_help_text()
        await message.reply_text(help_text, reply_markup=keyboards.main_menu())

    @client.on_callback_query(filters.regex(r"^menu:help$"))
    async def help_callback(client: AsyncClient, query) -> None:
        """Handle help button callback."""
        help_text = _get_help_text()
        await query.edit_message_text(help_text, reply_markup=keyboards.main_menu())
        await query.answer()


def _get_help_text() -> str:
    """Get the help text.

    Returns:
        Help text string.
    """
    return (
        "❓ <b>Help & Commands</b>\n\n"
        "🔍 <b>/search</b> - Search for a phone number (costs 1 credit)\n"
        "📜 <b>/history</b> - View your search history\n"
        "💳 <b>/credits</b> - Check your credit balance\n"
        "👤 <b>/profile</b> - View your profile\n"
        "📢 <b>/updates</b> - View bot updates\n"
        "❓ <b>/help</b> - Show this help message\n"
        "👋 <b>/start</b> - Start the bot\n\n"
        "<b>Admin Commands:</b>\n"
        "💳 <b>/addcredit</b> &lt;id&gt; &lt;n&gt; - Add credits to a user\n"
        "➖ <b>/removecredit</b> &lt;id&gt; &lt;n&gt; - Remove credits from a user\n"
        "✏️ <b>/setcredit</b> &lt;id&gt; &lt;n&gt; - Set user's credits\n"
        "📜 <b>/creditlog</b> &lt;id&gt; - View credit transactions\n"
        "📊 <b>/stats</b> - View statistics\n"
        "📢 <b>/broadcast</b> - Broadcast to all users\n\n"
        "💡 Need help? Contact the bot administrator."
    )
