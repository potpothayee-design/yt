"""ElevenLabs TTS provider."""

from __future__ import annotations

import re

import httpx

from app.services.providers.base import ProviderError, VoiceResult
from app.services.providers.voice.local import _spread_timings
from app.services.rendering.ffmpeg_utils import audio_duration


class ElevenLabsProvider:
    name = "elevenlabs"
    label = "ElevenLabs"
    requires_key = True

    # warm kid-friendly stock voices
    _VOICES = {"female": "21m00Tcm4TlvDq8ikWAM",   # Rachel
               "male": "ErXwobaYiN019PkySvjV",     # Antoni
               "child": "pNInz6obpgDQGcFmaJgB"}    # Adam (low, steady)

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.api_key = api_key or ""
        self.options = options or {}
        self.model = self.options.get("model", "eleven_multilingual_v2")

    def synthesize(self, text: str, out_path: str, *, voice: str = "female",
                   language: str = "en", target_duration: float | None = None) -> VoiceResult:
        if not self.api_key:
            raise ProviderError(self.name, "missing ELEVENLABS_API_KEY")
        voice_id = self.options.get("voice_id") or self._VOICES.get(voice, self._VOICES["female"])
        try:
            with httpx.Client(timeout=180) as client:
                resp = client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                    headers={"xi-api-key": self.api_key},
                    params={"output_format": "mp3_44100_128"},
                    json={
                        "text": text,
                        "model_id": self.model,
                        "voice_settings": {
                            "stability": 0.55, "similarity_boost": 0.75,
                            "style": 0.45, "use_speaker_boost": True,
                        },
                    },
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
