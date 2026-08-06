"""Configuration module for the Telebot application."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    BOT_TOKEN: str = ""
    API_ID: int = 0
    API_HASH: str = ""

    # MongoDB
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "telebot"

    # Redis (for caching and rate limiting)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # Search service (external API)
    SEARCH_API_URL: str = ""
    SEARCH_API_KEY: str = ""

    # Admin
    ADMIN_IDS: list[int] = [7157722788]

    # Bot
    BOT_USERNAME: str = "telebot_search_bot"
    WELCOME_MESSAGE: str = (
        "👋 Welcome to the Search Bot!\n\n"
        "Use /search to look up numbers.\n"
        "Check /credits for your balance.\n"
        "Type /help for assistance."
    )
    MAINTENANCE_MODE: bool = False

    # Rate limiting
    RATE_LIMIT_WINDOW: int = 60  # seconds
    RATE_LIMIT_MAX_REQUESTS: int = 20

    # Flood protection
    FLOOD_THRESHOLD: int = 5
    FLOOD_WINDOW: int = 10  # seconds

    # Command cooldown
    COMMAND_COOLDOWN: int = 5  # seconds

    # Cache
    CACHE_TTL: int = 300  # seconds (5 minutes)
    CACHE_MAX_SIZE: int = 1000

    # Credit defaults
    DEFAULT_CREDITS: int = 0

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "logs/bot.log"

    # Health check
    HEALTH_CHECK_PORT: int = 8080

    # Update channel for force-join
    FORCE_JOIN_CHANNEL: str = ""

    # Referral
    REFERRAL_CREDITS: int = 5

    # Cleanup
    CLEANUP_DELETE_SEARCH_LOGS_DAYS: int = 90
    CLEANUP_DELETE_OLD_LOGS_DAYS: int = 30

    # Broadcast cooldown
    BROADCAST_PAUSE: float = 1.0


settings: Settings = Settings()
