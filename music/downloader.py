from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

import yt_dlp

from music.queue import Track

URL_RE = re.compile(r"^https?://", re.IGNORECASE)


class AudioSourceError(Exception):
    pass


class Downloader:
    def __init__(self, download_path: Path) -> None:
        self.download_path = download_path
        self.download_path.mkdir(parents=True, exist_ok=True)

    def _opts(self) -> dict[str, Any]:
        return {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "skip_download": True,
            "format": "bestaudio/best",
        }

    def is_url(self, text: str) -> bool:
        return bool(URL_RE.match(text))

    def _extract(self, query: str) -> dict[str, Any] | None:
        try:
            with yt_dlp.YoutubeDL(self._opts()) as ydl:
                if self.is_url(query):
                    data = ydl.extract_info(query, download=False)
                else:
                    data = ydl.extract_info(f"ytsearch1:{query}", download=False)
        except Exception:
            return None
        if not data:
            return None
        if data.get("entries"):
            entry = data["entries"][0]
            data = entry or data
        if not data.get("title"):
            return None
        return data

    async def search(
        self,
        query: str,
        requester_id: int | None,
        requester_name: str | None,
    ) -> Track:
        loop = asyncio.get_running_loop()
        try:
            info = await asyncio.wait_for(
                loop.run_in_executor(None, self._extract, query),
                timeout=30,
            )
        except TimeoutError as exc:
            raise AudioSourceError("Search timed out. Please try again.") from exc
        if info is None:
            raise AudioSourceError("No results found for the requested song.")
        return self._track_from_info(info, requester_id, requester_name)

    def _track_from_info(
        self,
        info: dict[str, Any],
        requester_id: int | None,
        requester_name: str | None,
    ) -> Track:
        webpage = info.get("webpage_url") or info.get("original_url") or ""
        is_youtube = "youtube" in webpage.lower()
        stream_url = None
        if webpage and not is_youtube:
            stream_url = info.get("url") or webpage
        return Track(
            title=str(info.get("title") or "Unknown title"),
            url=webpage,
            duration=int(info.get("duration") or 0),
            thumbnail=info.get("thumbnail"),
            uploader=info.get("channel") or info.get("uploader"),
            requester_id=requester_id,
            requester_name=requester_name,
            source="youtube" if is_youtube else "direct",
            stream_url=stream_url,
        )

    async def from_url(
        self,
        url: str,
        requester_id: int | None,
        requester_name: str | None,
    ) -> Track:
        loop = asyncio.get_running_loop()
        try:
            info = await asyncio.wait_for(
                loop.run_in_executor(None, self._extract, url),
                timeout=30,
            )
        except TimeoutError:
            info = None
        if info is not None:
            return self._track_from_info(info, requester_id, requester_name)
        return Track(
            title=url,
            url=url,
            stream_url=url,
            duration=0,
            requester_id=requester_id,
            requester_name=requester_name,
            source="direct",
        )

    async def telegram_media_track(
        self,
        user_client: Any,
        message: Any,
        requester_id: int | None,
        requester_name: str | None,
    ) -> Track | None:
        media = message.audio or message.voice
        if message.document:
            mime = message.document.mime_type or ""
            if not mime.startswith("audio/"):
                return None
            media = message.document
        if media is None:
            return None

        extension = "ogg"
        if getattr(media, "file_name", None):
            extension = Path(media.file_name).suffix.lstrip(".") or extension
        elif getattr(media, "mime_type", None) and "/" in media.mime_type:
            extension = media.mime_type.split("/", 1)[1] or extension

        name = f"group_{message.chat.id}_song_{abs(hash(message.id))}.{extension}"
        target = self.download_path / name
        path = await asyncio.to_thread(
            user_client.download_media,
            message,
            file_name=str(target),
        )
        if not path:
            raise AudioSourceError("Failed to download the audio file.")

        title = f"{media.performer} - {media.title}" if getattr(media, "performer", None) else None
        title = (
            title
            or getattr(media, "title", None)
            or getattr(media, "file_name", None)
            or "Telegram audio"
        )
        return Track(
            title=title,
            duration=int(getattr(media, "duration", 0) or 0),
            thumbnail=None,
            uploader=media.performer if getattr(media, "performer", None) else None,
            requester_id=requester_id,
            requester_name=requester_name,
            source="telegram",
            file_path=str(path),
        )
