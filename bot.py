from __future__ import annotations

import asyncio
import logging
import sys

try:
    asyncio.get_running_loop()
except RuntimeError:
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

from pyrogram import Client, idle
from pytgcalls import PyTgCalls

from config import ConfigError, settings
from handlers import register_all
from music.downloader import Downloader
from music.ffmpeg import is_ffmpeg_available
from music.player import PlayerManager
from utils.logging_setup import setup_logging

BANNER = """
================================
Telegram Music Bot
================================
"""


def print_banner(ffmpeg_ok: bool, voice_ok: bool) -> None:
    print(BANNER)
    print("✓ Configuration loaded")
    if ffmpeg_ok:
        print("✓ FFmpeg detected")
    else:
        print("✗ FFmpeg missing")
    print("✓ Telegram client initialized")
    if voice_ok:
        print("✓ Voice system initialized")
    else:
        print("⚠ Voice system disabled (SESSION_STRING not configured)")
    print("✓ Bot started")
    print("\nBot is running...")
    print()


async def main() -> None:
    try:
        settings.validate()
    except ConfigError as exc:
        print(f"\nStartup error: {exc}\n")
        sys.exit(1)

    setup_logging()
    logger = logging.getLogger("bot")

    if not is_ffmpeg_available():
        print(
            "\nStartup error: FFmpeg is not installed or not in PATH.\n"
            "Install it first. On Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg\n",
        )
        sys.exit(1)

    voice_ok = bool(settings.SESSION_STRING)

    app = Client(
        "telegram-music-bot",
        api_id=int(settings.API_ID),
        api_hash=settings.API_HASH,
        bot_token=settings.BOT_TOKEN,
        in_memory=True,
    )

    user = None
    call_py = None
    if voice_ok:
        user = Client(
            "telegram-music-user",
            api_id=int(settings.API_ID),
            api_hash=settings.API_HASH,
            session_string=settings.SESSION_STRING,
            in_memory=True,
        )
        call_py = PyTgCalls(user)

    downloader = Downloader(settings.DOWNLOAD_PATH)
    manager = PlayerManager(app, user, settings, downloader)
    if call_py is not None:
        manager.attach(call_py)

    register_all(app, manager, downloader, settings)

    try:
        if call_py is not None:
            await call_py.start()
            await manager.start()
        await app.start()
    except Exception as exc:
        logger.error("Failed to start clients: %s", exc)
        print(f"\nStartup error: failed to initialize Telegram clients: {exc}\n")
        sys.exit(1)

    print_banner(is_ffmpeg_available(), voice_ok)

    try:
        await idle()
    finally:
        logger.info("Shutting down...")
        try:
            await manager.shutdown()
        except Exception:
            logger.exception("Error during player shutdown")
        try:
            await app.stop()
        except Exception:
            logger.exception("Error stopping bot client")
        if user is not None:
            try:
                await user.stop()
            except Exception:
                logger.exception("Error stopping user client")


if __name__ == "__main__":
    asyncio.run(main())
