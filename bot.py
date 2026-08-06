"""Main bot module - Telebot application entrypoint."""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from typing import Any

from kurigram import AsyncClient, idle

from config.config import settings
from database.connection import close_mongo, connect_to_mongo, get_db
from database.indexes import create_indexes
from handlers import register_all_handlers
from middlewares.admin import admin_middleware
from middlewares.cooldown import cooldown_middleware
from middlewares.flood_protection import flood_middleware
from middlewares.logging_middleware import logging_middleware
from middlewares.rate_limiter import rate_limiter
from middlewares.sanitization import sanitization_middleware
from services.cleanup_service import cleanup_service
from services.search_service import search_service
from utils.health import run_health_server, update_health
from utils.logging_setup import setup_logging

logger: Any = None


class MiddlewareDispatcher:
    """Dispatches middleware calls to the appropriate method."""

    def __init__(self, instance: Any) -> None:
        self._instance = instance

    def __call__(self, client: AsyncClient, update: Any, nxt: Any) -> Any:
        """Dispatch to the appropriate middleware method.

        Args:
            client: Kurigram client.
            update: Message or CallbackQuery.
            nxt: Next handler.

        Returns:
            Coroutine result.
        """
        if hasattr(update, "data"):
            return self._instance.on_callback_query(client, update, nxt)
        return self._instance.on_message(client, update, nxt)


def _make_middleware(instance: Any):
    """Create a Pyrogram/Kurigram-compatible middleware function.

    Args:
        instance: Middleware instance with on_message and on_callback_query methods.

    Returns:
        Middleware callable.
    """

    async def _middleware(client: AsyncClient, update: Any, nxt: Any) -> None:
        if hasattr(update, "data") and hasattr(update, "message"):
            await instance.on_callback_query(client, update, nxt)
        else:
            await instance.on_message(client, update, nxt)

    return _middleware


class Telebot:
    """Main bot application class."""

    def __init__(self) -> None:
        self.client: AsyncClient | None = None
        self._health_runner: Any = None
        self._cleanup_task: asyncio.Task | None = None
        self._running: bool = False

    def _create_client(self) -> AsyncClient:
        """Create and configure the Kurigram client.

        Returns:
            Configured AsyncClient instance.
        """
        client = AsyncClient(
            "telebot_session",
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            bot_token=settings.BOT_TOKEN,
            workdir=os.getcwd(),
            in_memory=False,
        )

        client.add_middleware(_make_middleware(logging_middleware))
        client.add_middleware(_make_middleware(rate_limiter))
        client.add_middleware(_make_middleware(flood_middleware))
        client.add_middleware(_make_middleware(sanitization_middleware))
        client.add_middleware(_make_middleware(admin_middleware))
        client.add_middleware(_make_middleware(cooldown_middleware))

        register_all_handlers(client)

        logger.info("Kurigram client created and configured")
        return client

    async def _initialize(self) -> bool:
        """Initialize all services.

        Returns:
            True if initialization successful.
        """
        logger.info("Initializing Telebot...")

        try:
            await connect_to_mongo()
            db = get_db()
            await create_indexes(db)
            logger.info("MongoDB initialized with indexes")
            update_health(database="healthy")
        except Exception as exc:
            logger.critical("Failed to connect to MongoDB", error=str(exc))
            update_health(database="unhealthy", telegram="unknown")
            return False

        self.client = self._create_client()

        try:
            await self.client.start()
            me = await self.client.get_me()
            logger.info("Telegram client started", bot_username=me.username, bot_id=me.id)
            update_health(telegram="healthy")
        except Exception as exc:
            logger.critical("Failed to start Telegram client", error=str(exc))
            update_health(telegram="unhealthy")
            return False

        try:
            self._health_runner = await run_health_server(settings.HEALTH_CHECK_PORT)
            logger.info("Health check server started", port=settings.HEALTH_CHECK_PORT)
        except Exception as exc:
            logger.warning("Failed to start health server", error=str(exc))
            self._health_runner = None

        self._cleanup_task = asyncio.create_task(cleanup_service.start(interval=3600))
        logger.info("Cleanup scheduler started")

        self._running = True
        update_health(status="healthy")
        logger.info("Telebot initialized successfully")
        return True

    async def run(self) -> None:
        """Run the bot."""
        global logger
        logger = setup_logging()

        success = await self._initialize()
        if not success:
            logger.critical("Failed to initialize bot. Exiting.")
            sys.exit(1)

        self._setup_signal_handlers()

        logger.info("Bot is running. Press Ctrl+C to stop.")
        await idle()

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        loop = asyncio.get_running_loop()

        def _signal_handler(sig: int) -> None:
            if not self._running:
                return
            self._running = False
            asyncio.create_task(self._shutdown(sig))

        for sig in (signal.SIGINT, signal.SIGTERM):
            if hasattr(loop, "add_signal_handler"):
                loop.add_signal_handler(sig, _signal_handler, sig)

    async def _shutdown(self, sig: int) -> None:
        """Graceful shutdown.

        Args:
            sig: Signal number.
        """
        logger.info("Graceful shutdown initiated", signal=signal.Signals(sig).name)
        update_health(status="shutting_down")

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        await search_service.close()
        logger.info("Search service closed")

        if self._health_runner:
            await self._health_runner.cleanup()
            logger.info("Health check server stopped")

        if self.client:
            await self.client.stop()
            logger.info("Telegram client stopped")

        await close_mongo()
        logger.info("MongoDB connection closed")

        update_health(status="stopped")
        logger.info("Bot shutdown complete")
        sys.exit(0)


bot = Telebot()


async def main() -> None:
    """Main entry point."""
    global logger
    logger = setup_logging()

    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        await bot._shutdown(signal.SIGINT)
    except Exception as exc:
        logger.critical("Fatal error", error=str(exc), exc_info=True)
        if bot.client:
            await bot.client.stop()
        await close_mongo()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
