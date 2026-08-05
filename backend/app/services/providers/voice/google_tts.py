"""Google Cloud Text-to-Speech provider (API-key auth)."""

from __future__ import annotations

import base64
import re

import httpx

from app.services.providers.base import ProviderError, VoiceResult
from app.services.providers.voice.local import _spread_timings
from app.services.rendering.ffmpeg_utils import audio_duration


class GoogleTTSProvider:
    name = "google-tts"
    label = "Google Cloud TTS"
    requires_key = True

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.api_key = api_key or ""
        self.options = options or {}

    def synthesize(self, text: str, out_path: str, *, voice: str = "female",
                   language: str = "en", target_duration: float | None = None) -> VoiceResult:
        if not self.api_key:
            raise ProviderError(self.name, "missing GOOGLE_TTS_API_KEY")
        lang = language if "-" in language else f"{language}-US"
        gender = "MALE" if voice == "male" else "FEMALE"
        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(
                    "https://texttospeech.googleapis.com/v1/text:synthesize",
                    params={"key": self.api_key},
                    json={
                        "input": {"text": text},
                        "voice": {"languageCode": lang, "ssmlGender": gender},
                        "audioConfig": {"audioEncoding": "MP3", "speakingRate": 0.95,
                                        "pitch": 1.5},
                    },
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(self.name, f"HTTP {exc.response.status_code}: {exc.response.text[:300]}") from exc
        except (httpx.HTTPError, KeyError) as exc:
            raise ProviderError(self.name, str(exc)) from exc

        with open(out_path, "wb") as fh:
            fh.write(base64.b64decode(data["audioContent"]))
        duration = audio_duration(out_path)
        words = re.findall(r"[A-Za-z']+|\d+", text)
        return VoiceResult(path=out_path, duration=duration,
                           word_timings=_spread_timings(words, duration))
