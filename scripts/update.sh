#!/usr/bin/env bash
set -e

PROJECT_DIR="/opt/telebot"

echo "=== Updating Telebot ==="

cd "$PROJECT_DIR"

# Stop the service
systemctl stop telebot

# Pull latest changes (if using git)
if [ -d .git ]; then
    git pull origin main
fi

# Update virtual environment
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Restart the service
systemctl restart telebot

echo "=== Update Complete ==="
echo "Status: systemctl status telebot"
echo "Logs: journalctl -u telebot -f"
