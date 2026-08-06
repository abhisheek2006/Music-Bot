"""Admin panel handler for inline keyboard admin actions."""

from __future__ import annotations

import os
import tempfile
from datetime import UTC, datetime

from kurigram import AsyncClient, InlineKeyboardButton, InlineKeyboardMarkup, filters

from config.config import settings
from database.repositories.ban_repo import ban_repo
from database.repositories.search_repo import search_repo
from database.repositories.user_repo import user_repo
from services.broadcast_service import broadcast_service
from services.credit_service import credit_service
from services.statistics_service import statistics_service
from utils.export import exporter
from utils.helpers import format_datetime
from utils.keyboards import keyboards
from utils.logging_setup import get_logger
from utils.validators import validate_int

logger = get_logger("handlers.admin_panel")

USER_PAGE_SIZE = 10
LOG_PAGE_SIZE = 10


def register_handlers(client: AsyncClient) -> None:
    """Register admin panel callback handlers.

    Args:
        client: Kurigram client.
    """

    # --- Admin Panel ---

    @client.on_callback_query(filters.regex(r"^admin:panel$"))
    async def admin_panel(client: AsyncClient, query) -> None:
        """Show the admin panel."""
        text = _get_admin_panel_text(client, query)
        await query.edit_message_text(text, reply_markup=keyboards.admin_menu())
        await query.answer()

    # --- User Management ---

    @client.on_callback_query(filters.regex(r"^admin:users$"))
    async def admin_users_list(client: AsyncClient, query) -> None:
        """List users."""
        await _show_users_page(client, query.message, page=0)
        await query.answer()

    @client.on_callback_query(filters.regex(r"^admin:users_page:(\d+)$"))
    async def admin_users_page(client: AsyncClient, query) -> None:
        """Paginated user list."""
        page = int(query.data.split(":")[2])
        await _show_users_page(client, query.message, page=page)
        await query.answer()

    @client.on_callback_query(filters.regex(r"^admin:user_detail:(\d+)$"))
    async def admin_user_detail(client: AsyncClient, query) -> None:
        """Show user detail."""
        user_id = int(query.data.split(":")[2])
        await _show_user_detail(client, query.message, user_id)
        await query.answer()

    @client.on_callback_query(filters.regex(r"^admin:user_credits:(\d+):add$"))
    async def admin_user_add_credit_prompt(client: AsyncClient, query) -> None:
        """Prompt for credit amount to add."""
        user_id = int(query.data.split(":")[2])
        await _prompt_credit_action(client, query, user_id, "add")

    @client.on_callback_query(filters.regex(r"^admin:user_credits:(\d+):remove$"))
    async def admin_user_remove_credit_prompt(client: AsyncClient, query) -> None:
        """Prompt for credit amount to remove."""
        user_id = int(query.data.split(":")[2])
        await _prompt_credit_action(client, query, user_id, "remove")

    @client.on_callback_query(filters.regex(r"^admin:user_ban:(\d+)$"))
    async def admin_user_ban(client: AsyncClient, query) -> None:
        """Ban a user."""
        user_id = int(query.data.split(":")[2])
        await ban_repo.ban_user(user_id, query.from_user.id, "Banned via admin panel")

        await _show_user_detail(client, query.message, user_id)
        await query.answer("✅ User banned.", show_alert=True)
        logger.info("User banned via admin panel", admin_id=query.from_user.id, target_id=user_id)

    @client.on_callback_query(filters.regex(r"^admin:user_unban:(\d+)$"))
    async def admin_user_unban(client: AsyncClient, query) -> None:
        """Unban a user."""
        user_id = int(query.data.split(":")[2])
        await ban_repo.unban_user(user_id)
        await _show_user_detail(client, query.message, user_id)
        await query.answer("✅ User unbanned.", show_alert=True)
        logger.info("User unbanned via admin panel", admin_id=query.from_user.id, target_id=user_id)

    # --- Credit Management ---

    @client.on_callback_query(filters.regex(r"^admin:credits$"))
    async def admin_credits_menu(client: AsyncClient, query) -> None:
        """Show credit management menu."""
        text = (
            "💳 <b>Credit Management</b>\n\n"
            "Use the commands below:\n\n"
            "<code>/addcredit &lt;user_id&gt; &lt;amount&gt;</code>\n"
            "<code>/removecredit &lt;user_id&gt; &lt;amount&gt;</code>\n"
            "<code>/setcredit &lt;user_id&gt; &lt;amount&gt;</code>\n"
            "<code>/creditlog [user_id]</code>"
        )
        await query.edit_message_text(text, reply_markup=keyboards.back_to_admin())
        await query.answer()

    # --- Broadcast ---

    @client.on_callback_query(filters.regex(r"^admin:broadcast$"))
    async def admin_broadcast_prompt(client: AsyncClient, query) -> None:
        """Prompt for broadcast message."""
        await query.message.edit_text(
            "📢 <b>Broadcast</b>\n\n"
            "Please send the broadcast message.\n"
            "You can use HTML formatting.\n\n"
            "❌ Send <code>/cancel</code> to cancel.",
        )
        await query.answer()

        try:
            response = await client.ask(
                query.message.chat.id, "📝 Send broadcast message:", timeout=120
            )
            if response.text:
                await query.message.edit_text("⏳ Broadcasting...")

                stats = await broadcast_service.send_broadcast(
                    client, query.from_user.id, response.text
                )

                result = (
                    f"✅ <b>Broadcast Completed</b>\n\n"
                    f"📬 Total: {stats['total']}\n"
                    f"✅ Delivered: {stats['success']}\n"
                    f"🚫 Blocked: {stats['blocked']}\n"
                    f"❌ Failed: {stats['failed']}"
                )
                await query.message.edit_text(result, reply_markup=keyboards.back_to_admin())
        except Exception:
            await query.message.edit_text(
                "⏰ Broadcast timed out or cancelled.",
                reply_markup=keyboards.back_to_admin(),
            )

    @client.on_callback_query(filters.regex(r"^admin:broadcast_d$"))
    async def admin_broadcast_designer(client: AsyncClient, query) -> None:
        """Open broadcast designer."""
        await query.message.edit_text(
            "📢 <b>Broadcast Designer</b>\n\n"
            "Use <code>/broadcast_D</code> to access the broadcast designer.\n"
            "It supports special syntax:\n"
            "<code>&lt;text&gt;</code> → monospace\n"
            "<code>[text]</code> → bold\n"
            "<code>|</code> → newline",
            reply_markup=keyboards.back_to_admin(),
        )
        await query.answer()

    # --- Statistics ---

    @client.on_callback_query(filters.regex(r"^admin:stats$"))
    async def admin_stats_menu(client: AsyncClient, query) -> None:
        """Show statistics menu."""
        await _show_dashboard(client, query.message)
        await query.answer()

    @client.on_callback_query(filters.regex(r"^admin:stats_period:(.+)$"))
    async def admin_stats_period(client: AsyncClient, query) -> None:
        """Show stats by period."""
        period = query.data.split(":")[2]
        await _show_stats_period(client, query.message, period)
        await query.answer()

    # --- Search Logs ---

    @client.on_callback_query(filters.regex(r"^admin:search_logs$"))
    async def admin_search_logs(client: AsyncClient, query) -> None:
        """List search logs."""
        await _show_search_logs_page(client, query.message, page=0)
        await query.answer()

    @client.on_callback_query(filters.regex(r"^admin:search_logs_page:(\d+)$"))
    async def admin_search_logs_page(client: AsyncClient, query) -> None:
        """Paginated search logs."""
        page = int(query.data.split(":")[2])
        await _show_search_logs_page(client, query.message, page=page)
        await query.answer()

    # --- Bans ---

    @client.on_callback_query(filters.regex(r"^admin:bans$"))
    async def admin_bans_list(client: AsyncClient, query) -> None:
        """List bans."""
        await _show_bans_page(client, query.message, page=0)
        await query.answer()

    @client.on_callback_query(filters.regex(r"^admin:bans_page:(\d+)$"))
    async def admin_bans_page(client: AsyncClient, query) -> None:
        """Paginated bans list."""
        page = int(query.data.split(":")[2])
        await _show_bans_page(client, query.message, page=page)
        await query.answer()

    # --- Settings ---

    @client.on_callback_query(filters.regex(r"^admin:force_join$"))
    async def admin_force_join(client: AsyncClient, query) -> None:
        """Show force-join settings."""
        from database.repositories.setting_repo import setting_repo

        channel = await setting_repo.get_force_join_channel()
        env_channel = settings.FORCE_JOIN_CHANNEL

        current = channel or env_channel
        if current:
            text = (
                f"🔗 <b>Force Join Settings</b>\n\n"
                f"Current channel: <code>{current}</code>\n\n"
                f"Send <code>/setchannel @yourchannel</code> to change.\n"
                f"Send <code>/setchannel</code> (without args) to clear."
            )
        else:
            text = (
                "🔗 <b>Force Join Settings</b>\n\n"
                "No channel is currently set.\n\n"
                "Send <code>/setchannel @yourchannel</code> to configure."
            )
        await query.edit_message_text(text, reply_markup=keyboards.back_to_admin())
        await query.answer()

    @client.on_callback_query(filters.regex(r"^admin:force_join_toggle$"))
    async def admin_force_join_toggle(client: AsyncClient, query) -> None:
        """Toggle force-join."""
        from database.repositories.setting_repo import setting_repo

        current = await setting_repo.get_force_join_channel()
        if current:
            await setting_repo.set_force_join_channel(None)
            await query.answer("✅ Force-join channel cleared.", show_alert=True)
        else:
            env_channel = settings.FORCE_JOIN_CHANNEL
            if env_channel:
                await setting_repo.set_force_join_channel(env_channel)
                await query.answer("✅ Force-join channel set from env.", show_alert=True)
            else:
                await query.answer(
                    "❌ Set FORCE_JOIN_CHANNEL in environment first.", show_alert=True
                )

        await admin_force_join(client, query)

    @client.on_callback_query(filters.regex(r"^admin:maintenance$"))
    async def admin_maintenance(client: AsyncClient, query) -> None:
        """Toggle maintenance mode."""
        from database.repositories.setting_repo import setting_repo

        current = await setting_repo.get_maintenance_mode()
        new_state = not current
        await setting_repo.set_maintenance_mode(new_state)

        status_text = "enabled" if new_state else "disabled"
        emoji = "🔧" if new_state else "🔓"
        await query.edit_message_text(
            f"{emoji} <b>Maintenance Mode</b>\n\n"
            f"Maintenance mode is now <b>{status_text}</b>.\n"
            f"Non-admin users cannot use the bot while maintenance mode is on.",
            reply_markup=keyboards.back_to_admin(),
        )
        await query.answer(f"✅ Maintenance mode {status_text}.", show_alert=True)
        logger.info("Maintenance mode toggled", admin_id=query.from_user.id, enabled=new_state)

    @client.on_callback_query(filters.regex(r"^admin:api_status$"))
    async def admin_api_status(client: AsyncClient, query) -> None:
        """Show API status."""
        await _show_api_status(client, query)

    # --- Actions ---

    @client.on_callback_query(filters.regex(r"^admin:restart$"))
    async def admin_restart(client: AsyncClient, query) -> None:
        """Show restart confirmation."""
        await query.edit_message_text(
            "🔄 <b>Restart Bot</b>\n\n"
            "Are you sure you want to restart the bot?\n\n"
            "The bot will be briefly unavailable.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "✅ Yes, Restart", callback_data="admin:confirm_restart"
                        )
                    ],
                    [InlineKeyboardButton("❌ Cancel", callback_data="admin:cancel")],
                ]
            ),
        )
        await query.answer()

    @client.on_callback_query(filters.regex(r"^admin:confirm_restart$"))
    async def admin_confirm_restart(client: AsyncClient, query) -> None:
        """Confirm bot restart."""
        await query.edit_message_text("🔄 Restarting...")
        await query.answer("Bot is restarting...", show_alert=True)
        logger.info("Bot restart confirmed by admin", admin_id=query.from_user.id)
        os._exit(0)

    @client.on_callback_query(filters.regex(r"^admin:shutdown$"))
    async def admin_shutdown(client: AsyncClient, query) -> None:
        """Show shutdown confirmation."""
        await query.edit_message_text(
            "🛑 <b>Shutdown Bot</b>\n\n"
            "Are you sure you want to shut down the bot?\n\n"
            "The bot will stop completely.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "✅ Yes, Shutdown", callback_data="admin:confirm_shutdown"
                        )
                    ],
                    [InlineKeyboardButton("❌ Cancel", callback_data="admin:cancel")],
                ]
            ),
        )
        await query.answer()

    @client.on_callback_query(filters.regex(r"^admin:confirm_shutdown$"))
    async def admin_confirm_shutdown(client: AsyncClient, query) -> None:
        """Confirm bot shutdown."""
        await query.edit_message_text("🛑 Shutting down...")
        await query.answer("Bot is shutting down...", show_alert=True)
        logger.info("Bot shutdown confirmed by admin", admin_id=query.from_user.id)
        os._exit(1)

    @client.on_callback_query(filters.regex(r"^admin:cancel$"))
    async def admin_cancel(client: AsyncClient, query) -> None:
        """Cancel admin action."""
        await query.edit_message_text(
            "✅ Action cancelled.",
            reply_markup=keyboards.admin_menu(),
        )
        await query.answer()

    # --- Export ---

    @client.on_callback_query(filters.regex(r"^admin:export_db$"))
    async def admin_export_db(client: AsyncClient, query) -> None:
        """Show export DB options."""
        await query.edit_message_text(
            "📥 <b>Export Database</b>\n\nChoose export format:",
            reply_markup=keyboards.export_format_selector("db"),
        )
        await query.answer()

    @client.on_callback_query(filters.regex(r"^admin:export_logs$"))
    async def admin_export_logs(client: AsyncClient, query) -> None:
        """Show export logs options."""
        await query.edit_message_text(
            "📋 <b>Export Logs</b>\n\nChoose export format:",
            reply_markup=keyboards.export_format_selector("logs"),
        )
        await query.answer()

    @client.on_callback_query(filters.regex(r"^admin:export_format:(\w+):(\w+)$"))
    async def admin_export_format(client: AsyncClient, query) -> None:
        """Handle export format selection."""
        fmt = query.data.split(":")[2]
        export_type = query.data.split(":")[3]
        await _do_export(client, query, fmt, export_type)


async def _do_export(client: AsyncClient, query, fmt: str, export_type: str) -> None:
    """Perform the export.

    Args:
        client: Kurigram client.
        query: CallbackQuery.
        fmt: Export format (json or csv).
        export_type: Export type (db or logs).
    """
    from config.config import settings

    await query.message.edit_text("⏳ Exporting...")

    tmp_dir = tempfile.gettempdir()

    if export_type == "db":
        if fmt == "json":
            all_data = {}
            for coll_name in ["users", "searches", "credit_logs", "broadcasts", "settings", "bans"]:
                coll = (
                    user_repo.collection.database[coll_name]
                    if coll_name == "users"
                    else _get_db_coll(coll_name)
                )
                docs = await coll.find({}).to_list(length=None)
                all_data[coll_name] = [exporter.serialize_document(doc) for doc in docs]

            file_path = os.path.join(
                tmp_dir, f"telebot_db_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            )
            exporter.to_json_file(all_data, file_path)

        elif fmt == "csv":
            file_path = os.path.join(
                tmp_dir, f"telebot_db_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            all_rows = []
            for coll_name in ["users", "searches", "credit_logs", "broadcasts"]:
                coll = _get_db_coll(coll_name)
                docs = await coll.find({}).to_list(length=None)
                for doc in docs:
                    row = exporter.serialize_document(doc)
                    row["collection"] = coll_name
                    all_rows.append(row)

            if all_rows:
                exporter.to_csv_file(all_rows, file_path)
            else:
                await query.message.edit_text("📭 No data to export.")
                return

        else:
            await query.message.edit_text("❌ Invalid format.")
            return

    elif export_type == "logs":
        log_file = settings.LOG_FILE
        if fmt == "json":
            file_path = os.path.join(
                tmp_dir, f"telebot_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            )
            try:
                with open(log_file) as f:
                    lines = f.readlines()
                log_data = [
                    {"line": i + 1, "content": line.strip()} for i, line in enumerate(lines)
                ]
                exporter.to_json_file(log_data, file_path)
            except FileNotFoundError:
                await query.message.edit_text("📭 No log files found.")
                return
        elif fmt == "csv":
            file_path = os.path.join(
                tmp_dir, f"telebot_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            try:
                with open(log_file) as f:
                    lines = f.readlines()
                log_data = [
                    {"line": i + 1, "content": line.strip()} for i, line in enumerate(lines)
                ]
                if log_data:
                    exporter.to_csv_file(log_data, file_path)
                else:
                    await query.message.edit_text("📭 No log files found.")
                    return
            except FileNotFoundError:
                await query.message.edit_text("📭 No log files found.")
                return
        else:
            await query.message.edit_text("❌ Invalid format.")
            return

    else:
        await query.message.edit_text("❌ Invalid export type.")
        return

    await query.message.reply_document(document=file_path)
    await query.message.edit_text(
        f"✅ Export completed!\n📄 File: <code>{os.path.basename(file_path)}</code>",
        reply_markup=keyboards.back_to_admin(),
    )
    logger.info("Export completed", format=fmt, type=export_type, file=file_path)

    try:
        os.remove(file_path)
    except Exception:
        pass


def _get_db_coll(name: str):
    """Get a database collection by name."""
    from database.connection import get_collection

    return get_collection(name)


def _get_admin_panel_text(client: AsyncClient, query) -> str:
    """Generate admin panel text.

    Args:
        client: Kurigram client.
        query: CallbackQuery.

    Returns:
        Admin panel text.
    """

    now = datetime.now(UTC)
    admin_mention = query.from_user.first_name or "Admin"

    return (
        f"👮‍♂️ <b>Admin Panel</b>\n\n"
        f"👤 Admin: {admin_mention}\n"
        f"🕐 Time: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        f"Choose an action from the menu below:"
    )


def _user_detail_markup(user_id: int) -> InlineKeyboardMarkup:
    """Build user detail keyboard for admin.

    Args:
        user_id: User ID.

    Returns:
        InlineKeyboardMarkup.
    """
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💳 Add Credit", callback_data=f"admin:user_credits:{user_id}:add"
                ),
                InlineKeyboardButton(
                    "➖ Remove Credit", callback_data=f"admin:user_credits:{user_id}:remove"
                ),
            ],
            [
                InlineKeyboardButton("🚫 Ban", callback_data=f"admin:user_ban:{user_id}"),
                InlineKeyboardButton("✅ Unban", callback_data=f"admin:user_unban:{user_id}"),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="admin:users")],
        ]
    )


async def _show_users_page(client: AsyncClient, msg, page: int = 0) -> None:
    """Show a paginated user list.

    Args:
        client: Kurigram client.
        msg: Message to edit.
        page: Page number (0-indexed).
    """
    skip = page * USER_PAGE_SIZE
    users = await user_repo.get_all_users(limit=USER_PAGE_SIZE, skip=skip)
    total = await user_repo.count_users()

    if not users:
        await msg.edit_message_text(
            "📋 No users found.",
            reply_markup=keyboards.back_to_admin(),
        )
        return

    lines = [f"👥 <b>Users</b> ({total} total, page {page + 1})\n"]
    for user in users:
        status = "🚫" if user.banned else "✅"
        admin_tag = "👑" if user.is_admin else ""
        lines.append(
            f"{status} <b>{user.first_name or 'N/A'}</b> "
            f"(@{user.username or 'N/A'}) <code>{user.user_id}</code> "
            f"💳{user.credits or 0} {admin_tag}"
        )

    text = "\n".join(lines)
    markup = keyboards.admin_users_pagination(total, page, USER_PAGE_SIZE)

    await msg.edit_message_text(text, reply_markup=markup)


async def _show_user_detail(client: AsyncClient, msg, user_id: int) -> None:
    """Show user detail page.

    Args:
        client: Kurigram client.
        msg: Message to edit.
        user_id: User ID.
    """
    user = await user_repo.get_by_id(user_id)
    if user is None:
        await msg.edit_message_text(
            f"❌ User <code>{user_id}</code> not found.",
            reply_markup=keyboards.admin_users_pagination(0, 0, 1),
        )
        return

    lines = [
        "👤 <b>User Details</b>\n\n",
        f"🆔 <b>ID:</b> <code>{user.user_id}</code>\n",
        f"👤 <b>Name:</b> {user.first_name or 'N/A'} {user.last_name or ''}\n",
    ]
    if user.username:
        lines.append(f"📎 <b>Username:</b> @{user.username}\n")
    lines.extend(
        [
            f"💳 <b>Credits:</b> {user.credits or 0}\n",
            f"👥 <b>Referrals:</b> {user.referral_count or 0}\n",
            f"🚫 <b>Banned:</b> {'Yes' if user.banned else 'No'}\n",
            f"👑 <b>Admin:</b> {'Yes' if user.is_admin else 'No'}\n",
            f"📅 <b>Joined:</b> {format_datetime(user.created_at)}\n",
        ]
    )
    text = "".join(lines)

    await msg.edit_message_text(text, reply_markup=_user_detail_markup(user_id))


async def _prompt_credit_action(client: AsyncClient, query, user_id: int, action: str) -> None:
    """Prompt admin for credit action amount.

    Args:
        client: Kurigram client.
        query: CallbackQuery.
        user_id: Target user ID.
        action: Action type (add or remove).
    """
    action_word = "add" if action == "add" else "remove"

    await query.message.edit_text(
        f"💳 <b>{action_word.title()} Credits</b>\n\n"
        f"User ID: <code>{user_id}</code>\n\n"
        f"Enter the amount of credits to {action_word}:",
    )

    try:
        response = await client.ask(query.message.chat.id, "Enter amount:", timeout=60)
        amount = validate_int(response.text.strip() if response.text else "")
        if amount is None or amount <= 0:
            await response.reply_text(
                "❌ Invalid amount. Please enter a positive number.",
                reply_markup=keyboards.back_to_admin(),
            )
            return

        from database.repositories.admin_repo import admin_repo

        await admin_repo.log_action(
            admin_id=query.from_user.id,
            action=f"credit_{action_word}",
            target_id=user_id,
            details={"amount": amount},
        )

        if action == "add":
            new_balance: int | None = await credit_service_add(
                user_id, amount, query.from_user.id, "Admin credit add"
            )
        else:
            new_balance = await credit_service_remove(
                user_id, amount, query.from_user.id, "Admin credit remove"
            )

        await response.reply_text(
            f"✅ Credits {action_word.title()}ed!\n\n"
            f"User: <code>{user_id}</code>\n"
            f"Amount: {amount}\n"
            f"New Balance: {new_balance or 0}",
            reply_markup=keyboards.back_to_admin(),
        )

    except Exception:
        await query.message.edit_text(
            "⏰ Operation timed out.",
            reply_markup=keyboards.back_to_admin(),
        )


async def _show_search_logs_page(client: AsyncClient, msg, page: int = 0) -> None:
    """Show a paginated search log list.

    Args:
        client: Kurigram client.
        msg: Message to edit.
        page: Page number (0-indexed).
    """
    skip = page * LOG_PAGE_SIZE
    searches = await search_repo.get_all(limit=LOG_PAGE_SIZE, skip=skip)
    total = await search_repo.count_all()

    if not searches:
        await msg.edit_message_text(
            "📋 No search logs found.",
            reply_markup=keyboards.back_to_admin(),
        )
        return

    lines = [f"📜 <b>Search Logs</b> ({total} total, page {page + 1})\n"]
    for i, search in enumerate(searches, skip + 1):
        status = "✅" if search.success else "❌"
        result_preview = truncate(search.result or "No result", 60) if search.result else "N/A"
        lines.append(
            f"{i}. {status} <code>{search.query}</code> by user <code>{search.user_id}</code>\n"
            f"   📋 {result_preview}\n"
            f"   📅 {format_datetime(search.created_at)}"
        )

    text = "\n".join(lines)
    markup = keyboards.admin_search_logs_pagination(total, page, LOG_PAGE_SIZE)

    await msg.edit_message_text(text, reply_markup=markup)


async def _show_bans_page(client: AsyncClient, msg, page: int = 0) -> None:
    """Show a paginated ban list.

    Args:
        client: Kurigram client.
        msg: Message to edit.
        page: Page number (0-indexed).
    """
    bans = await ban_repo.get_all(skip=page * LOG_PAGE_SIZE, limit=LOG_PAGE_SIZE)
    total = await ban_repo.count_all()

    if not bans:
        await msg.edit_message_text(
            "✅ No banned users.",
            reply_markup=keyboards.back_to_admin(),
        )
        return

    lines = [f"🚫 <b>Banned Users</b> ({total} total, page {page + 1})\n"]
    for i, ban in enumerate(bans, page * LOG_PAGE_SIZE + 1):
        reason_str = (
            f" 📝 {truncate(ban.get('reason', 'No reason'), 50)}" if ban.get("reason") else ""
        )
        lines.append(
            f"{i}. 🚫 <code>{ban['user_id']}</code> "
            f"by admin <code>{ban.get('admin_id', 'N/A')}</code>{reason_str}\n"
            f"   📅 {format_datetime(ban.get('created_at'))}"
        )

    text = "\n".join(lines)
    markup = keyboards.admin_bans_pagination(total, page, LOG_PAGE_SIZE)

    await msg.edit_message_text(text, reply_markup=markup)


async def _show_api_status(client: AsyncClient, query) -> None:
    """Show API status.

    Args:
        client: Kurigram client.
        query: CallbackQuery.
    """
    from database.connection import get_db

    lines = ["🔌 <b>API & Service Status</b>\n"]

    try:
        db = get_db()
        await db.command("ping")
        lines.append(
            f"✅ MongoDB: Connected\n   Host: {settings.MONGO_URI.split('@')[-1].split('/')[0] if '@' in settings.MONGO_URI else 'localhost'}"
        )
    except Exception as exc:
        lines.append(f"❌ MongoDB: Disconnected\n   Error: {str(exc)}")

    try:
        me = await client.get_me()
        lines.append(f"✅ Telegram: Connected\n   Bot: @{me.username}")
    except Exception as exc:
        lines.append(f"❌ Telegram: Disconnected\n   Error: {str(exc)}")

    lines.append(f"\n📡 Search API: {settings.SEARCH_API_URL or 'Not configured'}")
    lines.append(f"🔑 Search API Key: {'✅ Set' if settings.SEARCH_API_KEY else '❌ Not set'}")

    lines.append(f"\n🕐 Checked: {format_datetime(datetime.utcnow())}")

    await query.edit_message_text("\n".join(lines), reply_markup=keyboards.back_to_admin())
    await query.answer()


async def _show_dashboard(client: AsyncClient, msg) -> None:
    """Show the bot dashboard with statistics.

    Args:
        client: Kurigram client.
        msg: Message to edit.
    """
    stats = await statistics_service.get_dashboard_stats()
    top_users = await statistics_service.get_top_users(5)

    lines = [
        "📊 <b>Statistics Dashboard</b>\n",
        f"👥 Total Users: {stats['total_users']}",
        f"🚫 Banned: {stats['total_banned']}",
        f"🔍 Total Searches: {stats['total_searches']}",
        f"💳 Credits Added: {stats['total_credits_added']}",
        f"📊 Credit Operations: {stats['total_credit_operations']}",
        f"📢 Total Broadcasts: {stats['total_broadcasts']}",
    ]

    if top_users:
        lines.append("\n🏆 <b>Top Referrers:</b>")
        for i, user in enumerate(top_users, 1):
            name = f"{user.get('first_name', 'N/A')} {user.get('last_name', '')}".strip()
            lines.append(f"  {i}. {name} — {user.get('referral_count', 0)} referrals")

    text = "\n".join(lines)
    await msg.edit_message_text(text, reply_markup=keyboards.stats_period_selector())


async def _show_stats_period(client: AsyncClient, msg, period: str) -> None:
    """Show statistics for a specific period.

    Args:
        client: Kurigram client.
        msg: Message to edit.
        period: Period string.
    """
    from datetime import datetime

    if period == "global":
        stats = await statistics_service.get_dashboard_stats()
        lines = ["🌍 <b>Global Statistics</b>\n"]
        for key, value in stats.items():
            lines.append(f"📊 {key}: {value}")
        text = "\n".join(lines)
    elif period == "daily":
        data = await statistics_service.get_daily_stats(7)
        lines = ["📅 <b>Daily Statistics (last 7 days)</b>"]
        for stat_type, daily_data in data.items():
            for entry in daily_data:
                lines.append(f"  {entry['date']}: {stat_type} = {entry['value']}")
        text = "\n".join(lines)
    elif period == "monthly":
        now = datetime.now(UTC)
        data = await statistics_service.get_monthly_stats(now.year, now.month)
        lines = [f"📆 <b>Monthly Statistics</b> - {now.strftime('%B %Y')}"]
        for stat_type, stat_data in data.items():
            lines.append(f"📊 {stat_type}: {stat_data.get('total', 0)}")
        text = "\n".join(lines)
    else:
        text = "❌ Invalid period."

    await msg.edit_message_text(text, reply_markup=keyboards.back_to_admin())


def truncate(text: str, max_length: int = 100) -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


async def credit_service_add(
    user_id: int, amount: int, admin_id: int, reason: str | None = None
) -> int:
    """Add credits (helper)."""
    return await credit_service.add(user_id, amount, admin_id, reason)


async def credit_service_remove(
    user_id: int, amount: int, admin_id: int, reason: str | None = None
) -> int | None:
    """Remove credits (helper)."""
    return await credit_service.remove(user_id, amount, admin_id, reason)
