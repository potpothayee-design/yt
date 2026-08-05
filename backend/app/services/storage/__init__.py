"""Storage backends for generated media.

The pipeline itself is persistence-agnostic and always renders into a
filesystem work directory (``MEDIA_ROOT/projects/<id>`` in local mode). The
storage abstraction is what the API layer uses to *address*, *read* and
*expose* those artifacts:

* :class:`LocalStorage` — media lives on disk under ``MEDIA_ROOT`` and is
  served by FastAPI's static mount at ``/media/*`` (default, dev + compose).
* :class:`S3Storage` — AWS S3 or an S3-compatible bucket such as Cloudflare
  R2 (set ``S3_ENDPOINT_URL``). ``url()`` prefers the configured CDN/public
  base URL. When an artifact was rendered locally (the pipeline always
  writes to ``MEDIA_ROOT``) and has not been synced to the bucket,
  ``read_bytes()`` transparently falls back to the local copy, so a
  bucket-backed deployment works even before a sync job runs.

Select the backend with ``STORAGE_BACKEND=local|s3``.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.services.storage.local import LocalStorage
from app.services.storage.s3 import S3Storage

__all__ = ["LocalStorage", "S3Storage", "StorageBackend", "get_storage"]

# Common structural type — anything with these methods is a storage backend.
StorageBackend = LocalStorage | S3Storage


@lru_cache
def get_storage() -> StorageBackend:
    """Return the configured storage backend (process-wide singleton)."""
    settings = get_settings()
    if settings.STORAGE_BACKEND == "s3":
        return S3Storage.from_settings()
    return LocalStorage()
