#!/usr/bin/env bash
set -e

PROJECT_DIR="/opt/telebot"
BACKUP_DIR="/opt/telebot/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "=== Backing up Telebot ==="

mkdir -p "$BACKUP_DIR"

# Backup MongoDB database
echo "Backing up MongoDB..."
mongodump --out "$BACKUP_DIR/mongodb_$TIMESTAMP" --db telebot

# Backup configuration
echo "Backing up configuration..."
cp "$PROJECT_DIR/.env" "$BACKUP_DIR/dotenv_$TIMESTAMP" 2>/dev/null || true

# Backup logs
echo "Backing up logs..."
if [ -d "$PROJECT_DIR/logs" ]; then
    tar -czf "$BACKUP_DIR/logs_$TIMESTAMP.tar.gz" -C "$PROJECT_DIR" logs/
fi

# Remove backups older than 7 days
find "$BACKUP_DIR" -name "mongodb_*" -mtime +7 -exec rm -rf {} \; 2>/dev/null || true
find "$BACKUP_DIR" -name "dotenv_*" -mtime +7 -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "logs_*.tar.gz" -mtime +7 -delete 2>/dev/null || true

echo "=== Backup Complete ==="
echo "Backups stored in: $BACKUP_DIR"
ls -la "$BACKUP_DIR"
