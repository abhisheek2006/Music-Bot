from __future__ import annotations

import logging

from pyrogram import Client, filters
from pyrogram.types import Message

from config import Settings
from music.downloader import AudioSourceError, Downloader
from music.player import (
    PlayerManager,
    TrackPlaybackError,
    VoiceChatNotFound,
    VoiceDisabledError,
)
from utils.formatting import esc, format_added_to_queue, format_song_info
from utils.permissions import is_group
from utils.telegram import reply_html

logger = logging.getLogger("bot.handlers.play")

USAGE = "Usage: <code>/play &lt;song name or URL&gt;</code>"

DISABLED_TEXT = (
    "⚠️ Voice chat is not available on this bot.\n"
    "The owner must configure <code>SESSION_STRING</code> "
    "(a user account session) in the server environment."
)

NO_VOICE_CHAT_TEXT = (
    "⚠️ No active voice chat found. Start a voice chat in the group first, "
    "then use <code>/join</code> or send <code>/play</code> again."
)


def _is_telegram_audio(message: Message) -> bool:
    if message.audio or message.voice:
        return True
    if message.document and message.document.mime_type:
        return message.document.mime_type.startswith("audio/")
    return False


def register(
    app: Client,
    manager: PlayerManager,
    downloader: Downloader,
    settings: Settings,
) -> None:
    @app.on_message(filters.command(["play", "vplay", "stream", "song"]) & filters.group)
    async def play_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        if not manager.enabled:
            await reply_html(message, DISABLED_TEXT)
            return
        if not is_group(message.chat.type):
            await reply_html(message, "This command only works inside groups.")
            return

        command = message.command[0].lower()
        video = command == "vplay"
        direct = command == "stream"
        only_info = command == "song"

        parts = (message.text or "").split(maxsplit=1)
        query = parts[1].strip() if len(parts) > 1 else ""

        reply_to = message.reply_to_message
        is_telegram = reply_to is not None and _is_telegram_audio(reply_to)
        if not query and not is_telegram:
            await reply_html(message, USAGE)
            return

        user = message.from_user
        requester_id = user.id if user else None
        requester_name = user.first_name if user else None

        status_message = await reply_html(message, "🔍 Searching...")
        assert status_message is not None

        try:
            if is_telegram and not query:
                if manager.user is None:
                    await status_message.edit("⚠️ Voice chat is not available on this bot.")
                    return
                track = await downloader.telegram_media_track(
                    manager.user,
                    reply_to,
                    requester_id,
                    requester_name,
                )
                if track is None:
                    await status_message.edit("⚠️ This file type is not supported.")
                    return
            elif direct:
                track = await downloader.from_url(query, requester_id, requester_name)
            else:
                track = await downloader.search(query, requester_id, requester_name)
        except AudioSourceError as exc:
            await status_message.edit(f"⚠️ {esc(str(exc))}")
            return
        except Exception:
            logger.exception("Failed to resolve audio source")
            await status_message.edit("Unable to access this audio source.")
            return

        if only_info:
            await status_message.edit(format_song_info(track))
            return

        try:
            status, position = await manager.enqueue_and_play(
                message.chat.id,
                track,
                video=video,
            )
        except VoiceChatNotFound:
            await status_message.edit(NO_VOICE_CHAT_TEXT)
            return
        except VoiceDisabledError:
            await status_message.edit(DISABLED_TEXT)
            return
        except TrackPlaybackError as exc:
            await status_message.edit(
                f"❌ Unable to play: {esc(str(exc))}\nSkipping to the next song...",
            )
            return
        except Exception:
            logger.exception("Playback failed")
            await status_message.edit("❌ Playback failed. Please try again.")
            return

        if status == "playing":
            await status_message.edit(f"▶️ <b>Now Playing:</b> {esc(track.title)}")
            return
        if status == "full":
            await status_message.edit("⚠️ The queue is full. Remove some songs first.")
            return
        await status_message.edit(format_added_to_queue(track, position or 1))
