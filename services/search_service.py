"""Search service using aiohttp for async HTTP requests."""

from __future__ import annotations

import time
from typing import Any

import aiohttp
from aiohttp import ClientTimeout

from config.config import settings
from utils.cache import cache
from utils.logging_setup import get_logger
from utils.retry import RetryError, retry_async

logger = get_logger("services.search")

_client_timeout = ClientTimeout(total=30)


class SearchService:
    """Service for performing number searches via external API."""

    def __init__(self) -> None:
        self._api_url = settings.SEARCH_API_URL.rstrip("/")
        self._api_key = settings.SEARCH_API_KEY
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session.

        Returns:
            ClientSession instance.
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=_client_timeout)
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("Search service HTTP session closed")

    async def search(self, query: str, user_id: int) -> dict[str, Any]:
        """Perform a number search.

        Args:
            query: Search query (phone number).
            user_id: User performing the search.

        Returns:
            Search result dictionary.

        Raises:
            RetryError: If all retries fail.
            ValueError: If no API URL is configured.
        """
        cached = await cache.get(f"search:{query}")
        if cached:
            logger.info("Cache hit for search", query=query, user_id=user_id)
            return cached

        if not self._api_url:
            raise ValueError("SEARCH_API_URL is not configured")

        session = await self._get_session()

        async def _do_search() -> dict[str, Any]:
            headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
            url = f"{self._api_url}?query={query}"
            start_time = time.time()

            async with session.get(url, headers=headers) as response:
                duration_ms = int((time.time() - start_time) * 1000)
                data = await response.json()

                if response.status != 200:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=data.get("message", "Unknown error"),
                    )

                result = {
                    "query": query,
                    "result": data.get("result", data),
                    "success": data.get("success", True),
                    "source": data.get("source", "api"),
                    "duration_ms": duration_ms,
                }

                await cache.set(f"search:{query}", result)
                return result

        try:
            return await retry_async(
                _do_search,
                max_retries=3,
                base_delay=1.0,
                max_delay=30.0,
                exceptions=(aiohttp.ClientError, aiohttp.ClientResponseError),
                context=f"search:{query}",
            )
        except RetryError as exc:
            logger.error("Search failed after retries", query=query, error=str(exc))
            return {
                "query": query,
                "result": None,
                "success": False,
                "source": "api",
                "duration_ms": 0,
                "error": str(exc),
            }

    async def format_result(self, result: dict[str, Any]) -> str:
        """Format search result for display.

        Args:
            result: Search result dictionary.

        Returns:
            Formatted string.
        """
        if result.get("success"):
            data = result.get("result", {})
            if isinstance(data, dict):
                lines = []
                for key, value in data.items():
                    key_str = str(key).replace("_", " ").title()
                    value_str = str(value) if value is not None else "N/A"
                    lines.append(f"<b>{key_str}:</b> {value_str}")
                return "\n".join(lines) if lines else "No data found."
            return str(data) if data else "No results found."
        return f"❌ Search failed: {result.get('error', 'Unknown error')}"


search_service = SearchService()
