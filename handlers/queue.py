from __future__ import annotations

import logging

import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

from config import Settings
from music.player import PlayerManager
from utils.formatting import esc, format_now_playing, format_queue
from utils.permissions import can_control
from utils.telegram import reply_html

logger = logging.getLogger("bot.handlers.queue")


def register(app: Client, manager: PlayerManager, settings: Settings) -> None:
    @app.on_message(filters.command("queue"))
    async def queue_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        current = manager.queues.current(message.chat.id)
        tracks = manager.queues.get_queue(message.chat.id)
        text = format_queue(current, tracks, limit=10)
        await reply_html(message, text)

    @app.on_message(filters.command("nowplaying"))
    async def nowplaying_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        track, elapsed = await manager.now_playing(message.chat.id)
        if track is None:
            await reply_html(message, "No song is currently playing.")
            return
        text = format_now_playing(
            track,
            elapsed=elapsed,
            paused=manager.is_paused(message.chat.id),
            volume=manager.volume(message.chat.id),
        )
        await reply_html(message, text)

    @app.on_message(filters.command("clear") & filters.group)
    async def clear_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        user = message.from_user
        if user is None:
            await reply_html(message, "Unknown user.")
            return
        if not await can_control(client, message.chat.id, user.id):
            await reply_html(message, "You don't have permission to use this control.")
            return
        removed = manager.queues.clear(message.chat.id)
        await reply_html(
            message,
            f"🗑 Removed {removed} song{'s' if removed != 1 else ''} from the queue."
            if removed
            else "The queue is already empty.",
        )

    @app.on_message(filters.command("remove") & filters.group)
    async def remove_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        user = message.from_user
        if user is None:
            await reply_html(message, "Unknown user.")
            return
        if not await can_control(client, message.chat.id, user.id):
            await reply_html(message, "You don't have permission to use this control.")
            return
        parts = (message.text or "").split()
        if len(parts) < 2 or not parts[1].isdigit():
            await reply_html(message, "Usage: <code>/remove 3</code>")
            return
        position = int(parts[1])
        track = manager.queues.remove(message.chat.id, position)
        if track is None:
            await reply_html(message, f"No song at position #{position}.")
            return
        await reply_html(message, f"🗑 Removed: {esc(track.title)}")

    @app.on_message(filters.command("loop") & filters.group)
    async def loop_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        user = message.from_user
        if user is None:
            await reply_html(message, "Unknown user.")
            return
        current = manager.queues.current(message.chat.id)
        requester = current.requester_id if current else None
        if not await can_control(client, message.chat.id, user.id, requester):
            await reply_html(message, "You don't have permission to use this control.")
            return
        enabled = manager.toggle_loop(message.chat.id)
        if enabled:
            await reply_html(message, "🔁 Loop enabled for this group.")
        else:
            await reply_html(message, "🔁 Loop disabled for this group.")

    @app.on_message(filters.command("lyrics"))
    async def lyrics_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        parts = (message.text or "").split(maxsplit=1)
        query = parts[1].strip() if len(parts) > 1 else ""
        if not query:
            await reply_html(message, "Usage: <code>/lyrics artist - song</code>")
            return
        if " - " in query:
            artist, title = query.split(" - ", 1)
        elif " -" in query:
            artist, title = query.split(" -", 1)
        elif query.count(" ") >= 1:
            artist, title = query.split(" ", 1)
        else:
            await reply_html(message, "Usage: <code>/lyrics artist - song</code>")
            return
        artist = artist.strip()
        title = title.strip()
        if not artist or not title:
            await reply_html(message, "Usage: <code>/lyrics artist - song</code>")
            return
        url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        await reply_html(message, "Lyrics not found.")
                        return
                    data = await response.json()
            lyrics = data.get("lyrics", "")
            if not lyrics:
                await reply_html(message, "Lyrics not found.")
                return
            lyrics = lyrics[:3900]
            text = f"<b>{esc(artist)} — {esc(title)}</b>\n\n{esc(lyrics)}"
            await reply_html(message, text)
        except Exception:
            await reply_html(message, "Could not fetch lyrics. Please try again.")
