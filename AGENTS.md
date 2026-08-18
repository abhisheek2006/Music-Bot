# AGENTS.md

## Project Overview

Telegram Music Bot — a production-ready Python bot that joins Telegram group voice chats
and plays music. Built for Python 3.11/3.12 with Pyrogram, py-tgcalls (NTgCalls-based) and
yt-dlp.

## Build & Test Commands

### Dependencies

```bash
pip install -r requirements.txt
# For development/linting:
pip install -r requirements-dev.txt
```

### Linting

```bash
ruff check .
ruff format --check .
```

### Type Checking

```bash
mypy . --ignore-missing-imports --python-version 3.11
```

### Syntax check

```bash
python -m compileall .
```

### Running the Bot

```bash
python bot.py
```

### Generating a user session

```bash
python -m session_string
```

## Code Style Guidelines

- Use `from __future__ import annotations` in all files
- Use type hints throughout (PEP 484)
- No comments unless explicitly requested
- Use standard-library `logging` (setup in `utils/logging_setup.py`)
- Use aiohttp for async HTTP requests
- Use `ruff` for linting and `mypy` for type checking
- Keep Python 3.11/3.12 compatibility (do not target 3.14 — the voice stack does not support it)

## Architecture Notes

- **`bot.py`** is the entrypoint: loads config, checks FFmpeg, builds the Pyrogram
  `Client`(s) and `PyTgCalls`, registers handlers, then `idle()`.
- **Two clients**: a bot client (`telegram-music-bot`, bot_token) handles all
  commands; an optional user client (`telegram-music-user`, SESSION_STRING) powers
  voice chat via `PyTgCalls`. Without `SESSION_STRING` the bot still runs but voice
  commands reply that voice is disabled.
- **Handlers** are registered via `register_all(app, manager, downloader, settings)`
  in `handlers/__init__.py`.
- **`music/player.py`** holds all voice-chat logic (`PlayerManager`): per-chat playback,
  auto-next, auto-leave, now-playing messages, stream-end handling. It is the only module
  that talks to PyTgCalls.
- **`music/queue.py`** defines `Track` and a per-chat `QueueManager` (in-memory).
- **`music/downloader.py`** wraps yt-dlp (search, extract, direct URLs) and Telegram audio.
- **`config.py`** centralizes environment config; `settings.validate()` raises
  `ConfigError` with the exact messages: "API_ID is not configured.",
  "API_HASH is not configured.", "BOT_TOKEN is not configured."
- **Utils** contain helpers: permissions (owner/admin/requester), HTML-safe formatting,
  inline keyboards, file cleanup, redacting logging.
- **Runs standalone** — no database, no web server, no Docker Compose required
  (deploy via `Dockerfile` / `railway.json` / Nixpacks).

## Security Rules

- Never log or expose API secrets (`API_HASH`, `BOT_TOKEN`, `SESSION_STRING`).
  `utils/logging_setup.py` redacts these values.
- Always HTML-escape user-provided text before embedding it in messages
  (use `utils.formatting.esc`).
- `.env` and session files must never be committed.
