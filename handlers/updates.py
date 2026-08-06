"""Updates handler for bot updates."""

from __future__ import annotations

from datetime import UTC

from kurigram import AsyncClient, filters

from utils.keyboards import keyboards
from utils.logging_setup import get_logger

logger = get_logger("handlers.updates")

UPDATES_TEXT = """📢 <b>Latest Bot Updates</b>

📋 <b>Version 2.0.0</b> — 2024-01-15
• ✅ Added credit system for search operations
• 📊 Added statistics dashboard
• 🎨 Improved UI with inline keyboards
• 🛡️ Enhanced security with rate limiting and flood protection

📋 <b>Version 1.5.0</b> — 2023-12-01
• 🔍 Phone number search functionality
• 📜 Search history with pagination
• 👤 User profile management
• 📢 Broadcast system for admins

📋 <b>Version 1.0.0</b> — 2023-10-01
• 🚀 Initial release
• 👋 Welcome message system
• ⭐ Basic search functionality

💡 Stay tuned for more updates!
Follow our channel for announcements.

📅 Last checked: {timestamp}
"""


def register_handlers(client: AsyncClient) -> None:
    """Register updates handlers.

    Args:
        client: Kurigram client.
    """

    @client.on_message(filters.command("updates") & filters.private)
    async def updates_command(client: AsyncClient, message) -> None:
        """Handle /updates command."""
        from datetime import datetime

        text = UPDATES_TEXT.format(timestamp=datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"))
        await message.reply_text(text, reply_markup=keyboards.back_to_main())

    @client.on_callback_query(filters.regex(r"^menu:updates$"))
    async def updates_callback(client: AsyncClient, query) -> None:
        """Handle updates button."""
        from datetime import datetime

        text = UPDATES_TEXT.format(timestamp=datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"))
        await query.edit_message_text(text, reply_markup=keyboards.back_to_main())
        await query.answer()
