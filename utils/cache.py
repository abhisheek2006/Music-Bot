"""Async TTL cache with size-based eviction."""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from collections.abc import Callable
from typing import Any


class AsyncTTLCache:
    """Asynchronous TTL cache with LRU eviction.

    Thread-safe (async-safe) cache with time-to-live and maximum size.
    """

    def __init__(self, ttl: int = 300, maxsize: int = 1000) -> None:
        """Initialize the cache.

        Args:
            ttl: Time-to-live in seconds.
            maxsize: Maximum number of entries.
        """
        self._ttl = ttl
        self._maxsize = maxsize
        self._cache: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the cache.

        Args:
            key: Cache key.
            default: Default value if key not found.

        Returns:
            Cached value or default.
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return default

            expiry, value = entry
            if time.time() > expiry:
                del self._cache[key]
                return default

            self._cache.move_to_end(key)
            return value

    async def set(self, key: str, value: Any) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key.
            value: Value to cache.
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]

            self._cache[key] = (time.time() + self._ttl, value)
            self._cache.move_to_end(key)

            while len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)

    async def delete(self, key: str) -> None:
        """Delete a key from the cache.

        Args:
            key: Cache key.
        """
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: int | None = None,
    ) -> Any:
        """Get a value or compute and set it.

        Args:
            key: Cache key.
            factory: Callable to compute the value if not cached.
            ttl: Optional override TTL.

        Returns:
            Cached or computed value.
        """
        value = await self.get(key)
        if value is not None:
            return value

        value = await factory() if asyncio.iscoroutinefunction(factory) else factory()

        if ttl is not None:
            self._cache[key] = (time.time() + ttl, value)
        else:
            await self.set(key, value)

        return value

    def __len__(self) -> int:
        """Return number of cached entries."""
        return len(self._cache)

    async def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed.
        """
        now = time.time()
        expired_keys = [key for key, (expiry, _) in self._cache.items() if now > expiry]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)


# Global cache instance
cache = AsyncTTLCache(
    ttl=300,
    maxsize=1000,
)
