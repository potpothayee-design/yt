"""OpenAI TTS provider (tts-1 / tts-1-hd / gpt-4o-mini-tts)."""

from __future__ import annotations

import re

import httpx

from app.services.providers.base import ProviderError, VoiceResult
from app.services.providers.voice.local import _spread_timings
from app.services.rendering.ffmpeg_utils import audio_duration

_VOICES = {"female": "nova", "male": "onyx", "child": "shimmer"}


class OpenAITTSProvider:
    name = "openai-tts"
    label = "OpenAI TTS"
    requires_key = True

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.api_key = api_key or ""
        self.options = options or {}
        self.model = self.options.get("model", "tts-1")

    def synthesize(self, text: str, out_path: str, *, voice: str = "female",
                   language: str = "en", target_duration: float | None = None) -> VoiceResult:
        if not self.api_key:
            raise ProviderError(self.name, "missing OPENAI_API_KEY")
        chosen = _VOICES.get(voice, voice if len(voice) <= 10 else "nova")
        try:
            with httpx.Client(timeout=180) as client:
                resp = client.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "voice": chosen, "input": text,
                          "response_format": "mp3", "speed": 1.0},
                )
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(self.name, f"HTTP {exc.response.status_code}: {exc.response.text[:300]}") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(self.name, str(exc)) from exc

        with open(out_path, "wb") as fh:
            fh.write(resp.content)
        duration = audio_duration(out_path)
        words = re.findall(r"[A-Za-z']+|\d+", text)
        return VoiceResult(path=out_path, duration=duration,
                           word_timings=_spread_timings(words, duration))
