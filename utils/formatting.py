from __future__ import annotations

import html
from collections.abc import Iterable

from music.queue import Track


def esc(text: object) -> str:
    return html.escape(str(text), quote=False)


def format_duration(seconds: int | float | None) -> str:
    if seconds is None:
        return "Live"
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def mention(user_id: int, name: str | None = None) -> str:
    label = esc(name) if name else f"user {user_id}"
    return f'<a href="tg://user?id={user_id}">{label}</a>'


def requester_line(track: Track) -> str:
    if track.requester_id:
        return f"Requested by: {mention(track.requester_id, track.requester_name)}"
    return ""


def format_added_to_queue(track: Track, position: int) -> str:
    lines = [
        "🎵 <b>Added to Queue</b>",
        "",
        f"<b>Title:</b> {esc(track.title)}",
        f"<b>Artist:</b> {esc(track.uploader or 'Unknown')}",
        f"<b>Duration:</b> {format_duration(track.duration)}",
        f"<b>Position:</b> #{position}",
        "",
        requester_line(track),
    ]
    return "\n".join(line for line in lines if line)


def format_now_playing(
    track: Track,
    elapsed: int | None = None,
    paused: bool = False,
    volume: int | None = None,
) -> str:
    lines = [
        "🎧 <b>NOW PLAYING</b>",
        "",
        f"🎵 {esc(track.title)}",
        f"👤 {esc(track.uploader or 'Unknown')}",
        "",
        f"⏱ {format_duration(track.duration)}",
    ]
    if track.duration and elapsed is not None:
        lines.append(f"▶️ {format_duration(elapsed)} / {format_duration(track.duration)}")
    if paused:
        lines.append("⏸ <b>Paused</b>")
    if volume is not None:
        lines.append(f"🔊 Volume: {volume}%")
    lines.extend(["", requester_line(track)])
    return "\n".join(line for line in lines if line)


def format_song_info(track: Track) -> str:
    lines = [
        "🎵 <b>Song Info</b>",
        "",
        f"<b>Title:</b> {esc(track.title)}",
        f"<b>Artist:</b> {esc(track.uploader or 'Unknown')}",
        f"<b>Duration:</b> {format_duration(track.duration)}",
        "",
        requester_line(track),
    ]
    if track.url:
        lines.append("")
        lines.append(f'<a href="{esc(track.url)}">Open link</a>')
    return "\n".join(line for line in lines if line)


def format_queue(current: Track | None, tracks: Iterable[Track], limit: int) -> str:
    lines = ["🎶 <b>Music Queue</b>", ""]
    if current is not None:
        lines.append("▶️ <b>Now Playing:</b>")
        lines.append(f"   {esc(current.title)} — {esc(current.uploader or 'Unknown')}")
        lines.append("")
    items = list(tracks)
    if items:
        lines.append("Up Next:")
        for index, item in enumerate(items, start=1):
            if index > limit:
                lines.append(f"   ...and {len(items) - limit + 1} more")
                break
            lines.append(
                f"{index}. {esc(item.title)} — {esc(item.uploader or 'Unknown')}",
            )
        lines.append("")
    total = len(items) + (1 if current is not None else 0)
    lines.append(f"Total: {total} song{'s' if total != 1 else ''}")
    return "\n".join(lines)
