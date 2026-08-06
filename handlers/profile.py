"""Profile handler for viewing user profile."""

from __future__ import annotations

from kurigram import AsyncClient, filters

from database.repositories.search_repo import search_repo
from database.repositories.user_repo import user_repo
from utils.helpers import format_datetime
from utils.keyboards import keyboards
from utils.logging_setup import get_logger

logger = get_logger("handlers.profile")


def register_handlers(client: AsyncClient) -> None:
    """Register profile handlers.

    Args:
        client: Kurigram client.
    """

    @client.on_message(filters.command("profile") & filters.private)
    async def profile_command(client: AsyncClient, message) -> None:
        """Handle /profile command."""
        user_id = message.from_user.id
        await _show_profile(client, message, user_id)

    @client.on_callback_query(filters.regex(r"^menu:profile$"))
    async def profile_callback(client: AsyncClient, query) -> None:
        """Handle profile button."""
        await _show_profile(client, query.message, query.from_user.id)
        await query.answer()


async def _show_profile(client: AsyncClient, msg, user_id: int) -> None:
    """Show user profile.

    Args:
        client: Kurigram client.
        msg: Message or Query.
        user_id: User ID.
    """
    user = await user_repo.get_by_id(user_id)
    if user is None:
        try:
            from kurigram.types import User

            user = User(
                id=user_id,
                first_name="Unknown",
                is_bot=False,
            )
        except Exception:
            await msg.edit_message_text(
                "❌ Could not load profile.",
                reply_markup=keyboards.back_to_main(),
            )
            return

    search_count = await search_repo.count_user_history(user_id)

    lines = [
        f"👤 <b>{user.first_name or 'User'} {user.last_name or ''}</b>",
        f"🆔 <b>User ID:</b> <code>{user.user_id}</code>",
    ]

    if user.username:
        lines.append(f"📎 <b>Username:</b> @{user.username}")

    lines.extend(
        [
            f"💳 <b>Credits:</b> {user.credits or 0}",
            f"🔍 <b>Searches:</b> {search_count}",
            f"👥 <b>Referrals:</b> {user.referral_count or 0}",
            f"📅 <b>Joined:</b> {format_datetime(user.created_at)}",
            f"🕐 <b>Last Seen:</b> {format_datetime(user.last_seen)}",
        ]
    )

    if user.language_code:
        lines.append(f"🌐 <b>Language:</b> {user.language_code}")

    if user.is_admin:
        lines.append("👑 <b>Role:</b> Administrator")

    text = "👤 <b>Your Profile</b>\n\n" + "\n".join(lines)

    try:
        await msg.edit_message_text(text, reply_markup=keyboards.back_to_main())
    except Exception:
        await msg.reply_text(text, reply_markup=keyboards.back_to_main())
