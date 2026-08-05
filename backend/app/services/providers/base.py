"""Provider interfaces and shared data types.

A provider never writes to the database — it transforms inputs into files or
text and returns result objects. The pipeline persists everything.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

@dataclass
class ImagePrompt:
    """Everything an image provider needs to keep scenes consistent."""

    prompt: str
    negative_prompt: str
    width: int
    height: int
    seed: int
    character_sheet: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageResult:
    path: str
    width: int
    height: int


@dataclass
class VideoPrompt:
    prompt: str
    negative_prompt: str
    duration: float
    motion: str = "zoom_in"  # zoom_in | zoom_out | pan_left | pan_right | float


@dataclass
class ClipResult:
    path: str
    duration: float


@dataclass
class WordTiming:
    word: str
    start: float
    end: float


@dataclass
class VoiceResult:
    path: str
    duration: float
    word_timings: list[WordTiming]


@dataclass
class MusicResult:
    path: str
    duration: float
    credits: str


# ---------------------------------------------------------------------------
# Capability interfaces
# ---------------------------------------------------------------------------

class TextProvider(Protocol):
    name: str
    label: str
    requires_key: bool

    def generate(
        self,
        system: str,
        prompt: str,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.8,
        json_response: bool = False,
    ) -> str: ...


class ImageProvider(Protocol):
    name: str
    label: str
    requires_key: bool

    def generate_image(self, prompt: ImagePrompt, out_path: str) -> ImageResult: ...


class VideoProvider(Protocol):
    name: str
    label: str
    requires_key: bool

    def generate_clip(
        self, image_path: str, prompt: VideoPrompt, out_path: str
    ) -> ClipResult: ...


class VoiceProvider(Protocol):
    name: str
    label: str
    requires_key: bool

    def synthesize(
        self,
        text: str,
        out_path: str,
        *,
        voice: str = "female",
        language: str = "en",
        target_duration: float | None = None,
    ) -> VoiceResult: ...


class MusicProvider(Protocol):
    name: str
    label: str
    requires_key: bool

    def generate_track(
        self, mood: str, duration: float, out_path: str
    ) -> MusicResult: ...


class ProviderError(RuntimeError):
    """Raised when an external provider call fails."""

    def __init__(self, provider: str, message: str):
        super().__init__(f"[{provider}] {message}")
        self.provider = provider
