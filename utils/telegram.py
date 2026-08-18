from __future__ import annotations

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import Message


async def reply_html(message: Message, text: str, **kwargs) -> Message | None:
    kwargs.setdefault("parse_mode", ParseMode.HTML)
    kwargs.setdefault("disable_web_page_preview", True)
    return await message.reply(text, **kwargs)


async def send_html(client: Client, chat_id: int, text: str, **kwargs) -> Message | None:
    kwargs.setdefault("parse_mode", ParseMode.HTML)
    kwargs.setdefault("disable_web_page_preview", True)
    return await client.send_message(chat_id, text, **kwargs)
