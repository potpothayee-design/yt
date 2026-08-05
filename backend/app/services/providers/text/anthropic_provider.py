"""Anthropic Messages API text provider."""

from __future__ import annotations

import httpx

from app.services.providers.base import ProviderError


class AnthropicTextProvider:
    name = "anthropic"
    label = "Anthropic Claude"
    requires_key = True

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.api_key = api_key or ""
        self.options = options or {}
        self.model = self.options.get("model", "claude-3-5-haiku-latest")

    def generate(self, system: str, prompt: str, *, max_tokens: int = 4096,
                 temperature: float = 0.8, json_response: bool = False) -> str:
        if not self.api_key:
            raise ProviderError(self.name, "missing ANTHROPIC_API_KEY")
        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "system": system,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                resp.raise_for_status()
                data = resp.json()
            return "".join(b.get("text", "") for b in data.get("content", []))
        except httpx.HTTPStatusError as exc:
            raise ProviderError(self.name, f"HTTP {exc.response.status_code}: {exc.response.text[:300]}") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(self.name, str(exc)) from exc
