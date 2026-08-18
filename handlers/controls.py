from __future__ import annotations

import logging

from pyrogram import Client, filters
from pyrogram.types import Message

from config import Settings
from music.player import PlayerManager, VoiceDisabledError
from utils.formatting import esc
from utils.permissions import can_control, is_group
from utils.telegram import reply_html

logger = logging.getLogger("bot.handlers.controls")

NO_PLAYING = "No song is currently playing."


def register(app: Client, manager: PlayerManager, settings: Settings) -> None:
    async def allowed(client: Client, message: Message) -> bool:
        user = message.from_user
        if user is None:
            return False
        current = manager.queues.current(message.chat.id)
        requester = current.requester_id if current else None
        return await can_control(client, message.chat.id, user.id, requester)

    async def voice_enabled(message: Message) -> bool:
        if manager.enabled:
            return True
        await reply_html(
            message,
            "⚠️ Voice chat is not available on this bot. Set <code>SESSION_STRING</code>.",
        )
        return False

    @app.on_message(filters.command("pause") & filters.group)
    async def pause_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        if not await voice_enabled(message):
            return
        if not is_group(message.chat.type):
            await reply_html(message, "This command only works inside groups.")
            return
        if not await allowed(client, message):
            await reply_html(message, "You don't have permission to use this control.")
            return
        try:
            ok = await manager.pause(message.chat.id)
        except VoiceDisabledError:
            ok = False
        if ok:
            await reply_html(message, "⏸ Playback paused.")
        else:
            await reply_html(message, NO_PLAYING)

    @app.on_message(filters.command("resume") & filters.group)
    async def resume_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        if not await voice_enabled(message):
            return
        if not is_group(message.chat.type):
            await reply_html(message, "This command only works inside groups.")
            return
        if not await allowed(client, message):
            await reply_html(message, "You don't have permission to use this control.")
            return
        try:
            ok = await manager.resume(message.chat.id)
        except VoiceDisabledError:
            ok = False
        if ok:
            await reply_html(message, "▶️ Playback resumed.")
        else:
            await reply_html(message, "Nothing is paused right now.")

    @app.on_message(filters.command("skip") & filters.group)
    async def skip_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        if not await voice_enabled(message):
            return
        if not is_group(message.chat.type):
            await reply_html(message, "This command only works inside groups.")
            return
        if not await allowed(client, message):
            await reply_html(message, "You don't have permission to use this control.")
            return
        try:
            status, track = await manager.play_next(message.chat.id)
        except VoiceDisabledError:
            status = "not_playing"
            track = None
        if status == "playing" and track is not None:
            await reply_html(
                message,
                f"⏭ Skipped.\n\n<b>Now playing:</b>\n🎵 {esc(track.title)} — "
                f"{esc(track.uploader or 'Unknown')}",
            )
        elif status == "finished":
            await reply_html(message, "⏭ Skipped. Queue finished.")
        else:
            await reply_html(message, NO_PLAYING)

    @app.on_message(filters.command("stop") & filters.group)
    async def stop_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        if not await voice_enabled(message):
            return
        if not is_group(message.chat.type):
            await reply_html(message, "This command only works inside groups.")
            return
        if not await allowed(client, message):
            await reply_html(message, "You don't have permission to use this control.")
            return
        try:
            ok = await manager.stop(message.chat.id)
        except VoiceDisabledError:
            ok = False
        if not ok:
            await reply_html(message, NO_PLAYING)

    @app.on_message(filters.command("mute") & filters.group)
    async def mute_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        if not await voice_enabled(message):
            return
        if not is_group(message.chat.type):
            await reply_html(message, "This command only works inside groups.")
            return
        if not await allowed(client, message):
            await reply_html(message, "You don't have permission to use this control.")
            return
        try:
            ok = await manager.mute(message.chat.id)
        except VoiceDisabledError:
            ok = False
        if ok:
            await reply_html(message, "🔇 Muted.")
        else:
            await reply_html(message, NO_PLAYING)

    @app.on_message(filters.command("unmute") & filters.group)
    async def unmute_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        if not await voice_enabled(message):
            return
        if not is_group(message.chat.type):
            await reply_html(message, "This command only works inside groups.")
            return
        if not await allowed(client, message):
            await reply_html(message, "You don't have permission to use this control.")
            return
        try:
            ok = await manager.unmute(message.chat.id)
        except VoiceDisabledError:
            ok = False
        if ok:
            await reply_html(message, "🔊 Unmuted.")
        else:
            await reply_html(message, "Audio is not muted.")

    @app.on_message(filters.command("volume") & filters.group)
    async def volume_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        if not await voice_enabled(message):
            return
        if not is_group(message.chat.type):
            await reply_html(message, "This command only works inside groups.")
            return
        if not await allowed(client, message):
            await reply_html(message, "You don't have permission to use this control.")
            return
        parts = (message.text or "").split()
        if len(parts) < 2 or not parts[1].isdigit():
            await reply_html(message, "Usage: <code>/volume 50</code> (1-100)")
            return
        volume = int(parts[1])
        if not 1 <= volume <= 100:
            await reply_html(message, "Volume must be between 1 and 100.")
            return
        try:
            ok = await manager.set_volume(message.chat.id, volume)
        except VoiceDisabledError:
            ok = False
        if ok:
            await reply_html(message, f"🔊 Volume set to {volume}%.")
        else:
            await reply_html(message, NO_PLAYING)

    @app.on_message(filters.command("seek") & filters.group)
    async def seek_handler(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
        await reply_html(message, "Seeking is not supported by this voice system.")
