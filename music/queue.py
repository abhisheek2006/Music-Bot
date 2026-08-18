from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass
class Track:
    title: str
    url: str = ""
    duration: int = 0
    thumbnail: str | None = None
    uploader: str | None = None
    requester_id: int | None = None
    requester_name: str | None = None
    source: str = "youtube"
    stream_url: str | None = None
    file_path: str | None = None


class QueueManager:
    def __init__(self, limit: int = 30) -> None:
        self._limit = limit
        self._queues: dict[int, deque[Track]] = defaultdict(deque)
        self._current: dict[int, Track | None] = defaultdict(lambda: None)
        self._locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

    def lock(self, chat_id: int) -> asyncio.Lock:
        return self._locks[chat_id]

    def add(self, chat_id: int, track: Track) -> int | None:
        queue = self._queues[chat_id]
        if len(queue) >= self._limit:
            return None
        queue.append(track)
        return len(queue)

    def size(self, chat_id: int) -> int:
        return len(self._queues[chat_id])

    def is_empty(self, chat_id: int) -> bool:
        return not self._queues[chat_id]

    def peek(self, chat_id: int) -> Track | None:
        queue = self._queues[chat_id]
        return queue[0] if queue else None

    def pop(self, chat_id: int) -> Track | None:
        queue = self._queues[chat_id]
        return queue.popleft() if queue else None

    def remove(self, chat_id: int, position: int) -> Track | None:
        queue = self._queues[chat_id]
        index = position - 1
        if index < 0 or index >= len(queue):
            return None
        item = queue[index]
        del queue[index]
        return item

    def clear(self, chat_id: int) -> int:
        queue = self._queues[chat_id]
        removed = len(queue)
        queue.clear()
        return removed

    def get_queue(self, chat_id: int) -> list[Track]:
        return list(self._queues[chat_id])

    def set_current(self, chat_id: int, track: Track | None) -> None:
        self._current[chat_id] = track

    def current(self, chat_id: int) -> Track | None:
        return self._current.get(chat_id)
