#!/usr/bin/env bash
set -e

PROJECT_NAME="telebot"
PROJECT_DIR="/opt/$PROJECT_NAME"

echo "=== Installing $PROJECT_NAME ==="

# Update system
apt-get update -y

# Install dependencies
apt-get install -y python3 python3-pip python3-venv git curl nginx

# Install MongoDB
if ! command -v mongod &> /dev/null; then
    echo "Installing MongoDB..."
    wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | apt-key add -
    echo "deb http://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    apt-get update -y
    apt-get install -y mongodb-org
    mkdir -p /data/db
    mongod --fork --logpath /var/log/mongodb/mongod.log
fi

# Install Redis (optional, for rate limiting)
if ! command -v redis-server &> /dev/null; then
    echo "Installing Redis..."
    apt-get install -y redis-server
    systemctl enable redis-server
    systemctl start redis-server
fi

# Clone or navigate to project
if [ ! -d "$PROJECT_DIR" ]; then
    git clone https://github.com/your-repo/$PROJECT_NAME.git "$PROJECT_DIR" || {
        mkdir -p "$PROJECT_DIR"
        cp -r ./* "$PROJECT_DIR/"
    }
fi

cd "$PROJECT_DIR"

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install --upgrade pip
# Install Kurigram from GitHub dev branch for colored button support (ButtonStyle)
pip install "git+https://github.com/KurimuzonAkuma/kurigram.git"
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration."
    echo "   nano $PROJECT_DIR/.env"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Create systemd service
cat > /etc/systemd/system/$PROJECT_NAME.service << EOF
[Unit]
Description=$PROJECT_NAME Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload
systemctl enable $PROJECT_NAME
systemctl start $PROJECT_NAME

echo "=== Installation Complete ==="
echo "Check status: systemctl status $PROJECT_NAME"
echo "View logs: journalctl -u $PROJECT_NAME -f"
