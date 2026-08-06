# AGENTS.md

## Project Overview

Telebot is a production-ready Telegram bot with a credit system, built for Python 3.14+ using Kurigram.

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
mypy . --ignore-missing-imports --python-version 3.14
```

### Running the Bot
```bash
# Local
python bot.py

# Docker
docker-compose up -d
```

### Health Check
```bash
python scripts/health_check.py
curl http://localhost:8080/health
```

## Code Style Guidelines

- Use `from __future__ import annotations` in all files
- Use type hints throughout (PEP 484)
- Follow existing patterns in `handlers/`, `services/`, `database/`
- No comments unless explicitly requested
- Use structlog for logging (structured, JSON format)
- Use Motor for async MongoDB operations
- Use aiohttp for async HTTP requests

## Architecture Notes

- **Handlers** are registered via `register_handlers(client)` pattern
- **Middlewares** implement `on_message` and `on_callback_query` methods
- **Services** contain business logic (credit, search, broadcast, etc.)
- **Repositories** contain database operations
- **Models** are Pydantic BaseModel subclasses
- **Utils** contain helper functions (keyboards, cache, retry, etc.)
