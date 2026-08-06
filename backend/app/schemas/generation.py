from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AGE_RANGES = ("3-6", "7-9", "10-13")
ASPECT_RATIOS = ("16:9", "9:16", "1:1")


class GenerationParams(BaseModel):
    """Parameters chosen on the Generator page."""

    topic: str = Field(min_length=2, max_length=200)
    target_age: Literal["3-6", "7-9", "10-13"] = "3-6"
    length_seconds: int = Field(default=30, ge=15, le=600)
    style: str = Field(default="3D Cartoon", max_length=80)
    animation_type: str = Field(default="playful", max_length=60)
    voice: str = Field(default="female", max_length=40)
    language: str = Field(default="en", max_length=10)
    music_mood: str = Field(default="cheerful", max_length=40)
    aspect_ratio: Literal["16:9", "9:16", "1:1"] = "16:9"
    quality: Literal["draft", "standard", "high"] = "standard"
    # Narration playback speed — 1.25 fits ~25% more content per minute while
    # staying perfectly synced with the karaoke captions.
    voice_speed: float = Field(default=1.0, ge=0.75, le=1.5)


class ProjectCreateRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=200)
    params: GenerationParams | None = None


class ProjectUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    script: dict | None = None
    video_metadata: dict | None = None


class RegenerateRequest(BaseModel):
    """Partial regeneration targets exposed on the Preview page."""

    target: Literal["scene", "thumbnail", "voice", "music", "video"]
    scene_index: int | None = Field(default=None, ge=0)
    instruction: str | None = Field(default=None, max_length=500)


class ScriptUpdateRequest(BaseModel):
    script: dict


class UploadRequest(BaseModel):
    """Explicit user approval — uploads require ``confirm=True``."""

    confirm: bool = False
    privacy: Literal["private", "unlisted", "public"] = "private"
    scheduled_at: str | None = None  # RFC 3339, future timestamp
    made_for_kids: bool = True
    title: str | None = Field(default=None, max_length=100)
    description: str | None = None
    tags: list[str] | None = None
