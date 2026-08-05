"""ffmpeg access layer.

Uses (in order): ``FFMPEG_BINARY`` env override, a system ``ffmpeg`` on PATH,
or the self-contained binary shipped with ``imageio-ffmpeg`` (installable via
pip — no OS packages needed, which keeps Docker images slim and the app
deployable anywhere).
"""

from __future__ import annotations

import functools
import os
import re
import shutil
import subprocess


@functools.lru_cache(maxsize=1)
def ffmpeg_bin() -> str:
    override = os.environ.get("FFMPEG_BINARY")
    if override and os.path.exists(override):
        return override
    system = shutil.which("ffmpeg")
    if system:
        return system
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def run_ffmpeg(args: list[str], timeout: int = 900) -> subprocess.CompletedProcess:
    """Run ffmpeg with -y, raising RuntimeError with stderr tail on failure."""
    cmd = [ffmpeg_bin(), "-hide_banner", "-y", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        tail = "\n".join((proc.stderr or "").splitlines()[-25:])
        raise RuntimeError(f"ffmpeg failed ({proc.returncode}): {tail}")
    return proc


_DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")


def probe_duration(path: str) -> float:
    """Return media duration in seconds by parsing ffmpeg's probe output."""
    proc = subprocess.run(
        [ffmpeg_bin(), "-hide_banner", "-i", path],
        capture_output=True, text=True, timeout=120,
    )
    match = _DURATION_RE.search((proc.stderr or "") + (proc.stdout or ""))
    if not match:
        return 0.0
    h, m, s = int(match.group(1)), int(match.group(2)), float(match.group(3))
    return h * 3600 + m * 60 + s


def audio_duration(path: str) -> float:
    return probe_duration(path)


@functools.lru_cache(maxsize=1)
def available_filters() -> set[str]:
    proc = subprocess.run(
        [ffmpeg_bin(), "-hide_banner", "-filters"],
        capture_output=True, text=True, timeout=120,
    )
    names = set()
    for line in (proc.stdout or "").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].count(".") <= 1:
            names.add(parts[1])
    return names


def ffmpeg_version() -> str:
    proc = subprocess.run(
        [ffmpeg_bin(), "-version"], capture_output=True, text=True, timeout=60
    )
    return (proc.stdout or "").splitlines()[0] if proc.stdout else "unknown"
