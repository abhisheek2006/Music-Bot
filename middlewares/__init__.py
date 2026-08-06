"""Middlewares package."""

from __future__ import annotations

from middlewares.admin import AdminMiddleware
from middlewares.cooldown import CooldownMiddleware
from middlewares.flood_protection import FloodProtectionMiddleware
from middlewares.logging_middleware import LoggingMiddleware
from middlewares.rate_limiter import RateLimiterMiddleware
from middlewares.sanitization import SanitizationMiddleware

__all__ = [
    "AdminMiddleware",
    "CooldownMiddleware",
    "FloodProtectionMiddleware",
    "LoggingMiddleware",
    "RateLimiterMiddleware",
    "SanitizationMiddleware",
]
