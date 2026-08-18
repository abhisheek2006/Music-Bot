from __future__ import annotations

import shutil
import subprocess


def ffmpeg_version() -> str | None:
    executable = shutil.which("ffmpeg")
    if not executable:
        return None
    try:
        result = subprocess.run(
            [executable, "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    first_line = result.stdout.splitlines()[0] if result.stdout else ""
    return first_line or None


def is_ffmpeg_available() -> bool:
    return ffmpeg_version() is not None
