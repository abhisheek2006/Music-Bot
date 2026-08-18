from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


class ConfigError(Exception):
    pass


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value.strip())
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number.") from exc


class Settings:
    def __init__(self) -> None:
        self.API_ID: str = os.getenv("API_ID", "").strip()
        self.API_HASH: str = os.getenv("API_HASH", "").strip()
        self.BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
        self.SESSION_STRING: str = os.getenv("SESSION_STRING", "").strip()
        self.OWNER_ID: int = _int("OWNER_ID", 0)
        self.LOG_GROUP_ID: int = _int("LOG_GROUP_ID", 0)
        self.AUTO_LEAVE: bool = _bool(os.getenv("AUTO_LEAVE"), True)
        self.AUTO_LEAVE_DELAY: int = _int("AUTO_LEAVE_DELAY", 300)
        self.DEFAULT_VOLUME: int = _int("DEFAULT_VOLUME", 80)
        self.QUEUE_LIMIT: int = _int("QUEUE_LIMIT", 30)
        self.DOWNLOAD_PATH: Path = Path(os.getenv("DOWNLOAD_PATH", "downloads"))
        self.PROGRESS_INTERVAL: int = _int("PROGRESS_INTERVAL", 10)

    def validate(self) -> None:
        if not self.API_ID:
            raise ConfigError("API_ID is not configured.")
        if not self.API_ID.isdigit():
            raise ConfigError("API_ID must be a number.")
        if not self.API_HASH:
            raise ConfigError("API_HASH is not configured.")
        if not self.BOT_TOKEN:
            raise ConfigError("BOT_TOKEN is not configured.")
        if not 1 <= self.DEFAULT_VOLUME <= 100:
            raise ConfigError("DEFAULT_VOLUME must be between 1 and 100.")
        if self.QUEUE_LIMIT < 1:
            raise ConfigError("QUEUE_LIMIT must be at least 1.")
        if self.AUTO_LEAVE_DELAY < 10:
            raise ConfigError("AUTO_LEAVE_DELAY must be at least 10 seconds.")
        self.DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)


settings = Settings()
