from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any

import aiohttp
from pyrogram import Client
from pyrogram.enums import ParseMode
from pytgcalls import PyTgCalls
from pytgcalls import filters as fl
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import (
    AudioQuality,
    ChatUpdate,
    GroupCallConfig,
    MediaStream,
    StreamEnded,
    VideoQuality,
)

from config import Settings
from music.downloader import Downloader
from music.queue import QueueManager, Track
from utils import cleanup
from utils.formatting import format_now_playing
from utils.keyboards import player_keyboard

logger = logging.getLogger("bot.player")


class VoiceDisabledError(Exception):
    pass


class VoiceChatNotFound(Exception):
    pass


class TrackPlaybackError(Exception):
    pass


class PlayerManager:
    def __init__(
        self,
        app: Client,
        user: Client | None,
        config: Settings,
        downloader: Downloader,
    ) -> None:
        self.app = app
        self.user = user
        self.config = config
        self.downloader = downloader
        self.call: PyTgCalls | None = None
        self.queues = QueueManager(config.QUEUE_LIMIT)
        self.known_chats: set[int] = set()

        self._active: set[int] = set()
        self._paused: set[int] = set()
        self._muted: set[int] = set()
        self._volumes: dict[int, int] = {}
        self._loop: set[int] = set()
        self._switch_until: dict[int, float] = {}
        self._now_msg: dict[int, int] = {}
        self._now_is_photo: dict[int, bool] = {}
        self._leave_tasks: dict[int, asyncio.Task] = {}
        self._progress_task: asyncio.Task | None = None
        self._http: aiohttp.ClientSession | None = None
        self._stop_flag = False
        self._songs_played = 0
        self._start_time = time.monotonic()

    @property
    def enabled(self) -> bool:
        return self.call is not None

    def attach(self, call: PyTgCalls) -> None:
        self.call = call

    def record_chat(self, chat_id: int) -> None:
        self.known_chats.add(chat_id)

    def is_active(self, chat_id: int) -> bool:
        return chat_id in self._active

    def is_paused(self, chat_id: int) -> bool:
        return chat_id in self._paused

    def is_muted(self, chat_id: int) -> bool:
        return chat_id in self._muted

    def is_looping(self, chat_id: int) -> bool:
        return chat_id in self._loop

    def volume(self, chat_id: int) -> int:
        return self._volumes.get(chat_id, self.config.DEFAULT_VOLUME)

    def songs_played(self) -> int:
        return self._songs_played

    def uptime(self) -> float:
        return time.monotonic() - self._start_time

    def active_groups(self) -> list[int]:
        return list(self._active)

    async def start(self) -> None:
        if self.call is None:
            return

        @self.call.on_update(fl.stream_end())
        async def _stream_end_handler(_client: PyTgCalls, update: StreamEnded) -> None:
            try:
                await self._handle_stream_end(update.chat_id)
            except Exception:
                logger.exception("Stream end handler failed in chat %s", update.chat_id)

        @self.call.on_update(fl.chat_update(ChatUpdate.Status.LEFT_CALL))
        async def _chat_update_handler(_client: PyTgCalls, update: ChatUpdate) -> None:
            try:
                await self._handle_left(update.chat_id)
            except Exception:
                logger.exception("Chat update handler failed in chat %s", update.chat_id)

        self._progress_task = asyncio.create_task(self._progress_loop())

    async def has_active_voice_chat(self, chat_id: int) -> bool:
        if self.call is None:
            return False
        try:
            input_call = await self.call._app.get_input_call(chat_id)
            return input_call is not None
        except Exception:
            return False

    async def join(self, chat_id: int) -> bool:
        self._require_enabled()
        async with self.queues.lock(chat_id):
            if self.is_active(chat_id):
                return False
            if not await self.has_active_voice_chat(chat_id):
                raise VoiceChatNotFound()
            self._active.add(chat_id)
            logger.info("Joined voice chat (idle) in chat %s", chat_id)
            return True

    async def leave(self, chat_id: int, announce: bool = True) -> bool:
        self._require_enabled()
        async with self.queues.lock(chat_id):
            if not self.is_active(chat_id):
                return False
            await self._leave(chat_id, announce)
            return True

    async def enqueue_and_play(
        self,
        chat_id: int,
        track: Track,
        video: bool = False,
    ) -> tuple[str, int | None]:
        self._require_enabled()
        async with self.queues.lock(chat_id):
            if self.is_active(chat_id) and self.queues.current(chat_id) is not None:
                position = self.queues.add(chat_id, track)
                if position is None:
                    return "full", None
                logger.info("Queued in chat %s: %s (position %s)", chat_id, track.title, position)
                return "queued", position
            try:
                await self._play_now(chat_id, track, announce=True, video=video)
                return "playing", None
            except TrackPlaybackError as exc:
                await self._recover_after_failure(chat_id)
                raise exc
            except VoiceChatNotFound:
                raise

    async def play_next(self, chat_id: int) -> tuple[str, Track | None]:
        self._require_enabled()
        assert self.call is not None
        async with self.queues.lock(chat_id):
            if not self.is_active(chat_id) or self.queues.current(chat_id) is None:
                return "not_playing", None
            await self._cleanup_track(chat_id)
            next_track = self.queues.pop(chat_id)
            if next_track is not None:
                try:
                    await self._play_now(chat_id, next_track)
                except TrackPlaybackError:
                    await self._recover_after_failure(chat_id)
                    return "finished", None
                except VoiceChatNotFound:
                    await self._idle_after_queue(chat_id)
                    return "finished", None
                return "playing", next_track
            self.queues.set_current(chat_id, None)
            try:
                await self.call.pause(chat_id)
            except Exception:
                pass
            await self._idle_after_queue(chat_id)
            return "finished", None

    async def stop(self, chat_id: int, announce: bool = True) -> bool:
        self._require_enabled()
        assert self.call is not None
        async with self.queues.lock(chat_id):
            if not self.is_active(chat_id):
                return False
            await self._delete_now_message(chat_id)
            await self._cleanup_track(chat_id)
            self.queues.clear(chat_id)
            self.queues.set_current(chat_id, None)
            self._paused.discard(chat_id)
            self._muted.discard(chat_id)
            try:
                await self.call.pause(chat_id)
            except Exception:
                pass
            if self.config.AUTO_LEAVE:
                await self._schedule_auto_leave(chat_id, "⏹ Playback stopped.")
            elif announce:
                await self._safe_call(
                    self.app.send_message,
                    chat_id,
                    "⏹ Playback stopped.",
                )
            return True

    async def pause(self, chat_id: int) -> bool:
        self._require_enabled()
        assert self.call is not None
        async with self.queues.lock(chat_id):
            if not self.is_active(chat_id) or self.queues.current(chat_id) is None:
                return False
            if chat_id in self._paused:
                return False
            try:
                await self.call.pause(chat_id)
            except Exception:
                return False
            self._paused.add(chat_id)
            await self._refresh_now(chat_id)
            return True

    async def resume(self, chat_id: int) -> bool:
        self._require_enabled()
        assert self.call is not None
        async with self.queues.lock(chat_id):
            if chat_id not in self._paused:
                return False
            try:
                await self.call.resume(chat_id)
            except Exception:
                return False
            self._paused.discard(chat_id)
            await self._refresh_now(chat_id)
            return True

    async def mute(self, chat_id: int) -> bool:
        self._require_enabled()
        assert self.call is not None
        async with self.queues.lock(chat_id):
            if not self.is_active(chat_id) or self.queues.current(chat_id) is None:
                return False
            if chat_id in self._muted:
                return False
            try:
                await self.call.mute(chat_id)
            except Exception:
                return False
            self._muted.add(chat_id)
            return True

    async def unmute(self, chat_id: int) -> bool:
        self._require_enabled()
        assert self.call is not None
        async with self.queues.lock(chat_id):
            if chat_id not in self._muted:
                return False
            try:
                await self.call.unmute(chat_id)
            except Exception:
                return False
            self._muted.discard(chat_id)
            return True

    async def set_volume(self, chat_id: int, volume: int) -> bool:
        self._require_enabled()
        assert self.call is not None
        if not 1 <= volume <= 100:
            return False
        async with self.queues.lock(chat_id):
            if not self.is_active(chat_id):
                return False
            try:
                await self.call.change_volume_call(chat_id, volume)
            except Exception:
                return False
            self._volumes[chat_id] = volume
            await self._refresh_now(chat_id)
            return True

    def toggle_loop(self, chat_id: int) -> bool:
        if chat_id in self._loop:
            self._loop.discard(chat_id)
            return False
        self._loop.add(chat_id)
        return True

    async def now_playing(self, chat_id: int) -> tuple[Track | None, int | None]:
        track = self.queues.current(chat_id)
        elapsed = None
        if track is not None and self.is_active(chat_id) and self.call is not None:
            try:
                elapsed = await self.call.time(chat_id)
            except Exception:
                elapsed = None
        return track, elapsed

    def _require_enabled(self) -> None:
        if self.call is None:
            raise VoiceDisabledError()

    async def _play_now(
        self,
        chat_id: int,
        track: Track,
        announce: bool = True,
        video: bool = False,
    ) -> None:
        self._require_enabled()
        assert self.call is not None
        self._switch_until[chat_id] = time.monotonic() + 3.0
        self.queues.set_current(chat_id, track)
        self._paused.discard(chat_id)
        self._muted.discard(chat_id)
        media = self._build_media(track, video=video)
        try:
            await self.call.play(chat_id, media, GroupCallConfig(auto_start=False))
        except NoActiveGroupCall as exc:
            self._active.discard(chat_id)
            raise VoiceChatNotFound() from exc
        except Exception as exc:
            await self._cleanup_track(chat_id)
            self.queues.set_current(chat_id, None)
            raise TrackPlaybackError(track.title) from exc
        self._active.add(chat_id)
        self._songs_played += 1
        volume = self._volumes.get(chat_id, self.config.DEFAULT_VOLUME)
        try:
            await self.call.change_volume_call(chat_id, volume)
        except Exception:
            pass
        logger.info("Now playing in chat %s: %s", chat_id, track.title)
        if announce:
            await self._send_now_playing(chat_id)

    async def _recover_after_failure(self, chat_id: int) -> None:
        attempts = 0
        while attempts < 5:
            next_track = self.queues.pop(chat_id)
            if next_track is None:
                await self._idle_after_queue(chat_id)
                return
            try:
                await self._play_now(chat_id, next_track)
                return
            except TrackPlaybackError:
                self.queues.set_current(chat_id, None)
                await cleanup.delete_file(next_track.file_path)
                attempts += 1
            except VoiceChatNotFound:
                await self._idle_after_queue(chat_id)
                return
        await self._idle_after_queue(chat_id)

    async def _handle_stream_end(self, chat_id: int) -> None:
        if not self.is_active(chat_id):
            return
        if time.monotonic() < self._switch_until.get(chat_id, 0.0):
            return
        async with self.queues.lock(chat_id):
            if not self.is_active(chat_id):
                return
            current = self.queues.current(chat_id)
            if current is None:
                return
            logger.info("Playback finished in chat %s: %s", chat_id, current.title)
            await self._cleanup_track(chat_id)
            next_track = self.queues.pop(chat_id)
            if next_track is None and chat_id in self._loop:
                next_track = current
            if next_track is not None:
                try:
                    await self._play_now(chat_id, next_track)
                except TrackPlaybackError:
                    await self._recover_after_failure(chat_id)
                except VoiceChatNotFound:
                    await self._idle_after_queue(chat_id)
            else:
                self.queues.set_current(chat_id, None)
                await self._idle_after_queue(chat_id)

    async def _handle_left(self, chat_id: int) -> None:
        async with self.queues.lock(chat_id):
            task = self._leave_tasks.pop(chat_id, None)
            if task and not task.done():
                task.cancel()
            await self._delete_now_message(chat_id)
            await self._cleanup_track(chat_id)
            self.queues.clear(chat_id)
            self.queues.set_current(chat_id, None)
            self._paused.discard(chat_id)
            self._muted.discard(chat_id)
            self._active.discard(chat_id)
            logger.info("Voice chat left/closed in chat %s", chat_id)

    async def _idle_after_queue(self, chat_id: int) -> None:
        await self._delete_now_message(chat_id)
        if self.config.AUTO_LEAVE:
            await self._schedule_auto_leave(chat_id)
        else:
            if self.call is not None:
                try:
                    await self.call.pause(chat_id)
                except Exception:
                    pass
            await self._safe_call(self.app.send_message, chat_id, "⏹ Queue finished.")

    async def _schedule_auto_leave(self, chat_id: int, message_text: str | None = None) -> None:
        task = self._leave_tasks.get(chat_id)
        if task and not task.done():
            task.cancel()
        delay = self.config.AUTO_LEAVE_DELAY
        if message_text:
            await self._safe_call(self.app.send_message, chat_id, message_text)
        else:
            await self._safe_call(
                self.app.send_message,
                chat_id,
                f"⏹ Queue finished. Leaving the voice chat in {delay}s...",
            )
        task = asyncio.create_task(self._auto_leave_after(chat_id, delay))
        self._leave_tasks[chat_id] = task

    async def _auto_leave_after(self, chat_id: int, delay: int) -> None:
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return
        async with self.queues.lock(chat_id):
            if self.queues.current(chat_id) is None and self.queues.is_empty(chat_id):
                await self._leave(chat_id, announce=False)

    async def _leave(self, chat_id: int, announce: bool = True) -> None:
        task = self._leave_tasks.pop(chat_id, None)
        if task and not task.done():
            task.cancel()
        await self._delete_now_message(chat_id)
        await self._cleanup_track(chat_id)
        self.queues.clear(chat_id)
        self.queues.set_current(chat_id, None)
        self._paused.discard(chat_id)
        self._muted.discard(chat_id)
        self._volumes.pop(chat_id, None)
        self._active.discard(chat_id)
        if self.call is not None:
            try:
                await self.call.leave_call(chat_id)
            except Exception:
                pass
        logger.info("Left voice chat %s", chat_id)
        if announce:
            await self._safe_call(self.app.send_message, chat_id, "👋 Left the voice chat.")

    async def _cleanup_track(self, chat_id: int) -> None:
        track = self.queues.current(chat_id)
        if track is not None and track.file_path:
            await cleanup.delete_file(track.file_path)

    def _build_media(self, track: Track, video: bool = False) -> MediaStream:
        source = track.file_path or track.stream_url or track.url
        if video:
            return MediaStream(source, AudioQuality.HIGH, VideoQuality.HD_720p)
        return MediaStream(
            source,
            AudioQuality.HIGH,
            VideoQuality.HD_720p,
            video_flags=MediaStream.Flags.IGNORE,
        )

    async def _refresh_now(self, chat_id: int) -> None:
        track = self.queues.current(chat_id)
        message_id = self._now_msg.get(chat_id)
        if track is None:
            await self._delete_now_message(chat_id)
            return
        elapsed = None
        if self.is_active(chat_id) and self.call is not None:
            try:
                elapsed = await self.call.time(chat_id)
            except Exception:
                elapsed = None
        text = format_now_playing(
            track,
            elapsed=elapsed,
            paused=self.is_paused(chat_id),
            volume=self.volume(chat_id),
        )
        if message_id:
            await self._edit_now_message(chat_id, text)
        else:
            await self._send_now_playing(chat_id)

    async def _send_now_playing(self, chat_id: int) -> None:
        await self._delete_now_message(chat_id)
        track = self.queues.current(chat_id)
        if track is None:
            return
        text = format_now_playing(
            track,
            elapsed=0,
            paused=self.is_paused(chat_id),
            volume=self.volume(chat_id),
        )
        keyboard = player_keyboard(paused=self.is_paused(chat_id))
        photo = await self._download_thumbnail(chat_id, track.thumbnail)
        message = None
        if photo:
            message = await self._safe_call(
                self.app.send_photo,
                chat_id,
                photo,
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
            if message is not None:
                self._now_is_photo[chat_id] = True
        if message is None:
            message = await self._safe_call(
                self.app.send_message,
                chat_id,
                text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=keyboard,
            )
            if message is not None:
                self._now_is_photo[chat_id] = False
        if message is not None:
            self._now_msg[chat_id] = message.id
        if photo:
            await cleanup.delete_file(photo)

    async def _edit_now_message(self, chat_id: int, text: str) -> None:
        message_id = self._now_msg.get(chat_id)
        if not message_id:
            return
        keyboard = player_keyboard(paused=self.is_paused(chat_id))
        if self._now_is_photo.get(chat_id):
            await self._safe_call(
                self.app.edit_message_caption,
                chat_id,
                message_id,
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        else:
            await self._safe_call(
                self.app.edit_message_text,
                chat_id,
                message_id,
                text=text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=keyboard,
            )

    async def _delete_now_message(self, chat_id: int) -> None:
        message_id = self._now_msg.pop(chat_id, None)
        self._now_is_photo.pop(chat_id, None)
        if message_id:
            await self._safe_call(self.app.delete_messages, chat_id, message_id)

    async def _download_thumbnail(self, chat_id: int, url: str | None) -> str | None:
        if not url:
            return None
        if self._http is None:
            self._http = aiohttp.ClientSession()
        path = self.config.DOWNLOAD_PATH / f"thumb_{chat_id}_{uuid.uuid4().hex}.jpg"
        try:
            async with self._http.get(url, timeout=aiohttp.ClientTimeout(total=8)) as response:
                if response.status != 200:
                    return None
                data = await response.read()
                if len(data) < 100:
                    return None
                path.write_bytes(data)
                return str(path)
        except Exception:
            return None

    async def _progress_loop(self) -> None:
        while not self._stop_flag:
            await asyncio.sleep(self.config.PROGRESS_INTERVAL)
            for chat_id in list(self._now_msg):
                try:
                    await self._refresh_now(chat_id)
                except Exception:
                    pass

    async def _safe_call(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception:
            return None

    async def shutdown(self) -> None:
        self._stop_flag = True
        if self._progress_task is not None and not self._progress_task.done():
            self._progress_task.cancel()
        for chat_id in list(self._active):
            try:
                async with self.queues.lock(chat_id):
                    await self._leave(chat_id, announce=False)
            except Exception:
                pass
        if self._http is not None:
            await self._http.close()
            self._http = None
        await cleanup.cleanup_downloads(self.config.DOWNLOAD_PATH)
