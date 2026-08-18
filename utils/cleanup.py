from __future__ import annotations

import asyncio
import logging
from pathlib import Path

logger = logging.getLogger("bot.cleanup")


def _unlink_sync(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        logger.warning("Failed to remove temp file: %s", path)


async def delete_file(path: str | Path | None) -> None:
    if not path:
        return
    await asyncio.to_thread(_unlink_sync, Path(path))


async def cleanup_downloads(directory: Path) -> None:
    await asyncio.to_thread(_cleanup_sync, directory)


def _cleanup_sync(directory: Path) -> None:
    try:
        for entry in directory.iterdir():
            if entry.is_file():
                _unlink_sync(entry)
    except OSError:
        logger.warning("Could not read downloads directory: %s", directory)
