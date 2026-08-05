"""Provider registry & factory.

Providers are addressed by (capability, name). Resolution order for the
instance used by a pipeline run:

1. Per-user setting from the Settings page (DB, API key encrypted at rest)
2. Environment default (``TEXT_PROVIDER`` / ``OPENAI_API_KEY`` etc.)
3. The ``local`` offline provider — always available as a safe fallback
"""

from __future__ import annotations

import importlib
from typing import Any

from app.core.config import get_settings
from app.core.errors import ProviderNotConfiguredError

CAPABILITIES = ("text", "image", "video", "voice", "music")

# capability -> provider name -> (module, class, label, requires_key, description)
_REGISTRY: dict[str, dict[str, tuple[str, str, str, bool, str]]] = {
    "text": {
        "local": (
            "app.services.providers.text.local", "LocalTextProvider",
            "Built-in Writer (offline)", False,
            "Original curriculum-aware writing engine. No API key needed — "
            "works fully offline using the internal knowledge base.",
        ),
        "openai": (
            "app.services.providers.text.openai_provider", "OpenAITextProvider",
            "OpenAI GPT", True,
            "OpenAI chat models guided by the internal knowledge base and "
            "strict originality/age-appropriateness constraints.",
        ),
        "anthropic": (
            "app.services.providers.text.anthropic_provider", "AnthropicTextProvider",
            "Anthropic Claude", True,
            "Anthropic Claude models guided by the internal knowledge base "
            "and strict originality/age-appropriateness constraints.",
        ),
    },
    "image": {
        "local": (
            "app.services.providers.image.local", "LocalImageProvider",
            "Built-in Illustrator (offline)", False,
            "Procedural storybook illustrator with a consistent seeded "
            "character, palette and composition per project. No key needed.",
        ),
        "openai": (
            "app.services.providers.image.openai_images", "OpenAIImageProvider",
            "OpenAI Images (DALL·E / gpt-image)", True,
            "OpenAI image generation using the pipeline's consistent scene "
            "prompts and character sheet.",
        ),
        "stability": (
            "app.services.providers.image.stability", "StabilityImageProvider",
            "Stability AI (SDXL)", True,
            "Stability AI image generation with negative prompt support.",
        ),
    },
    "video": {
        "local": (
            "app.services.providers.video.local", "LocalVideoProvider",
            "Built-in Motion Engine (offline)", False,
            "Ken Burns motion-graphics renderer (zoom/pan/float) built on "
            "ffmpeg. Creates as many seamless clips as needed. No key needed.",
        ),
        "pika": (
            "app.services.providers.video.pika", "PikaVideoProvider",
            "Pika", True,
            "Pika text-to-video using structured scene prompts (short clips "
            "are merged automatically by the pipeline).",
        ),
        "runway": (
            "app.services.providers.video.runway", "RunwayVideoProvider",
            "Runway Gen", True,
            "Runway image-to-video using the rendered keyframe and motion "
            "prompts (short clips are merged automatically).",
        ),
    },
    "voice": {
        "local": (
            "app.services.providers.voice.local", "LocalVoiceProvider",
            "Built-in Voice (offline)", False,
            "Offline formant synthesizer (clear, paced narration with word "
            "timings). Great for previews; plug a voiced provider for release.",
        ),
        "openai-tts": (
            "app.services.providers.voice.openai_tts", "OpenAITTSProvider",
            "OpenAI TTS", True, "Warm, natural OpenAI voices (alloy, nova, shimmer...).",
        ),
        "elevenlabs": (
            "app.services.providers.voice.elevenlabs", "ElevenLabsProvider",
            "ElevenLabs", True, "Highly expressive kid-friendly voices.",
        ),
        "google-tts": (
            "app.services.providers.voice.google_tts", "GoogleTTSProvider",
            "Google Cloud TTS", True, "Google Cloud voices in many languages.",
        ),
    },
    "music": {
        "local": (
            "app.services.providers.music.local", "LocalMusicProvider",
            "Built-in Composer (offline)", False,
            "Royalty-free procedural music-box composer. Loopable, soft, "
            "cheerful, mixes quietly under narration. No key needed.",
        ),
        "library": (
            "app.services.providers.music.library", "LibraryMusicProvider",
            "Royalty-free Library", False,
            "Pick a track from a configured folder of your own licensed/ "
            "royalty-free music files.",
        ),
    },
}


class ProviderRegistry:
    """Access to the static provider catalog."""

    @staticmethod
    def catalog() -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for capability, providers in _REGISTRY.items():
            for name, (_, _, label, requires_key, description) in providers.items():
                out.append(
                    {
                        "capability": capability,
                        "name": name,
                        "label": label,
                        "requires_key": requires_key,
                        "is_local": not requires_key,
                        "description": description,
                    }
                )
        return out

    @staticmethod
    def names(capability: str) -> list[str]:
        return list(_REGISTRY.get(capability, {}))


def provider_catalog() -> list[dict[str, Any]]:
    return ProviderRegistry.catalog()


def _load(capability: str, name: str):
    entry = _REGISTRY.get(capability, {}).get(name)
    if not entry:
        raise ProviderNotConfiguredError(capability, f"{name} (unknown provider)")
    module_path, class_name, *_ = entry
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def get_provider(
    capability: str,
    provider_name: str | None = None,
    api_key: str | None = None,
    options: dict[str, Any] | None = None,
) -> Any:
    """Instantiate a provider.

    ``provider_name=None`` resolves the environment default for the
    capability. A missing API key for a key-requiring provider falls back to
    the local provider so the pipeline keeps working and flags it in logs.
    """
    settings = get_settings()
    if capability not in CAPABILITIES:
        raise ProviderNotConfiguredError(capability, "unknown capability")

    name = provider_name or getattr(settings, f"{capability.upper()}_PROVIDER")
    if name not in _REGISTRY[capability]:
        name = "local"

    *_, requires_key, _desc = _REGISTRY[capability][name]
    key = api_key if api_key is not None else settings.provider_key(name)
    if requires_key and not key:
        # graceful degradation with an explicit, visible reason
        from app.core.logging import get_logger

        get_logger("studio.providers").warning(
            "provider %s/%s requires an API key — falling back to local",
            capability, name,
        )
        name = "local"
        key = None

    cls = _load(capability, name)
    return cls(api_key=key, options=options or {})
