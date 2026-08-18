from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.types import Message

from config import Settings
from handlers import admin, callbacks, controls, play, queue, start, voice
from music.downloader import Downloader
from music.player import PlayerManager


def register_all(
    app: Client,
    manager: PlayerManager,
    downloader: Downloader,
    settings: Settings,
) -> None:
    start.register(app, manager, settings)
    play.register(app, manager, downloader, settings)
    controls.register(app, manager, settings)
    queue.register(app, manager, settings)
    voice.register(app, manager, settings)
    admin.register(app, manager, settings)
    callbacks.register(app, manager, settings)

    @app.on_message(filters.group)
    async def _record_chat(client: Client, message: Message) -> None:
        manager.record_chat(message.chat.id)
