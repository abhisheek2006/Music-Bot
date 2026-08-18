# Telegram Music Bot

A production-ready Python bot that joins Telegram **group voice chats** and plays music
with a per-group queue, automatic next-song playback, inline controls, volume control and
graceful error recovery. Designed for personal/group use on a Linux VPS or Railway.

## Requirements

- **Python** 3.11 or 3.12 (verified stack; do not use 3.14)
- **FFmpeg** installed on the host (required by the voice library)
- A **Telegram bot token** (BotFather)
- A **Telegram user account** session — **bots cannot join voice chats**, so playback
  requires a user account that is a member of your group

### Library stack (verified compatible)

| Package       | Version    | Purpose                              |
|---------------|------------|--------------------------------------|
| Pyrogram      | 2.0.106    | MTProto client (bot + user sessions) |
| py-tgcalls    | 2.3.3      | Voice-chat streaming (NTgCalls core) |
| ntgcalls      | 2.2.5      | Native WebRTC voice-chat engine      |
| TgCrypto      | 1.2.5      | Fast crypto for Pyrogram             |
| aiohttp       | 3.9.5      | Async HTTP (thumbnails)              |
| yt-dlp        | 2026.7.4   | Search + metadata extraction         |
| python-dotenv | 1.2.3      | `.env` loading                       |

This uses the **current** `py-tgcalls` (NTgCalls-based) API — not the old MarshalX
`tgcalls` bindings. Wheels are prebuilt for Linux/macOS/Windows on Python 3.10–3.14.

## Getting credentials

### 1. API_ID and API_HASH

1. Go to https://my.telegram.org and log in.
2. Click **API development tools**.
3. Create an application. You get an **api_id** and **api_hash**.
   (This is the official Telegram API credentials page.)

### 2. BOT_TOKEN

1. Open Telegram and message **@BotFather**.
2. Send `/newbot`, choose a name and username.
3. Copy the token that BotFather replies with.

### 3. SESSION_STRING (the user account)

Because regular bot accounts **cannot join voice chats**, you need a Pyrogram string
session of a normal Telegram account:

```bash
pip install pyrogram tgcrypto
python -m session_string
```

Enter the API_ID / API_HASH and log in with the phone number. Copy the printed string
into `SESSION_STRING` in your `.env`. The same account must be a **member of the group**
where you want music (admin is recommended so it can reliably join).

## FFmpeg

The voice library converts audio with FFmpeg. The bot checks for it at startup and exits
with a clear message if it is missing.

Ubuntu/Debian:

```bash
sudo apt update
sudo apt install ffmpeg
```

Verify:

```bash
ffmpeg -version
```

## Installation

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Copy the example file and fill it in:

```bash
cp .env.example .env
```

```dotenv
API_ID=12345678
API_HASH=your_api_hash
BOT_TOKEN=123456789:your_bot_token
SESSION_STRING=your_pyrogram_string_session
OWNER_ID=0
LOG_GROUP_ID=0
AUTO_LEAVE=true
AUTO_LEAVE_DELAY=300
DEFAULT_VOLUME=80
QUEUE_LIMIT=30
```

Required: `API_ID`, `API_HASH`, `BOT_TOKEN`.
Required for voice playback: `SESSION_STRING`.
`OWNER_ID` enables `/broadcast`, `/stats`, `/restart`.

Never commit `.env` — it is already in `.gitignore`.

## Running locally

```bash
python bot.py
```

Expected startup output:

```
================================
Telegram Music Bot
================================

✓ Configuration loaded
✓ FFmpeg detected
✓ Telegram client initialized
✓ Voice system initialized
✓ Bot started

Bot is running...
```

## Usage

Add the **bot** and the **user account** to your group, then:

1. Start a **voice chat** in the group.
2. `/join` — bot joins (it can also auto-join on `/play`).
3. `/play Alan Walker Faded` — plays in the voice chat.

### Commands

| Command | Description |
|---|---|
| `/start` `/help` | Welcome and command help |
| `/ping` | Latency check |
| `/play <song/URL>` | Search and play / queue a song |
| `/vplay <song/URL>` | Play as video in a voice chat |
| `/stream <URL>` | Stream a direct audio URL |
| `/song <song>` | Show song info without playing |
| `/join` `/leave` | Join / leave the voice chat |
| `/pause` `/resume` | Pause / resume playback |
| `/skip` | Skip the current song |
| `/stop` | Stop playback and clear queue |
| `/mute` `/unmute` | Mute / unmute audio |
| `/volume <1-100>` | Set volume |
| `/queue` | Show the queue |
| `/nowplaying` | Show current song + progress |
| `/remove <n>` | Remove queued song #n |
| `/clear` | Clear the queue (keeps current song) |
| `/loop` | Toggle looping the current song |
| `/lyrics artist - song` | Fetch lyrics |
| `/stats` | Owner-only bot stats |
| `/broadcast <text>` | Owner-only broadcast |
| `/restart` | Owner-only restart |

### Permissions

- Everyone: `/play`, `/song`, `/queue`, `/nowplaying`, `/lyrics`, `/join`
- Admins (or the song requester): `/skip`, `/stop`, `/clear`, `/remove`, `/volume`,
  `/pause`, `/resume`, `/mute`, `/unmute`, `/leave`, `/loop`
- Owner (`OWNER_ID`): `/broadcast`, `/stats`, `/restart`

Inline buttons (`⏸ Pause`, `⏭ Skip`, `⏹ Stop`, `📋 Queue`) are shown on the now-playing
message and enforce the same permissions.

## Running on a VPS (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-venv ffmpeg git
git clone https://github.com/your-user/telegram-music-bot.git
cd telegram-music-bot

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env with your credentials
python bot.py
```

Keep it running with a process manager:

### systemd

```bash
sudo useradd -m telegram
sudo cp systemd/telegram-music-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable telegram-music-bot
sudo systemctl start telegram-music-bot
journalctl -u telegram-music-bot -f
```

Adjust `User`, `WorkingDirectory` and the `.env` path in the service file to match your
setup.

## Deploying on Railway

The repository includes a `Dockerfile` (installs FFmpeg), `railway.json` and
`nixpacks.toml`.

1. Create a new Railway project and deploy this repo.
2. Railway auto-detects the Dockerfile.
3. Add the **Variables**: `API_ID`, `API_HASH`, `BOT_TOKEN`, `SESSION_STRING`,
   `OWNER_ID`, and any other options.
4. Railway keeps the process alive and restarts it on failure.

Alternatively (no Dockerfile): Railway's Nixpacks builder uses `nixpacks.toml`, which
installs FFmpeg and runs `python bot.py`. A minimum instance size is recommended because
music streaming is CPU/network heavy.

## Troubleshooting

- **`Startup error: FFmpeg is not installed`** — install FFmpeg (see above) or add it in
  the Docker image / Railway buildpack.
- **`No active voice chat found`** — start a voice chat in the group first (the bot will
  not create one itself).
- **`SESSION_STRING` missing warning** — voice features are disabled. Generate a user
  session with `python -m session_string`.
- **"Bot can't join the voice chat"** — the user account must be a member of the group and
  the group must have `Everyone is an administrator` disabled, or the user must have
  permission to join voice chats.
- **Song plays but no audio** — make sure the group voice chat is actually active and the
  bot account is not muted by the group.
- **`FloodWait` errors** — Telegram rate limits; the bot waits and retries automatically.
- **Sound quality** — set `DEFAULT_VOLUME` and adjust bitrate via py-tgcalls
  `AudioQuality` in `music/player.py`.

## Project structure

```
telegram-music-bot/
├── bot.py                 # entrypoint, startup checks, graceful shutdown
├── config.py              # environment loading + validation
├── session_string.py      # generates a Pyrogram string session
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile / railway.json / nixpacks.toml
├── handlers/              # Telegram command/callback handlers
│   ├── start.py  play.py  controls.py  queue.py  voice.py  admin.py  callbacks.py
├── music/
│   ├── player.py          # playback engine (PyTgCalls), auto-next, now-playing
│   ├── queue.py           # per-group queue + Track model
│   ├── downloader.py      # yt-dlp search / metadata / telegram audio
│   └── ffmpeg.py          # ffmpeg availability check
├── utils/
│   ├── permissions.py     # owner/admin/requester checks
│   ├── formatting.py      # safe HTML formatting
│   ├── keyboards.py       # inline control buttons
│   ├── cleanup.py         # temp file cleanup
│   └── logging_setup.py   # logging (secrets redacted)
├── systemd/               # systemd service example
└── downloads/             # temporary audio files (auto-cleaned)
```

## Notes

- Queues, playback state and settings are in-memory and **per group** — groups never
  interfere with each other.
- Temporary audio files are deleted after playback; `downloads/` never grows unbounded.
- Only public, legally accessible media is processed. The bot does not bypass DRM,
  paywalls, authentication or any access controls.
# Music-Bot
