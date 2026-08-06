"""Search handler for user search queries."""

from __future__ import annotations

import time

from kurigram import AsyncClient, filters
from kurigram.types import Message

from config.constants import Messages
from database.repositories.ban_repo import ban_repo
from database.repositories.search_repo import search_repo
from database.repositories.setting_repo import setting_repo
from services.credit_service import credit_service
from services.search_service import search_service
from services.statistics_service import statistics_service
from utils.keyboards import keyboards
from utils.logging_setup import get_logger
from utils.validators import validate_search_query

logger = get_logger("handlers.search")


def register_handlers(client: AsyncClient) -> None:
    """Register search handlers.

    Args:
        client: Kurigram client.
    """

    @client.on_message(filters.command("search") & filters.private)
    async def search_command(client: AsyncClient, message: Message) -> None:
        """Handle /search command."""
        await _handle_search_command(client, message)

    @client.on_callback_query(filters.regex(r"^menu:search$"))
    async def search_callback(client: AsyncClient, query) -> None:
        """Handle search button from main menu."""
        await _handle_search_callback(client, query)

    @client.on_callback_query(filters.regex(r"^search:start$"))
    async def search_start_callback(client: AsyncClient, query) -> None:
        """Handle search start callback."""
        await query.answer()
        await _prompt_and_search(client, query)

    @client.on_callback_query(filters.regex(r"^search:cancel$"))
    async def search_cancel_callback(client: AsyncClient, query) -> None:
        """Handle search cancel callback."""
        await query.message.edit_text(
            "✅ Search cancelled.",
            reply_markup=keyboards.back_to_main(),
        )
        await query.answer()


async def _handle_search_command(client: AsyncClient, message: Message) -> None:
    """Handle /search command.

    Args:
        client: Kurigram client.
        message: Message object.
    """
    user = message.from_user
    if user is None:
        return

    user_id = user.id

    if await ban_repo.is_banned(user_id):
        await message.reply_text("❌ You are banned from using this bot.")
        return

    maintenance = await setting_repo.get_maintenance_mode()
    if maintenance:
        await message.reply_text("🔧 The bot is currently under maintenance.")
        return

    from handlers.force_join import require_force_join

    if not await require_force_join(client, user_id):
        return

    has_credits = await credit_service.check_balance(user_id)
    if not has_credits:
        await message.reply_text(Messages.NO_CREDITS)
        return

    query_text = _extract_query(message.text)
    if not query_text:
        await message.reply_text(
            "🔍 <b>Search Number</b>\n\n"
            "Please provide a phone number to search.\n\n"
            "📌 Example: <code>/search +1234567890</code>\n\n"
            "Or click the button below to be prompted:",
            reply_markup=keyboards.cancel_button(),
        )
        return

    await _perform_search(client, user_id, query_text, message)


async def _handle_search_callback(client: AsyncClient, query) -> None:
    """Handle search button callback.

    Args:
        client: Kurigram client.
        query: CallbackQuery.
    """
    user = query.from_user
    if user is None:
        return

    user_id = user.id

    if await ban_repo.is_banned(user_id):
        await query.answer("❌ You are banned.", show_alert=True)
        return

    maintenance = await setting_repo.get_maintenance_mode()
    if maintenance:
        await query.answer("🔧 Bot is under maintenance.", show_alert=True)
        return

    from handlers.force_join import require_force_join

    if not await require_force_join(client, user_id):
        return

    has_credits = await credit_service.check_balance(user_id)
    if not has_credits:
        await query.answer(Messages.NO_CREDITS, show_alert=True)
        return

    await _prompt_and_search(client, query)


async def _prompt_and_search(client: AsyncClient, query) -> None:
    """Prompt user for a search number and perform search.

    Args:
        client: Kurigram client.
        query: CallbackQuery.
    """
    user_id = query.from_user.id

    try:
        prompt = await query.message.edit_text(
            "🔍 <b>Enter Phone Number</b>\n\n"
            "Please type the phone number you want to look up.\n\n"
            "📌 Format: <code>+1234567890</code>\n"
            "⏰ You have 60 seconds to respond.",
        )

        response = await client.ask(
            chat_id=query.message.chat.id,
            text=query.message.text,
            timeout=60,
        )

        if response.text:
            query_text = _extract_query(response.text)
            if not query_text:
                await response.reply_text(
                    "❌ Invalid phone number format.",
                    reply_markup=keyboards.back_to_main(),
                )
                return
            await _perform_search(client, user_id, query_text, response, prompt_msg=prompt)
        else:
            await prompt.edit_text(
                "✅ Search cancelled.",
                reply_markup=keyboards.back_to_main(),
            )

    except Exception:
        await query.message.edit_text(
            "⏰ Search timed out or was cancelled.",
            reply_markup=keyboards.back_to_main(),
        )


async def _perform_search(
    client: AsyncClient,
    user_id: int,
    query_text: str,
    message: Message,
    prompt_msg=None,
) -> None:
    """Perform the actual search.

    Args:
        client: Kurigram client.
        user_id: User ID.
        query_text: Search query.
        message: Message object.
        prompt_msg: Optional prompt message to edit.
    """
    target_msg = prompt_msg if prompt_msg else message

    try:
        if not search_service._api_url:
            await target_msg.edit_text(
                "❌ Search service is not configured.\nPlease contact the administrator.",
                reply_markup=keyboards.back_to_main(),
            )
            return

        processing_msg = await target_msg.edit_text("⏳ Searching... Please wait.")

        start_time = time.time()

        result = await search_service.search(query_text, user_id)
        duration_ms = int((time.time() - start_time) * 1000)

        is_success = bool(result.get("success")) and result.get("result") is not None

        await search_repo.create(
            {
                "user_id": user_id,
                "query": query_text,
                "result": str(result.get("result"))[:500] if result.get("result") else None,
                "success": is_success,
                "duration_ms": duration_ms,
            }
        )

        await statistics_service.increment("daily_searches", 1)

        if is_success:
            new_balance = await credit_service.deduct(user_id, 1)
            formatted = await search_service.format_result(result)

            result_text = (
                f"🔍 <b>Search Results</b>\n\n"
                f"📱 <b>Number:</b> <code>{query_text}</code>\n\n"
                f"{formatted}\n\n"
                f"💳 Remaining credits: {new_balance or 0}\n"
                f"⏱️ Response time: {duration_ms}ms"
            )

            await processing_msg.edit_text(result_text, reply_markup=keyboards.back_to_main())
            logger.info(
                "Search successful",
                user_id=user_id,
                query=query_text,
                duration_ms=duration_ms,
            )
        else:
            error_msg = (
                result.get("error", "Search failed") if isinstance(result, dict) else str(result)
            )
            current_balance = await user_repo_get_credits(user_id)
            await processing_msg.edit_text(
                f"❌ Search failed.\n\nError: {error_msg}\n\n"
                f"💳 Remaining credits: {current_balance}",
                reply_markup=keyboards.back_to_main(),
            )

    except Exception as exc:
        logger.error("Search error", user_id=user_id, query=query_text, error=str(exc))
        try:
            await target_msg.edit_text(
                f"❌ An error occurred during search.\n\n{str(exc)}",
                reply_markup=keyboards.back_to_main(),
            )
        except Exception:
            await message.reply_text(
                f"❌ Search error: {str(exc)}",
                reply_markup=keyboards.back_to_main(),
            )


def _extract_query(text: str | None) -> str | None:
    """Extract and validate a search query from message text.

    Args:
        text: Message text.

    Returns:
        Validated query string or None.
    """
    if not text:
        return None

    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        query = text.strip()
    else:
        query = parts[1].strip()

    if not query:
        return None

    is_valid, error = validate_search_query(query)
    if not is_valid:
        return None
    return query


async def user_repo_get_credits(user_id: int) -> int:
    """Get user credits (helper to avoid import issues)."""
    from database.repositories.user_repo import user_repo

    return await user_repo.get_credits(user_id)
