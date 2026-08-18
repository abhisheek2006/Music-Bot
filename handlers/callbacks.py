from __future__ import annotations

import logging

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery

from config import Settings
from music.player import PlayerManager, VoiceDisabledError
from utils.formatting import format_queue
from utils.keyboards import PREFIX
from utils.permissions import can_control

logger = logging.getLogger("bot.handlers.callbacks")


def register(app: Client, manager: PlayerManager, settings: Settings) -> None:
    @app.on_callback_query()
    async def music_callback(client: Client, callback: CallbackQuery) -> None:
        data = callback.data or ""
        if isinstance(data, bytes):
            data = data.decode("utf-8", "ignore")
        if not data.startswith(f"{PREFIX}:"):
            return
        action = data.split(":", 1)[1]
        message = callback.message
        if message is None:
            return
        chat_id = message.chat.id
        user = callback.from_user
        if user is None:
            await callback.answer("Unknown user.")
            return

        try:
            current = manager.queues.current(chat_id)
            requester = current.requester_id if current else None
            if not await can_control(client, chat_id, user.id, requester):
                await callback.answer(
                    "You don't have permission to use this control.",
                    show_alert=True,
                )
                return

            if action == "pause":
                try:
                    ok = await manager.pause(chat_id)
                except VoiceDisabledError:
                    ok = False
                reply = "⏸ Playback paused." if ok else "No song is currently playing."
                await callback.answer(reply)
                return

            if action == "resume":
                try:
                    ok = await manager.resume(chat_id)
                except VoiceDisabledError:
                    ok = False
                await callback.answer("▶️ Playback resumed." if ok else "Nothing is paused.")
                return

            if action == "skip":
                try:
                    status, track = await manager.play_next(chat_id)
                except VoiceDisabledError:
                    status = "not_playing"
                    track = None
                if status == "playing" and track is not None:
                    await callback.answer(f"⏭ Now playing: {track.title}")
                elif status == "finished":
                    await callback.answer("⏭ Skipped. Queue finished.")
                else:
                    await callback.answer("Nothing to skip.")
                return

            if action == "stop":
                try:
                    ok = await manager.stop(chat_id)
                except VoiceDisabledError:
                    ok = False
                await callback.answer("⏹ Playback stopped." if ok else "Nothing is playing.")
                return

            if action == "queue":
                current = manager.queues.current(chat_id)
                tracks = manager.queues.get_queue(chat_id)
                text = format_queue(current, tracks, limit=10)
                try:
                    await message.reply(
                        text,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True,
                    )
                except Exception:
                    pass
                await callback.answer()
                return
        except Exception:
            logger.exception("Callback handler failed")
            await callback.answer("Something went wrong.", show_alert=True)
