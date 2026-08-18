from __future__ import annotations

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

PREFIX = "mp"


def _data(action: str) -> str:
    return f"{PREFIX}:{action}"


def player_keyboard(paused: bool = False) -> InlineKeyboardMarkup:
    if paused:
        row1 = [
            InlineKeyboardButton("▶️ Resume", _data("resume")),
            InlineKeyboardButton("⏭ Skip", _data("skip")),
        ]
    else:
        row1 = [
            InlineKeyboardButton("⏸ Pause", _data("pause")),
            InlineKeyboardButton("⏭ Skip", _data("skip")),
        ]
    row2 = [
        InlineKeyboardButton("⏹ Stop", _data("stop")),
        InlineKeyboardButton("📋 Queue", _data("queue")),
    ]
    return InlineKeyboardMarkup([row1, row2])
