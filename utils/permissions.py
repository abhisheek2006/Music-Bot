from __future__ import annotations

import time

from pyrogram import Client
from pyrogram.enums import ChatMemberStatus, ChatType

from config import settings


def is_owner(user_id: int | None) -> bool:
    if not user_id:
        return False
    return bool(settings.OWNER_ID) and user_id == settings.OWNER_ID


class PermissionCache:
    def __init__(self, ttl: int = 120) -> None:
        self._ttl = ttl
        self._store: dict[tuple[int, int], tuple[bool, float]] = {}

    def get(self, chat_id: int, user_id: int) -> bool | None:
        entry = self._store.get((chat_id, user_id))
        if entry is None:
            return None
        value, expires = entry
        if time.monotonic() > expires:
            self._store.pop((chat_id, user_id), None)
            return None
        return value

    def set(self, chat_id: int, user_id: int, value: bool) -> None:
        self._store[(chat_id, user_id)] = (value, time.monotonic() + self._ttl)

    def clear_chat(self, chat_id: int) -> None:
        for key in [k for k in self._store if k[0] == chat_id]:
            self._store.pop(key, None)


permission_cache = PermissionCache()


def is_group(chat_type: ChatType) -> bool:
    return chat_type in (ChatType.GROUP, ChatType.SUPERGROUP)


async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    cached = permission_cache.get(chat_id, user_id)
    if cached is not None:
        return cached
    result = False
    try:
        member = await client.get_chat_member(chat_id, user_id)
        result = member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    except Exception:
        result = False
    permission_cache.set(chat_id, user_id, result)
    return result


async def can_control(
    client: Client,
    chat_id: int,
    user_id: int | None,
    requester_id: int | None = None,
) -> bool:
    if not user_id:
        return False
    if is_owner(user_id):
        return True
    if requester_id and user_id == requester_id:
        return True
    return await is_admin(client, chat_id, user_id)
