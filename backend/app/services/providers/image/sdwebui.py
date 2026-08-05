"""Stable Diffusion WebUI (AUTOMATIC1111) — self-hosted open-source images.

Upstream: https://github.com/AUTOMATIC1111/stable-diffusion-webui

Setup (needs an NVIDIA GPU; full guide in docs/PROVIDERS.md):
    1. install SD WebUI (one-click installer from the repo)
    2. start it with the API enabled:  webui-user.bat --api
    3. set SDWEBUI_HOST (default http://127.0.0.1:7860) if it differs

The pipeline's character sheet, scene prompts and negative prompts are passed
straight through, so frame consistency still comes from prompt engineering.
"""

from __future__ import annotations

import base64
import os

from app.services.providers.base import ImagePrompt, ImageResult, ProviderError


def _host() -> str:
    return os.environ.get("SDWEBUI_HOST", "http://127.0.0.1:7860").rstrip("/")


def _snap8(value: int) -> int:
    return max(256, (value // 8) * 8)


class SDWebUIImageProvider:
    name = "sd-webui"
    label = "Stable Diffusion WebUI (open-source, self-hosted)"
    requires_key = False

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.options = options or {}
        self.host = self.options.get("host") or _host()
        self.steps = int(self.options.get("steps", 22))

    def probe(self) -> tuple[bool, str]:
        import httpx

        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self.host}/sdapi/v1/options")
                resp.raise_for_status()
            return True, "Stable Diffusion WebUI API reachable."
        except Exception:
            return False, ("SD WebUI API not reachable — start it with `--api` "
                           "(see docs/PROVIDERS.md → Open-source providers).")

    def generate_image(self, prompt: ImagePrompt, out_path: str) -> ImageResult:
        import httpx

        payload = {
            "prompt": prompt.prompt,
            "negative_prompt": prompt.negative_prompt,
            "width": _snap8(prompt.width),
            "height": _snap8(prompt.height),
            "seed": prompt.seed,
            "steps": self.steps,
            "cfg_scale": 6.5,
            "sampler_name": "DPM++ 2M Karras",
        }
        try:
            with httpx.Client(timeout=600.0) as client:
                resp = client.post(f"{self.host}/sdapi/v1/txt2img", json=payload)
                resp.raise_for_status()
                images = resp.json().get("images", [])
        except httpx.HTTPError as exc:
            raise ProviderError(self.name, f"SD WebUI request failed: {exc}") from exc
        if not images:
            raise ProviderError(self.name, "SD WebUI returned no image")
        with open(out_path, "wb") as fh:
            fh.write(base64.b64decode(images[0]))
        return ImageResult(path=out_path, width=payload["width"], height=payload["height"])
