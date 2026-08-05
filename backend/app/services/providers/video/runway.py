"""Runway image-to-video provider (Gen-3 style tasks API).

Implements the full request/poll/download flow. Runway clips are short, so
the pipeline requests one clip per scene and the composer merges them with
matched transitions — narrative continuity comes from the shared keyframe
image + character sheet embedded in every prompt.

NOTE: vendor video APIs evolve quickly; the endpoint/payload here follows the
public Runway API documentation. Adjust ``_BASE``/payload fields in
``options`` if your account uses a different version.
"""

from __future__ import annotations

import time

import httpx

from app.services.providers.base import ClipResult, ProviderError, VideoPrompt
from app.services.rendering.ffmpeg_utils import probe_duration

_BASE = "https://api.dev.runwayml.com/v1"


class RunwayVideoProvider:
    name = "runway"
    label = "Runway Gen"
    requires_key = True

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.api_key = api_key or ""
        self.options = options or {}
        self.model = self.options.get("model", "gen3a_turbo")

    def generate_clip(self, image_path: str, prompt: VideoPrompt, out_path: str) -> ClipResult:
        if not self.api_key:
            raise ProviderError(self.name, "missing RUNWAY_API_KEY")
        headers = {"Authorization": f"Bearer {self.api_key}",
                   "X-Runway-Version": "2024-11-06"}
        with open(image_path, "rb") as fh:
            import base64
            image_b64 = base64.b64encode(fh.read()).decode()
        duration = 10 if prompt.duration > 6 else 5
        try:
            with httpx.Client(timeout=120) as client:
                task = client.post(
                    f"{_BASE}/image_to_video",
                    headers=headers,
                    json={
                        "model": self.model,
                        "promptImage": f"data:image/png;base64,{image_b64}",
                        "promptText": prompt.prompt[:900],
                        "duration": duration,
                    },
                )
                task.raise_for_status()
                task_id = task.json()["id"]
                # poll for completion
                for _ in range(180):
                    time.sleep(5)
                    poll = client.get(f"{_BASE}/tasks/{task_id}", headers=headers)
                    poll.raise_for_status()
                    data = poll.json()
                    status = data.get("status")
                    if status == "SUCCEEDED" and data.get("output"):
                        video = client.get(data["output"][0])
                        video.raise_for_status()
                        with open(out_path, "wb") as fh:
                            fh.write(video.content)
                        return ClipResult(path=out_path, duration=probe_duration(out_path))
                    if status in ("FAILED", "CANCELLED"):
                        raise ProviderError(self.name, f"task {status}: {data.get('failure', '')}")
            raise ProviderError(self.name, "timed out waiting for clip")
        except httpx.HTTPStatusError as exc:
            raise ProviderError(self.name, f"HTTP {exc.response.status_code}: {exc.response.text[:300]}") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(self.name, str(exc)) from exc
