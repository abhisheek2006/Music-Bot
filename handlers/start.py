from __future__ import annotations

import logging
import time

from pyrogram import Client, filters, raw
from pyrogram.types import Message

from config import Settings
from music.player import PlayerManager
from utils.telegram import reply_html

logger = logging.getLogger("bot.handlers.start")

HELP_TEXT = """
<b>🎵 MUSIC</b>
/play &lt;song or URL&gt; — play music
/vplay &lt;song or URL&gt; — play video in voice chat
/stream &lt;URL&gt; — stream a direct URL
/song &lt;song&gt; — search and show song info

<b>🎧 VOICE CHAT</b>
/join — join the active voice chat
/leave — leave the voice chat

<b>▶️ PLAYER</b>
/pause — pause playback
/resume — resume playback
/skip — skip the current song
/stop — stop playback and clear queue
/mute — mute audio
/unmute — unmute audio
/volume &lt;1-100&gt; — set volume

<b>🛠 QUEUE</b>
/queue — show the queue
/nowplaying — show the current song
/remove &lt;number&gt; — remove a queued song
/clear — clear the queue

<b>ℹ️ INFO</b>
/help — this help
/ping — check latency
/lyrics — search lyrics
"""

WELCOME_TEXT = (
    "<b>🎵 Telegram Music Bot</b>\n\n"
    "I can play music inside Telegram group voice chats.\n\n"
    "1. Add me to a group together with a music user account.\n"
    "2. Start a voice chat in the group.\n"
    "3. Send /join then /play &lt;song name&gt;.\n\n"
    "Send /help to see all commands."
)


def register(app: Client, manager: PlayerManager, settings: Settings) -> None:
    @app.on_message(filters.command("start") & filters.private)
    async def start_private(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        await reply_html(message, WELCOME_TEXT)

    @app.on_message(filters.command("start") & filters.group)
    async def start_group(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        await reply_html(message, "🎧 Music bot is active in this group. Send /help for commands.")

    @app.on_message(filters.command("help"))
    async def help_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        await reply_html(message, HELP_TEXT)

    @app.on_message(filters.command("ping"))
    async def ping_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        start = time.monotonic()
        latency_ms = None
        try:
            await client.invoke(raw.functions.help.GetNearestDc())
            latency_ms = round((time.monotonic() - start) * 1000)
        except Exception:
            pass
        if latency_ms is not None:
            text = f"🏓 <b>Pong!</b>\n\nLatency: <b>{latency_ms} ms</b>"
        else:
            text = "🏓 <b>Pong!</b>"
        await reply_html(message, text)
