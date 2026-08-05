"""Local filesystem storage: media under ``MEDIA_ROOT`` served at ``/media/*``."""

from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings


def normalize_key(path: str | Path) -> str:
    """Normalize any stored path to a bucket-style relative key.

    Accepts ``projects/1/final.mp4``, ``/media/projects/1/final.mp4`` and
    absolute paths under ``MEDIA_ROOT`` and always returns
    ``projects/1/final.mp4``.
    """
    raw = str(path).replace("\\", "/")
    settings = get_settings()
    root = str(Path(settings.MEDIA_ROOT).resolve()).replace("\\", "/")
    if raw.startswith(root + "/"):
        raw = raw[len(root) + 1 :]
    raw = raw.lstrip("/")
    if raw.startswith("media/"):
        raw = raw[len("media/") :]
    return raw


class LocalStorage:
    """Stores/reads media on the local disk under ``MEDIA_ROOT``."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or get_settings().MEDIA_ROOT).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    # -- addressing -----------------------------------------------------
    def abspath(self, path: str | Path) -> Path:
        """Absolute filesystem path for a stored key."""
        return self.root / normalize_key(path)

    def url(self, path: str | Path) -> str:
        """Public URL path served by the backend's static ``/media`` mount."""
        return "/media/" + normalize_key(path)

    # -- bytes ----------------------------------------------------------
    def read_bytes(self, path: str | Path) -> bytes:
        return self.abspath(path).read_bytes()

    def write_bytes(self, path: str | Path, data: bytes) -> Path:
        dest = self.abspath(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return dest

    def exists(self, path: str | Path) -> bool:
        return self.abspath(path).exists()
