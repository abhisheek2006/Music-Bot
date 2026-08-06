"""Logging setup module with structured logging."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import structlog
from structlog.processors import (
    JSONRenderer,
    KeyValueRenderer,
    TimeStamper,
    format_exc_info,
)
from structlog.stdlib import (
    LoggerFactory,
    PosJSONRenderer,
    ProcessorFormatter,
)
from structlog.typing import EventDict, WrappedLogger

from config.config import settings


def _mask_secrets(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    """Mask sensitive fields in log entries."""
    sensitive_keys = {
        "bot_token",
        "api_hash",
        "mongo_uri",
        "redis_password",
        "search_api_key",
        "password",
        "token",
        "secret",
        "authorization",
    }
    masked_keys = set()

    for key in list(event_dict.keys()):
        key_lower = key.lower()
        for sensitive in sensitive_keys:
            if sensitive in key_lower:
                event_dict[key] = "***MASKED***"
                masked_keys.add(key)
                break

    return event_dict


def _remove_none_values(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    """Remove None values from log entries."""
    return {k: v for k, v in event_dict.items() if v is not None}


def setup_logging() -> structlog.BoundLogger:
    """Set up structured logging for the application.

    Returns:
        BoundLogger: Configured structlog logger.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    processors: list = [
        structlog.contextvars.merge_contextvars,
        _remove_none_values,
        _mask_secrets,
        TimeStamper(fmt="iso", utc=True),
        format_exc_info,
        structlog.processors.add_log_level,
    ]

    if settings.LOG_FORMAT == "json":
        processors.append(JSONRenderer())
    else:
        processors.append(KeyValueRenderer(key_order=["timestamp", "level", "event"]))

    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        stream=sys.stdout,
    )

    stdlib_handler = logging.FileHandler(settings.LOG_FILE)
    stdlib_handler.setFormatter(
        ProcessorFormatter(
            foreign_pre_chain=[
                TimeStamper(fmt="iso", utc=True),
                structlog.processors.add_log_level,
            ],
            processors=[
                ProcessorFormatter.remove_processor_formatter,
                lambda _, __, ed: _mask_secrets(None, "", ed),
                JSONRenderer() if settings.LOG_FORMAT == "json" else PosJSONRenderer(),
            ],
            logger_factory=StdlibLoggerFactory(),
        )
    )
    logging.getLogger().addHandler(stdlib_handler)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=LoggerFactory(),
        cache_logger_on_first=True,
    )

    return structlog.get_logger("telebot")


class StdlibLoggerFactory:
    """Logger factory for stdlib logging integration."""

    def __call__(self) -> logging.Logger:
        return logging.getLogger("telebot")


def get_logger(name: str = "telebot") -> structlog.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name.

    Returns:
        BoundLogger instance.
    """
    return structlog.get_logger(name)
