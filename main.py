#!/usr/bin/env python3
"""Simple entry point for the Telebot."""

import asyncio
import sys

from bot import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
