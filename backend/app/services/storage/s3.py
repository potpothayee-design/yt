"""S3-compatible storage (AWS S3, Cloudflare R2) with local-mirror fallback.

Cloudflare R2: set ``S3_ENDPOINT_URL=https://<accountid>.r2.cloudflarestorage.com``
and ``S3_REGION=auto``. Point ``S3_PUBLIC_BASE_URL`` at your public bucket /
CDN domain so ``url()`` returns directly-cacheable links.

Because the render pipeline always writes artifacts to the local
``MEDIA_ROOT`` work directory first (and no sync daemon runs in-process),
``read_bytes()`` falls back to that local copy when the object is not (yet)
in the bucket. ``url()`` still returns the object/CDN address, which suits
deployments that mount the same CDN over a synced bucket or that serve media
through the backend's ``/media`` route via a reverse proxy.
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.services.storage.local import normalize_key


class S3Storage:
    """S3/R2 object storage backend implementing the storage interface."""

    def __init__(
        self,
        bucket: str,
        region: str = "auto",
        endpoint_url: str = "",
        access_key_id: str = "",
        secret_access_key: str = "",
        public_base_url: str = "",
    ) -> None:
        if not bucket:
            raise ValueError("S3_BUCKET must be set when STORAGE_BACKEND=s3")
        import boto3  # imported lazily — only needed for the s3 backend

        self.bucket = bucket
        self.region = region
        self.public_base_url = public_base_url.rstrip("/")
        endpoint = endpoint_url or None
        self._client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint,
            aws_access_key_id=access_key_id or None,
            aws_secret_access_key=secret_access_key or None,
        )

    @classmethod
    def from_settings(cls) -> S3Storage:
        settings = get_settings()
        return cls(
            bucket=settings.S3_BUCKET,
            region=settings.S3_REGION,
            endpoint_url=settings.S3_ENDPOINT_URL,
            access_key_id=settings.S3_ACCESS_KEY_ID,
            secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            public_base_url=settings.S3_PUBLIC_BASE_URL,
        )

    # -- addressing -----------------------------------------------------
    def url(self, path: str | Path) -> str:
        key = normalize_key(path)
        if self.public_base_url:
            return f"{self.public_base_url}/{key}"
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"

    def abspath(self, path: str | Path) -> Path:
        raise RuntimeError(
            "S3/R2 storage has no local filesystem path; use read_bytes() "
            "(uploads call LocalStorage.abspath only for the local backend)."
        )

    # -- bytes ----------------------------------------------------------
    def read_bytes(self, path: str | Path) -> bytes:
        key = normalize_key(path)
        try:
            obj = self._client.get_object(Bucket=self.bucket, Key=key)
            return obj["Body"].read()
        except Exception:
            # Graceful fallback: the pipeline renders to the local media root;
            # serve the local copy when the object has not been synced yet.
            local = Path(get_settings().MEDIA_ROOT) / key
            if local.exists():
                return local.read_bytes()
            raise

    def write_bytes(self, path: str | Path, data: bytes) -> str:
        import mimetypes

        key = normalize_key(path)
        content_type = (
            mimetypes.guess_type(key)[0] or "application/octet-stream"
        )
        self._client.put_object(
            Bucket=self.bucket, Key=key, Body=data, ContentType=content_type
        )
        return key

    def exists(self, path: str | Path) -> bool:
        key = normalize_key(path)
        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            local = Path(get_settings().MEDIA_ROOT) / key
            return local.exists()
