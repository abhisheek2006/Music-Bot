from __future__ import annotations

import logging

from pyrogram import Client, filters
from pyrogram.types import Message

from config import Settings
from music.player import PlayerManager, VoiceChatNotFound, VoiceDisabledError
from utils.permissions import can_control, is_group
from utils.telegram import reply_html

logger = logging.getLogger("bot.handlers.voice")

DISABLED_TEXT = (
    "⚠️ Voice chat is not available on this bot. "
    "Set <code>SESSION_STRING</code> in the server configuration."
)


def register(app: Client, manager: PlayerManager, settings: Settings) -> None:
    @app.on_message(filters.command("join") & filters.group)
    async def join_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        if not manager.enabled:
            await reply_html(message, DISABLED_TEXT)
            return
        if not is_group(message.chat.type):
            await reply_html(message, "This command only works inside groups.")
            return
        try:
            joined = await manager.join(message.chat.id)
        except VoiceChatNotFound:
            await reply_html(
                message,
                "No active voice chat found. Start a voice chat first.",
            )
            return
        except VoiceDisabledError:
            await reply_html(message, DISABLED_TEXT)
            return
        if joined:
            await reply_html(message, "🎧 Joined the voice chat.")
        else:
            await reply_html(message, "🎧 Already connected to the voice chat.")

    @app.on_message(filters.command("leave") & filters.group)
    async def leave_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        if not manager.enabled:
            await reply_html(message, DISABLED_TEXT)
            return
        if not is_group(message.chat.type):
            await reply_html(message, "This command only works inside groups.")
            return
        user = message.from_user
        if user is None:
            await reply_html(message, "Unknown user.")
            return
        current = manager.queues.current(message.chat.id)
        requester = current.requester_id if current else None
        if not await can_control(client, message.chat.id, user.id, requester):
            await reply_html(message, "You don't have permission to use this control.")
            return
        try:
            ok = await manager.leave(message.chat.id)
        except VoiceDisabledError:
            ok = False
        if not ok:
            await reply_html(message, "The bot is not in a voice chat.")
