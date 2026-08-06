"""Pollinations.AI video generation — free, keyless, light weekly credit cap.

https://pollinations.ai — Seedance/Wan-Fast via the unified gen endpoint.
The free anonymous tier draws from a small weekly credit allowance, so the
pipeline should be pointed here for special scenes rather than bulk renders.
When the allowance is exhausted the provider raises a clear error and the
job can fall back to the built-in motion engine.

Note: the URL API only accepts text-to-video without a publicly reachable
input image, so keyframe images are not sent; scene prompts keep the look
consistent instead (same limitation/pragmatics as other zero-setup tiers).
"""

from __future__ import annotations

import os
import urllib.parse

from app.core.config import get_settings
from app.services.providers.base import ClipResult, ProviderError, VideoPrompt

_BASE = os.environ.get("POLLINATIONS_VIDEO_BASE", "https://gen.pollinations.ai/image")


def build_video_url(prompt: VideoPrompt, aspect_ratio: str = "16:9") -> str:
    duration = int(round(min(10.0, max(2.0, prompt.duration))))
    query = urllib.parse.urlencode({
        "model": os.environ.get("POLLINATIONS_VIDEO_MODEL", "seedance"),
        "duration": duration,
        "aspectRatio": aspect_ratio,
        "audio": "false",
        "safe": "true",
        "private": "true",
        "nologo": "true",
    })
    return f"{_BASE}/{urllib.parse.quote(prompt.prompt)}?{query}"


class PollinationsVideoProvider:
    name = "pollinations"
    label = "Pollinations video (free, keyless, weekly credits)"
    requires_key = False

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.options = options or {}
        self.api_key = (api_key if api_key is not None
                        else get_settings().provider_key("pollinations")) or ""

    def probe(self) -> tuple[bool, str]:
        import httpx

        try:
            with httpx.Client(timeout=6.0) as client:
                resp = client.get(_BASE.rsplit("/", 1)[0])
            if resp.status_code < 500:
                return True, ("Pollinations reachable — free Seedance/Wan-Fast tier "
                              "(small weekly credit allowance, no key needed).")
            return False, f"Pollinations returned HTTP {resp.status_code}."
        except Exception:
            return False, "could not reach pollinations.ai — check your connection."

    def generate_clip(
        self, image_path: str, prompt: VideoPrompt, out_path: str
    ) -> ClipResult:
        import httpx

        url = build_video_url(prompt, self.options.get("aspect_ratio", "16:9"))
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            with httpx.Client(timeout=900.0, follow_redirects=True) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code in (402, 429):
                    raise ProviderError(self.name, "free weekly video credits exhausted — "
                                                   "switch back to the built-in Motion Engine "
                                                   "or wait for the allowance to reset")
                resp.raise_for_status()
        except ProviderError:
            raise
        except httpx.HTTPError as exc:
            raise ProviderError(self.name, f"Pollinations video request failed: {exc}") from exc
        if len(resp.content) < 10_000:
            raise ProviderError(self.name, "Pollinations returned an unexpected (tiny) response")
        with open(out_path, "wb") as fh:
            fh.write(resp.content)

        from app.services.rendering.ffmpeg_utils import probe_duration

        try:
            duration = probe_duration(out_path)
        except Exception:
            duration = prompt.duration
        return ClipResult(path=out_path, duration=duration)
