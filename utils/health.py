"""Health check HTTP server."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from aiohttp import web

from utils.logging_setup import get_logger

logger = get_logger("utils.health")

_health_status: dict[str, Any] = {
    "status": "starting",
    "started_at": datetime.now(UTC).isoformat(),
    "checks": {
        "database": "unknown",
        "telegram": "unknown",
    },
}


def update_health(
    database: str = "unknown",
    telegram: str = "unknown",
    status: str = "unknown",
) -> None:
    """Update the health status.

    Args:
        database: Database status.
        telegram: Telegram status.
        status: Overall status.
    """
    _health_status["checks"]["database"] = database
    _health_status["checks"]["telegram"] = telegram
    _health_status["status"] = status
    _health_status["last_updated"] = datetime.now(UTC).isoformat()


def get_health_status() -> dict[str, Any]:
    """Get the current health status.

    Returns:
        Health status dictionary.
    """
    return _health_status.copy()


def create_health_app() -> web.Application:
    """Create the health check aiohttp application.

    Returns:
        aiohttp Application instance.
    """
    app = web.Application()

    async def health_handler(request: web.Request) -> web.Response:
        """Handle health check requests."""
        status_code = 200 if _health_status["status"] in ("healthy", "degraded") else 503
        body = json.dumps(
            _health_status,
            default=str,
            indent=2,
        )
        return web.Response(
            text=body,
            content_type="application/json",
            status=status_code,
        )

    async def ping_handler(request: web.Request) -> web.Response:
        """Handle ping requests."""
        return web.Response(text="pong", status=200)

    app.router.add_get("/health", health_handler)
    app.router.add_get("/health/live", health_handler)
    app.router.add_get("/health/ready", health_handler)
    app.router.add_get("/ping", ping_handler)

    return app


async def run_health_server(port: int = 8080) -> web.AppRunner:
    """Run the health check HTTP server.

    Args:
        port: Port to listen on.

    Returns:
        AppRunner instance.
    """
    app = create_health_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("Health check server started", port=port)
    return runner
