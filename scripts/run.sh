#!/usr/bin/env bash
set -e

PROJECT_DIR="/opt/telebot"

echo "=== Running Telebot ==="

cd "$PROJECT_DIR"

# Activate virtual environment
source venv/bin/activate

# Ensure logs directory exists
mkdir -p logs

# Run the bot
exec python bot.py
