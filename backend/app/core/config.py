"""Central application configuration.

All settings are read from environment variables (or a local ``.env`` file).
Secrets are NEVER hardcoded — see ``.env.example`` for the full list.
"""

from __future__ import annotations

import secrets
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo/backend


class Settings(BaseSettings):
    """Application settings resolved from the environment."""

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env", BASE_DIR.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Core ---
    APP_NAME: str = "AI Kids Video Studio"
    APP_VERSION: str = "1.0.0"
    # In dev we auto-generate an ephemeral key if none is provided, but we log
    # a loud warning. Production MUST set SECRET_KEY explicitly.
    SECRET_KEY: str = ""
    # Passwordless one-click dev login ("Continue as local dev" button).
    # None = auto: enabled ONLY in ephemeral dev mode (no SECRET_KEY set),
    # i.e. never in production unless ALLOW_DEV_LOGIN=true is set explicitly.
    ALLOW_DEV_LOGIN: bool | None = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12
    FIRST_USER_IS_ADMIN: bool = True

    # --- Database ---
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'storage' / 'studio.db'}"

    # --- Storage ---
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    MEDIA_ROOT: str = str(BASE_DIR / "storage" / "media")
    S3_BUCKET: str = ""
    S3_REGION: str = "auto"
    S3_ENDPOINT_URL: str = ""            # set for Cloudflare R2
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_PUBLIC_BASE_URL: str = ""         # CDN base URL for public object access

    # --- AI providers (keys optional — local providers need none) ---
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    STABILITY_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    GOOGLE_TTS_API_KEY: str = ""
    PIKA_API_KEY: str = ""
    RUNWAY_API_KEY: str = ""

    TEXT_PROVIDER: str = "local"
    IMAGE_PROVIDER: str = "local"
    VIDEO_PROVIDER: str = "local"
    VOICE_PROVIDER: str = "local"
    MUSIC_PROVIDER: str = "local"

    # --- YouTube ---
    YOUTUBE_CLIENT_ID: str = ""
    YOUTUBE_CLIENT_SECRET: str = ""
    YOUTUBE_REDIRECT_URI: str = "http://localhost:8000/api/v1/youtube/callback"
    YOUTUBE_SCOPES: str = (
        "https://www.googleapis.com/auth/youtube.upload,"
        "https://www.googleapis.com/auth/youtube"
    )

    # --- GitHub Actions integration ---
    GITHUB_DISPATCH_TOKEN: str = ""
    GITHUB_REPOSITORY: str = ""
    JOB_CALLBACK_SECRET: str = ""
    # Public URL of this API, used for GitHub Actions callbacks
    PUBLIC_API_URL: str = "http://localhost:8000"

    # --- Server ---
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    CORS_ORIGINS: str = "*"

    # --- Rendering defaults ---
    RENDER_WIDTH: int = 1280
    RENDER_HEIGHT: int = 720
    RENDER_FPS: int = 24
    MAX_PARALLEL_JOBS: int = 2

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def youtube_scope_list(self) -> list[str]:
        return [s.strip() for s in self.YOUTUBE_SCOPES.split(",") if s.strip()]

    @property
    def effective_secret_key(self) -> str:
        return self.SECRET_KEY or "dev-insecure-" + self.APP_NAME

    def ensure_secret_key(self) -> None:
        """Generate an ephemeral development key when none is configured."""
        if not self.SECRET_KEY:
            self.SECRET_KEY = "dev-" + secrets.token_hex(32)

    @property
    def dev_login_enabled(self) -> bool:
        """Passwordless dev login: explicit setting wins, else dev-mode only."""
        if self.ALLOW_DEV_LOGIN is not None:
            return self.ALLOW_DEV_LOGIN
        return self.SECRET_KEY.startswith("dev-")

    @property
    def sqlalchemy_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgres://"):  # some platforms provide this scheme
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        return url

    def provider_key(self, provider: str) -> str:
        """Return the configured API key for a provider name (or '')."""
        return {
            "openai": self.OPENAI_API_KEY,
            "anthropic": self.ANTHROPIC_API_KEY,
            "stability": self.STABILITY_API_KEY,
            "elevenlabs": self.ELEVENLABS_API_KEY,
            "google-tts": self.GOOGLE_TTS_API_KEY,
            "pika": self.PIKA_API_KEY,
            "runway": self.RUNWAY_API_KEY,
        }.get(provider, "")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_secret_key()
    Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
    if settings.STORAGE_BACKEND == "local":
        Path(settings.DATABASE_URL.replace("sqlite:///", "")).parent.mkdir(
            parents=True, exist_ok=True
        ) if settings.DATABASE_URL.startswith("sqlite") else None
    return settings
