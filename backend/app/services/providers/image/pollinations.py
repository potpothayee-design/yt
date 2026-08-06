"""Pollinations.AI image generation — free Flux images, keyless by default.

https://pollinations.ai — anonymous tier: construct a URL, get an image back,
nothing stored. A free POLLINATIONS_KEY (optional) lifts rate limits.

Flux URL prompt API does not take a separate negative prompt, so the
pipeline's negative terms are folded in as an "avoid: ..." tail.
"""

from __future__ import annotations

import os
import urllib.parse

from app.core.config import get_settings
from app.services.providers.base import ImagePrompt, ImageResult, ProviderError

_BASE = os.environ.get("POLLINATIONS_IMAGE_BASE", "https://image.pollinations.ai/prompt")
_MAX_DIM = 2048


def build_image_url(prompt: ImagePrompt) -> str:
    """Public for tests — the anonymous image URL for a scene prompt."""
    negative = prompt.negative_prompt.strip()
    full_prompt = prompt.prompt if not negative else f"{prompt.prompt} -- avoid: {negative}"
    query = urllib.parse.urlencode({
        "width": min(prompt.width, _MAX_DIM),
        "height": min(prompt.height, _MAX_DIM),
        "seed": prompt.seed,
        "model": os.environ.get("POLLINATIONS_IMAGE_MODEL", "flux"),
        "nologo": "true",
        "safe": "true",
        "private": "true",
    })
    return f"{_BASE}/{urllib.parse.quote(full_prompt)}?{query}"


class PollinationsImageProvider:
    name = "pollinations"
    label = "Pollinations Flux (free, keyless)"
    requires_key = False

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.options = options or {}
        self.api_key = (api_key if api_key is not None
                        else get_settings().provider_key("pollinations")) or ""

    def probe(self) -> tuple[bool, str]:
        import httpx

        try:
            with httpx.Client(timeout=6.0) as client:
                resp = client.get("https://image.pollinations.ai/")
            if resp.status_code < 500:
                return True, "Pollinations reachable — anonymous free Flux tier, no key needed."
            return False, f"Pollinations returned HTTP {resp.status_code} — try later."
        except Exception:
            return False, "could not reach pollinations.ai — check your connection."

    def generate_image(self, prompt: ImagePrompt, out_path: str) -> ImageResult:
        import httpx

        url = build_image_url(prompt)
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            with httpx.Client(timeout=180.0, follow_redirects=True) as client:
                resp = client.get(url, headers=headers)
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(self.name, f"Pollinations image request failed: {exc}") from exc
        if len(resp.content) < 2048:
            raise ProviderError(self.name, "Pollinations returned an unexpected (tiny) response")
        with open(out_path, "wb") as fh:
            fh.write(resp.content)
        return ImageResult(path=out_path,
                           width=min(prompt.width, _MAX_DIM),
                           height=min(prompt.height, _MAX_DIM))
