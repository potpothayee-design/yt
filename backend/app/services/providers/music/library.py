"""Royalty-free library provider.

Picks a user-supplied licensed/royalty-free track from a configured folder
(``options.library_dir`` or ``MUSIC_LIBRARY_DIR`` env var). Files can be
organized per mood subfolder (``cheerful/``, ``calm/`` ...) or tagged by
filename containing the mood name. Compliance rule: only tracks the user has
permission to use should be placed in the library.
"""

from __future__ import annotations

import os
import random
from pathlib import Path

from app.services.providers.base import MusicResult, ProviderError
from app.services.rendering.ffmpeg_utils import run_ffmpeg

_EXTS = {".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac"}


class LibraryMusicProvider:
    name = "library"
    label = "Royalty-free Library"
    requires_key = False

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.options = options or {}
        self.library_dir = Path(
            self.options.get("library_dir")
            or os.environ.get("MUSIC_LIBRARY_DIR", "")
        )

    def _candidates(self, mood: str) -> list[Path]:
        if not self.library_dir or not self.library_dir.exists():
            return []
        mood = mood.lower()
        hits = [p for p in self.library_dir.rglob("*")
                if p.suffix.lower() in _EXTS and mood in str(p).lower()]
        if not hits:
            hits = [p for p in self.library_dir.rglob("*") if p.suffix.lower() in _EXTS]
        return hits

    def generate_track(self, mood: str, duration: float, out_path: str) -> MusicResult:
        candidates = self._candidates(mood)
        if not candidates:
            raise ProviderError(
                self.name,
                "no library tracks found. Set MUSIC_LIBRARY_DIR and add your "
                "licensed/royalty-free music files (see docs/PROVIDERS.md).",
            )
        chosen = random.choice(candidates)
        # loop/trim to duration with a gentle fade, normalized quiet bed
        run_ffmpeg([
            "-stream_loop", "-1", "-i", str(chosen),
            "-t", f"{duration:.3f}",
            "-af", f"volume=0.35,afade=t=in:st=0:d=1.2,afade=t=out:st={max(0.0, duration - 1.8):.2f}:d=1.8",
            "-ac", "1", "-ar", "22050", "-y", out_path,
        ], timeout=300)
        return MusicResult(path=out_path, duration=duration,
                           credits=f"Library track: {chosen.name} (user-licensed)")
