"""Pika text-to-video provider.

Same contract as the local engine; because clips are short, the pipeline
schedules one clip per scene and the composer stitches them with matched
transitions. Pika's public API has changed over time — the payload here is
kept in one small method (``_payload``) so upgrading to a new schema is a
one-line change.
"""

from __future__ import annotations

import time

import httpx

from app.services.providers.base import ClipResult, ProviderError, VideoPrompt
from app.services.rendering.ffmpeg_utils import probe_duration

_BASE = "https://api.pika.art/v1"


class PikaVideoProvider:
    name = "pika"
    label = "Pika"
    requires_key = True

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.api_key = api_key or ""
        self.options = options or {}
        self.model = self.options.get("model", "pika-1.5")

    @staticmethod
    def _payload(prompt: VideoPrompt) -> dict:
        return {
            "promptText": prompt.prompt[:900],
            "negativePrompt": prompt.negative_prompt[:500],
            "options": {"aspectRatio": "16:9", "frameRate": 24},
        }

    def generate_clip(self, image_path: str, prompt: VideoPrompt, out_path: str) -> ClipResult:
        if not self.api_key:
            raise ProviderError(self.name, "missing PIKA_API_KEY")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            with httpx.Client(timeout=120) as client:
                task = client.post(f"{_BASE}/generations", headers=headers,
                                   json={"model": self.model, **self._payload(prompt)})
                task.raise_for_status()
                gen_id = task.json().get("id") or task.json().get("generation_id")
                for _ in range(180):
                    time.sleep(5)
                    poll = client.get(f"{_BASE}/generations/{gen_id}", headers=headers)
                    poll.raise_for_status()
                    data = poll.json()
                    status = (data.get("status") or "").lower()
                    url = (data.get("video") or {}).get("url") or data.get("video_url")
                    if status in ("succeeded", "completed") and url:
                        video = client.get(url)
                        video.raise_for_status()
                        with open(out_path, "wb") as fh:
                            fh.write(video.content)
                        return ClipResult(path=out_path, duration=probe_duration(out_path))
                    if status in ("failed", "cancelled"):
                        raise ProviderError(self.name, f"generation {status}")
            raise ProviderError(self.name, "timed out waiting for clip")
        except httpx.HTTPStatusError as exc:
            raise ProviderError(self.name, f"HTTP {exc.response.status_code}: {exc.response.text[:300]}") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(self.name, str(exc)) from exc
