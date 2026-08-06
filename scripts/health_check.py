#!/usr/bin/env python3
"""Health check script for monitoring."""

import asyncio
import json
import os
import sys

import aiohttp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def check_health() -> int:
    """Check the health endpoint."""
    port = int(os.environ.get("HEALTH_CHECK_PORT", "8080"))

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(f"http://localhost:{port}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(json.dumps(data, indent=2))
                    return 0
                else:
                    print(f"Health check failed with status: {response.status}")
                    return 1
    except Exception as exc:
        print(f"Health check failed: {exc}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(check_health())
    sys.exit(exit_code)
