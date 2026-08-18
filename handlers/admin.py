from __future__ import annotations

import logging
import os
import sys

from pyrogram import Client, filters
from pyrogram.types import Message

from config import Settings
from music.player import PlayerManager
from utils.formatting import format_duration
from utils.permissions import is_owner
from utils.telegram import reply_html

logger = logging.getLogger("bot.handlers.admin")

NO_PERMISSION = "You are not authorized to use this command."


def register(app: Client, manager: PlayerManager, settings: Settings) -> None:
    @app.on_message(filters.command("stats"))
    async def stats_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        if not is_owner(message.from_user.id if message.from_user else None):
            await reply_html(message, NO_PERMISSION)
            return
        uptime = format_duration(manager.uptime())
        text = (
            "<b>📊 Bot Stats</b>\n\n"
            f"⏱ Uptime: {uptime}\n"
            f"👥 Known chats: {len(manager.known_chats)}\n"
            f"🎧 Active voice chats: {len(manager.active_groups())}\n"
            f"🎵 Songs played: {manager.songs_played()}\n"
            f"🔊 Voice enabled: {'Yes' if manager.enabled else 'No'}"
        )
        await reply_html(message, text)

    @app.on_message(filters.command("broadcast"))
    async def broadcast_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        if not is_owner(message.from_user.id if message.from_user else None):
            await reply_html(message, NO_PERMISSION)
            return
        text = ""
        if message.reply_to_message:
            text = message.reply_to_message.text or ""
        else:
            parts = (message.text or "").split(maxsplit=1)
            text = parts[1].strip() if len(parts) > 1 else ""
        if not text:
            await reply_html(
                message,
                "Usage: <code>/broadcast your message</code>\n"
                "or reply to a message with /broadcast",
            )
            return
        sent = 0
        failed = 0
        for chat_id in list(manager.known_chats):
            try:
                await client.send_message(chat_id, text, disable_web_page_preview=True)
                sent += 1
            except Exception:
                failed += 1
        await reply_html(
            message,
            f"📣 Broadcast complete.\nSent: <b>{sent}</b>\nFailed: <b>{failed}</b>",
        )

    @app.on_message(filters.command("restart"))
    async def restart_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        if not is_owner(message.from_user.id if message.from_user else None):
            await reply_html(message, NO_PERMISSION)
            return
        await reply_html(message, "🔄 Restarting...")
        try:
            await manager.shutdown()
        except Exception:
            logger.exception("Error during restart shutdown")
        try:
            await client.stop()
        except Exception:
            pass
        os.execv(sys.executable, [sys.executable] + sys.argv)
