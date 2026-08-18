from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGGING_DIR = Path("logs")

SECRET_FIELDS = ("BOT_TOKEN", "API_HASH", "SESSION_STRING", "API_ID")


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        for field in SECRET_FIELDS:
            message = message.replace(field, "[REDACTED]")
        return message


def setup_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    fmt = RedactingFormatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    root.addHandler(console)

    try:
        LOGGING_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            LOGGING_DIR / "bot.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
        )
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
    except OSError:
        pass

    logging.getLogger("pyrogram").setLevel(logging.INFO)
    logging.getLogger("pytgcalls").setLevel(logging.INFO)
    logging.getLogger("ntgcalls").setLevel(logging.INFO)
