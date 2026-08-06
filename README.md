# Telebot - Telegram Search Bot with Credit System

A production-ready Telegram bot with a credit-based number search system, built for Python 3.14+ with async architecture.

## Architecture

| Component | Technology |
|-----------|-----------|
| Language | Python 3.14+ |
| Telegram Library | [Kurigram](https://github.com/kurigram/kurigram) (Pyrogram-compatible fork) |
| Database | MongoDB (async via Motor) |
| HTTP Client | aiohttp (async) |
| Caching | In-memory TTL cache |
| Logging | structlog (JSON structured) |
| Deployment | Docker + docker-compose |

## Project Structure

```
telebot/
├── bot.py                    # Main bot class & entrypoint
├── main.py                   # Simple entry point
├── config/
│   ├── __init__.py
│   ├── config.py             # Settings (pydantic)
│   └── constants.py          # Enums & constants
├── database/
│   ├── __init__.py
│   ├── connection.py          # Motor async MongoDB
│   ├── indexes.py             # Index creation
│   └── repositories/
│       ├── __init__.py
│       ├── user_repo.py
│       ├── search_repo.py
│       ├── credit_repo.py
│       ├── credit_log_repo.py
│       ├── broadcast_repo.py
│       ├── setting_repo.py
│       ├── admin_repo.py
│       ├── ban_repo.py
│       └── statistics_repo.py
├── handlers/
│   ├── __init__.py            # Handler registration
│   ├── start.py
│   ├── help.py
│   ├── search.py
│   ├── history.py
│   ├── credits.py
│   ├── profile.py
│   ├── updates.py
│   ├── welcome.py
│   └── admin_panel.py         # Admin inline keyboard handlers
├── middlewares/
│   ├── __init__.py
│   ├── admin.py               # Admin permission checks
│   ├── rate_limiter.py
│   ├── flood_protection.py
│   ├── cooldown.py
│   ├── sanitization.py
│   └── logging_middleware.py
├── services/
│   ├── __init__.py
│   ├── credit_service.py
│   ├── search_service.py
│   ├── broadcast_service.py
│   ├── telegram_service.py
│   ├── statistics_service.py
│   └── cleanup_service.py
├── utils/
│   ├── __init__.py
│   ├── keyboards.py           # Inline keyboard builders
│   ├── cache.py               # Async TTL cache
│   ├── helpers.py             # Formatting utilities
│   ├── validators.py          # Input validation
│   ├── retry.py               # Retry with exponential backoff
│   ├── export.py              # CSV/JSON export
│   ├── health.py              # Health check HTTP server
│   └── referral.py            # Referral system
├── models/
│   └── __init__.py            # Pydantic data models
├── scripts/
│   ├── install.sh
│   ├── update.sh
│   ├── backup.sh
│   ├── run.sh
│   └── health_check.py
├── docker/
│   └── Dockerfile
├── docker-compose.yml
├── systemd.service
├── supervisor.conf
├── logrotate.conf
├── .env.example
├── requirements.txt
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.14+
- MongoDB 7.0+
- (Optional) Redis

### Local Installation

```bash
# Clone the repository
git clone <repo-url> telebot
cd telebot

# Create virtual environment
python3.14 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run
python bot.py
```

### Docker Deployment

```bash
# Configure environment
cp .env.example .env
# Edit .env

# Start with Docker Compose
docker-compose up -d
```

### VPS Deployment (systemd)

```bash
# Run the install script
bash scripts/install.sh

# Edit .env
nano /opt/telebot/.env

# Restart
systemctl restart telebot

# Check status
systemctl status telebot
journalctl -u telebot -f
```

## Features

### Credit System
- Each search costs 1 credit
- New users start with 0 credits
- Admins can add, remove, or set credits via commands or inline keyboards
- All transactions are logged

### Admin Panel
Access via `/start` → bot menu, or use these commands:

| Command | Description |
|---------|-------------|
| `/addcredit <id> <n> [reason]` | Add credits to user |
| `/removecredit <id> <n> [reason]` | Remove credits |
| `/setcredit <id> <n>` | Set exact credit balance |
| `/creditlog [id]` | View credit transactions |
| `/stats` | View statistics dashboard |
| `/broadcast <msg>` | Broadcast to all users |
| `/ban <id> [reason]` | Ban a user |
| `/unban <id>` | Unban a user |
| `/users` | List all users |
| `/setchannel [channel]` | Configure force-join channel |

### User Panel
- **🔍 Search Number** - Search phone numbers (costs 1 credit)
- **📜 History** - View search history with pagination
- **💳 My Credits** - Check balance and transaction history
- **ℹ️ Help** - Bot help and usage guide
- **📢 Updates** - Latest bot updates
- **👤 Profile** - User profile and stats

### Security
- Admin-only middleware
- Rate limiting (sliding window)
- Flood protection with temporary bans
- Command cooldown (anti-spam)
- Input sanitization (XSS, SQL injection prevention)
- Secret masking in logs

### Data Exports
- Export database to JSON or CSV
- Export logs to JSON or CSV
- Available via admin panel

### Monitoring
- HTTP health check endpoint at `:8080/health`
- Structured JSON logging
- Log rotation (7-14 days retention)
- Automatic MongoDB and Telegram reconnection

## Database Collections

| Collection | Description |
|------------|-------------|
| `users` | User profiles, credits, admin status |
| `searches` | Search logs (query, result, timestamp) |
| `credit_logs` | All credit transactions |
| `credit_logs` | All credit transactions |
| `broadcasts` | Broadcast messages and stats |
| `settings` | Bot configuration (maintenance, force-join) |
| `admin_logs` | Admin action history |
| `bans` | Banned users |
| `statistics` | Daily/monthly stats for analytics |

## Environment Variables

See `.env.example` for all configuration options.

## MongoDB Indexes

Indexes are automatically created on startup:
- `users`: Unique index on `user_id`, indexes on `created_at`, `is_admin`, `banned`, `username`
- `searches`: Indexes on `user_id`, `timestamp`, `query`
- `credit_logs`: Indexes on `user_id`, `timestamp`, `admin_id`
- `broadcasts`: Indexes on `created_at`, `status`
- `settings`: Unique index on `key`
- `admins`: Unique index on `user_id`
- `bans`: Unique index on `user_id`, index on `banned_at`
- `statistics`: Compound unique index on `(date, type)`

## License

MIT
