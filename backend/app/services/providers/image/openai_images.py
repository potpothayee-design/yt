"""OpenAI Images provider (DALL·E 3 / gpt-image-1)."""

from __future__ import annotations

import base64

import httpx

from app.services.providers.base import ImagePrompt, ImageResult, ProviderError


class OpenAIImageProvider:
    name = "openai"
    label = "OpenAI Images (DALL·E / gpt-image)"
    requires_key = True

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.api_key = api_key or ""
        self.options = options or {}
        self.model = self.options.get("model", "dall-e-3")

    def generate_image(self, prompt: ImagePrompt, out_path: str) -> ImageResult:
        if not self.api_key:
            raise ProviderError(self.name, "missing OPENAI_API_KEY")
        w, h = prompt.width, prompt.height
        size = "1024x1024"
        if self.model == "dall-e-3":
            size = "1792x1024" if w > h else ("1024x1792" if h > w else "1024x1024")
        body: dict = {
            "model": self.model,
            "prompt": prompt.prompt + f" AVOID: {prompt.negative_prompt}",
            "n": 1,
            "size": size,
        }
        if self.model == "dall-e-3":
            body["quality"] = "hd"
            body["response_format"] = "b64_json"
        try:
            with httpx.Client(timeout=300) as client:
                resp = client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()["data"][0]
                raw = (base64.b64decode(data["b64_json"]) if data.get("b64_json")
                       else client.get(data["url"]).content)
        except httpx.HTTPStatusError as exc:
            raise ProviderError(self.name, f"HTTP {exc.response.status_code}: {exc.response.text[:300]}") from exc
        except (httpx.HTTPError, KeyError) as exc:
            raise ProviderError(self.name, str(exc)) from exc

        with open(out_path, "wb") as fh:
            fh.write(raw)
        return ImageResult(path=out_path, width=w, height=h)
