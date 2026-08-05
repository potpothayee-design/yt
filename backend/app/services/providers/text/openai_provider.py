"""OpenAI chat-completions text provider."""

from __future__ import annotations

import httpx

from app.services.providers.base import ProviderError


class OpenAITextProvider:
    name = "openai"
    label = "OpenAI GPT"
    requires_key = True

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.api_key = api_key or ""
        self.options = options or {}
        self.model = self.options.get("model", "gpt-4o-mini")

    def generate(self, system: str, prompt: str, *, max_tokens: int = 4096,
                 temperature: float = 0.8, json_response: bool = False) -> str:
        if not self.api_key:
            raise ProviderError(self.name, "missing OPENAI_API_KEY")
        body: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if json_response:
            body["response_format"] = {"type": "json_object"}
        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:  # surface API message
            raise ProviderError(self.name, f"HTTP {exc.response.status_code}: {exc.response.text[:300]}") from exc
        except (httpx.HTTPError, KeyError, IndexError) as exc:
            raise ProviderError(self.name, str(exc)) from exc
