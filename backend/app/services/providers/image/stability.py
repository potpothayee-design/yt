"""Stability AI (SDXL / Stable Image Core) provider."""

from __future__ import annotations

import httpx

from app.services.providers.base import ImagePrompt, ImageResult, ProviderError


class StabilityImageProvider:
    name = "stability"
    label = "Stability AI (SDXL)"
    requires_key = True

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.api_key = api_key or ""
        self.options = options or {}
        self.model = self.options.get("model", "core")

    def generate_image(self, prompt: ImagePrompt, out_path: str) -> ImageResult:
        if not self.api_key:
            raise ProviderError(self.name, "missing STABILITY_API_KEY")
        aspect = "16:9" if prompt.width > prompt.height else ("9:16" if prompt.height > prompt.width else "1:1")
        try:
            with httpx.Client(timeout=300) as client:
                resp = client.post(
                    f"https://api.stability.ai/v2beta/stable-image/generate/{self.model}",
                    headers={"Authorization": f"Bearer {self.api_key}", "Accept": "image/*"},
                    files={"none": ""},
                    data={
                        "prompt": prompt.prompt,
                        "negative_prompt": prompt.negative_prompt,
                        "aspect_ratio": aspect,
                        "seed": str(prompt.seed % (2**31)),
                        "style_preset": "3d-model",
                        "output_format": "png",
                    },
                )
                resp.raise_for_status()
                raw = resp.content
        except httpx.HTTPStatusError as exc:
            raise ProviderError(self.name, f"HTTP {exc.response.status_code}: {exc.response.text[:300]}") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(self.name, str(exc)) from exc

        with open(out_path, "wb") as fh:
            fh.write(raw)
        return ImageResult(path=out_path, width=prompt.width, height=prompt.height)
