"""Admin command handlers for text-based admin commands."""

from __future__ import annotations

import re

from kurigram import AsyncClient, filters

from config.constants import Messages
from database.repositories.ban_repo import ban_repo
from database.repositories.credit_log_repo import credit_log_repo
from database.repositories.user_repo import user_repo
from services.broadcast_service import broadcast_service
from services.credit_service import credit_service
from utils.helpers import sanitize_text
from utils.keyboards import keyboards
from utils.logging_setup import get_logger
from utils.validators import validate_int

logger = get_logger("handlers.admin_commands")


def register_handlers(client: AsyncClient) -> None:
    """Register admin command handlers.

    Args:
        client: Kurigram client.
    """

    @client.on_message(filters.command("addcredit") & filters.private)
    async def addcredit_command(client: AsyncClient, message) -> None:
        """Handle /addcredit command."""
        if not message.is_admin:
            await message.reply_text(Messages.ADMIN_ONLY)
            return

        if message.text:
            parts = message.text.split(maxsplit=2)
            if len(parts) < 3:
                await message.reply_text(
                    "📋 Usage: <code>/addcredit &lt;user_id&gt; &lt;amount&gt; [reason]</code>\n\n"
                    "💡 Example: <code>/addcredit 123456789 10</code>"
                )
                return

            target_id = validate_int(parts[1])
            amount = validate_int(parts[2])
            reason = parts[3] if len(parts) > 3 else None

            if target_id is None:
                await message.reply_text(Messages.INVALID_USER_ID)
                return
            if amount is None or amount <= 0:
                await message.reply_text(Messages.INVALID_CREDIT_AMOUNT)
                return

            new_balance = await credit_service.add(target_id, amount, message.from_user.id, reason)
            target = await user_repo.get_by_id(target_id)
            target_name = target.first_name if target else str(target_id)

            await message.reply_text(
                f"✅ <b>Credits Added</b>\n\n"
                f"👤 User: {target_name}\n"
                f"👤 ID: <code>{target_id}</code>\n"
                f"➕ Amount: +{amount} credits\n"
                f"⚖️ New Balance: {new_balance} credits",
                reply_markup=keyboards.back_to_admin(),
            )
            logger.info(
                "Admin added credits",
                admin_id=message.from_user.id,
                target_id=target_id,
                amount=amount,
            )

    @client.on_message(filters.command("removecredit") & filters.private)
    async def removecredit_command(client: AsyncClient, message) -> None:
        """Handle /removecredit command."""
        if not message.is_admin:
            await message.reply_text(Messages.ADMIN_ONLY)
            return

        if message.text:
            parts = message.text.split(maxsplit=2)
            if len(parts) < 3:
                await message.reply_text(
                    "📋 Usage: <code>/removecredit &lt;user_id&gt; &lt;amount&gt; [reason]</code>\n\n"
                    "💡 Example: <code>/removecredit 123456789 5</code>"
                )
                return

            target_id = validate_int(parts[1])
            amount = validate_int(parts[2])
            reason = parts[3] if len(parts) > 3 else None

            if target_id is None:
                await message.reply_text(Messages.INVALID_USER_ID)
                return
            if amount is None or amount <= 0:
                await message.reply_text(Messages.INVALID_CREDIT_AMOUNT)
                return

            new_balance = await credit_service.remove(
                target_id, amount, message.from_user.id, reason
            )

            target = await user_repo.get_by_id(target_id)
            target_name = target.first_name if target else str(target_id)

            await message.reply_text(
                f"✅ <b>Credits Removed</b>\n\n"
                f"👤 User: {target_name}\n"
                f"👤 ID: <code>{target_id}</code>\n"
                f"➖ Amount: -{amount} credits\n"
                f"⚖️ New Balance: {new_balance or 0} credits",
                reply_markup=keyboards.back_to_admin(),
            )

    @client.on_message(filters.command("setcredit") & filters.private)
    async def setcredit_command(client: AsyncClient, message) -> None:
        """Handle /setcredit command."""
        if not message.is_admin:
            await message.reply_text(Messages.ADMIN_ONLY)
            return

        if message.text:
            parts = message.text.split(maxsplit=2)
            if len(parts) < 3:
                await message.reply_text(
                    "📋 Usage: <code>/setcredit &lt;user_id&gt; &lt;amount&gt;</code>\n\n"
                    "💡 Example: <code>/setcredit 123456789 50</code>"
                )
                return

            target_id = validate_int(parts[1])
            amount = validate_int(parts[2])

            if target_id is None:
                await message.reply_text(Messages.INVALID_USER_ID)
                return
            if amount is None or amount < 0:
                await message.reply_text("❌ Amount must be a non-negative number.")
                return

            new_balance = await credit_service.set(target_id, amount, message.from_user.id)
            target = await user_repo.get_by_id(target_id)
            target_name = target.first_name if target else str(target_id)

            await message.reply_text(
                f"✅ <b>Credits Set</b>\n\n"
                f"👤 User: {target_name}\n"
                f"👤 ID: <code>{target_id}</code>\n"
                f"⚙️ New Balance: {new_balance} credits",
                reply_markup=keyboards.back_to_admin(),
            )

    @client.on_message(filters.command("creditlog") & filters.private)
    async def creditlog_command(client: AsyncClient, message) -> None:
        """Handle /creditlog command for admins."""
        if not message.is_admin:
            await message.reply_text(Messages.ADMIN_ONLY)
            return

        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            logs = await credit_log_repo.get_all(limit=50)
            if not logs:
                await message.reply_text(Messages.CREDIT_LOG_EMPTY)
                return

            lines = ["📜 <b>All Credit Transactions</b> (last 50)\n"]
            for i, log in enumerate(logs, 1):
                action_emoji = (
                    "➕" if log.action == "added" else "➖" if log.action == "removed" else "⚙️"
                )
                lines.append(
                    f"{i}. {action_emoji} User {log.user_id}: {log.amount:+d} "
                    f"({log.action}) by admin {log.admin_id}"
                )
        await message.reply_text("\n".join(lines), reply_markup=keyboards.back_to_admin())

    @client.on_message(filters.command("broadcast_D") & filters.private)
    async def broadcast_d_command(client: AsyncClient, message) -> None:
        """Handle /broadcast_D command (broadcast designer)."""
        if not message.is_admin:
            await message.reply_text(Messages.ADMIN_ONLY)
            return

        await message.reply_text(
            "📢 <b>Broadcast Designer</b>\n\n"
            "Enter your broadcast message using the special syntax:\n\n"
            "<code>&lt;text&gt;</code> → monospace text\n"
            "<code>[text]</code> → bold text\n"
            "<code>|</code> → newline\n\n"
            "📝 Example:\n"
            "<code>Welcome to [Telebot] v2.0 | &lt;New search feature!&gt; | /help for commands</code>\n\n"
            "⏰ You have 300 seconds. Send <code>/cancel</code> to abort.",
        )

        try:
            response = await client.ask(
                chat_id=message.chat.id,
                text="📝 Enter your broadcast message (use the syntax above):",
                timeout=300,
            )

            if not response.text:
                await response.reply_text(
                    "❌ No message provided.", reply_markup=keyboards.back_to_admin()
                )
                return

            if response.text.strip().lower() == "/cancel":
                await response.reply_text(
                    "✅ Broadcast cancelled.", reply_markup=keyboards.back_to_admin()
                )
                return

            formatted = _parse_broadcast_design(response.text)

            await response.reply_text(
                f"📋 <b>Preview:</b>\n\n{formatted}\n\n⏳ Broadcasting...",
            )

            stats = await broadcast_service.send_broadcast(
                client,
                message.from_user.id,
                formatted,
            )

            result = (
                f"✅ <b>Broadcast Designer Completed</b>\n\n"
                f"📬 Total: {stats['total']}\n"
                f"✅ Delivered: {stats['success']}\n"
                f"🚫 Blocked: {stats['blocked']}\n"
                f"❌ Failed: {stats['failed']}"
            )
            await response.reply_text(result, reply_markup=keyboards.back_to_admin())

        except Exception:
            await message.reply_text(
                "⏰ Broadcast designer timed out or was cancelled.",
                reply_markup=keyboards.back_to_admin(),
            )

    @client.on_message(filters.command("setchannel") & filters.private)
    async def setchannel_command(client: AsyncClient, message) -> None:
        """Handle /setchannel command."""
        if not message.is_admin:
            await message.reply_text(Messages.ADMIN_ONLY)
            return

        from database.repositories.setting_repo import setting_repo

        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            await setting_repo.set_force_join_channel(None)
            await message.reply_text(
                "✅ Force-join channel cleared.",
                reply_markup=keyboards.back_to_admin(),
            )
            return

        channel = sanitize_text(parts[1].strip(), 100)
        await setting_repo.set_force_join_channel(
            channel.lstrip("@") if not channel.startswith("@") else channel
        )

        await message.reply_text(
            f"✅ Force-join channel set to: <code>{channel}</code>",
            reply_markup=keyboards.back_to_admin(),
        )
        logger.info("Force-join channel set", admin_id=message.from_user.id, channel=channel)

    @client.on_message(filters.command("stats") & filters.private)
    async def stats_command(client: AsyncClient, message) -> None:
        """Handle /stats command."""
        if not message.is_admin:
            await message.reply_text(Messages.ADMIN_ONLY)
            return

        from services.statistics_service import statistics_service

        stats = await statistics_service.get_dashboard_stats()
        text = (
            "📊 <b>Bot Statistics Dashboard</b>\n\n"
            f"👥 Total Users: {stats['total_users']}\n"
            f"🚫 Banned Users: {stats['total_banned']}\n"
            f"🔍 Total Searches: {stats['total_searches']}\n"
            f"💳 Credits Added: {stats['total_credits_added']}\n"
            f"📊 Credit Operations: {stats['total_credit_operations']}\n"
            f"📢 Total Broadcasts: {stats['total_broadcasts']}"
        )
        await message.reply_text(text, reply_markup=keyboards.back_to_admin())

    @client.on_message(filters.command("broadcast") & filters.private)
    async def broadcast_command(client: AsyncClient, message) -> None:
        """Handle /broadcast command."""
        if not message.is_admin:
            await message.reply_text(Messages.ADMIN_ONLY)
            return

        from services.broadcast_service import broadcast_service

        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            await message.reply_text(
                "📢 <b>Broadcast</b>\n\n"
                "Usage: <code>/broadcast &lt;your message&gt;</code>\n\n"
                "This will send your message to all users."
            )
            return

        broadcast_msg = parts[1]
        await message.reply_text("⏳ Broadcasting...")

        stats = await broadcast_service.send_broadcast(client, message.from_user.id, broadcast_msg)

        result = (
            f"✅ <b>Broadcast Completed</b>\n\n"
            f"📬 Total: {stats['total']}\n"
            f"✅ Delivered: {stats['success']}\n"
            f"🚫 Blocked: {stats['blocked']}\n"
            f"❌ Failed: {stats['failed']}"
        )
        await message.reply_text(result, reply_markup=keyboards.back_to_admin())

    @client.on_message(filters.command("ban") & filters.private)
    async def ban_command(client: AsyncClient, message) -> None:
        """Handle /ban command."""
        if not message.is_admin:
            await message.reply_text(Messages.ADMIN_ONLY)
            return

        parts = (message.text or "").split(maxsplit=2)
        if len(parts) < 2:
            await message.reply_text(
                "📋 Usage: <code>/ban &lt;user_id&gt; [reason]</code>\n\n"
                "💡 Example: <code>/ban 123456789 spamming</code>"
            )
            return

        target_id = validate_int(parts[1])
        if target_id is None:
            await message.reply_text(Messages.INVALID_USER_ID)
            return

        reason = parts[2] if len(parts) > 2 else "No reason provided"
        await ban_repo.ban_user(target_id, message.from_user.id, reason)

        await message.reply_text(
            f"✅ User <code>{target_id}</code> has been banned.\nReason: {sanitize_text(reason)}",
            reply_markup=keyboards.back_to_admin(),
        )
        logger.info(
            "User banned by command",
            admin_id=message.from_user.id,
            target_id=target_id,
            reason=reason,
        )

    @client.on_message(filters.command("unban") & filters.private)
    async def unban_command(client: AsyncClient, message) -> None:
        """Handle /unban command."""
        if not message.is_admin:
            await message.reply_text(Messages.ADMIN_ONLY)
            return

        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            await message.reply_text("📋 Usage: <code>/unban &lt;user_id&gt;</code>")
            return

        target_id = validate_int(parts[1])
        if target_id is None:
            await message.reply_text(Messages.INVALID_USER_ID)
            return

        result = await ban_repo.unban_user(target_id)
        if result:
            await message.reply_text(
                f"✅ User <code>{target_id}</code> has been unbanned.",
                reply_markup=keyboards.back_to_admin(),
            )
        else:
            await message.reply_text(f"⚠️ User <code>{target_id}</code> is not banned.")

    @client.on_message(filters.command("users") & filters.private)
    async def users_command(client: AsyncClient, message) -> None:
        """Handle /users command."""
        if not message.is_admin:
            await message.reply_text(Messages.ADMIN_ONLY)
            return

        from database.repositories.user_repo import user_repo as ur

        users = await ur.get_all_users(limit=20)
        total = await ur.count_users()

        if not users:
            await message.reply_text("📋 No users found.", reply_markup=keyboards.back_to_admin())
            return

        lines = [f"👥 <b>Users</b> ({total} total, showing 20)\n"]
        for user in users:
            status = "🚫" if user.banned else "✅"
            admin_tag = " 👑" if user.is_admin else ""
            lines.append(
                f"{status} {user.first_name or 'N/A'} "
                f"(@{user.username or 'N/A'}) "
                f"<code>{user.user_id}</code> "
                f"💳{user.credits or 0} {admin_tag}"
            )
        await message.reply_text("\n".join(lines), reply_markup=keyboards.back_to_admin())


def _parse_broadcast_design(text: str) -> str:
    """Parse broadcast designer syntax.

    Syntax:
        <text> → <code>text</code> (monospace)
        [text] → <b>text</b> (bold)
        | → \\n (newline)

    Args:
        text: Raw broadcast text.

    Returns:
        HTML-formatted string.
    """
    text = text.strip()
    text = re.sub(r"<([^>|]+)>", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]|]+)\]", lambda m: f"<b>{m.group(1)}</b>", text)
    text = text.replace("|", "\n")
    return text
