"""Google Gemini via AI Studio — generous free tier, key takes 1 minute.

Get a free key (no credit card, no install):
    https://aistudio.google.com  → "Get API key"

Free tier is more than a million tokens/day — plenty for scripts/metadata.
Model defaults to ``gemini-flash-latest`` (override with ``GEMINI_MODEL``).
"""

from __future__ import annotations

import json
import os
import re

from app.services.providers.base import ProviderError

_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _model() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-flash-latest")


def _extract_json(text: str) -> str:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate, flags=re.S).strip()
    try:
        json.loads(candidate)
        return candidate
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", candidate, re.S)
        if match:
            json.loads(match.group(0))
            return match.group(0)
        raise


class GeminiTextProvider:
    name = "gemini"
    label = "Google Gemini Flash (free tier)"
    requires_key = True

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.api_key = api_key or ""
        self.options = options or {}
        self.model = self.options.get("model") or _model()

    def probe(self) -> tuple[bool, str]:
        if not self.api_key:
            return False, ("no Google AI Studio key stored — get a free one at "
                           "aistudio.google.com and add it on the API Keys page")
        import httpx

        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.get(f"{_BASE}/models",
                                  headers={"x-goog-api-key": self.api_key})
            if resp.status_code == 200:
                return True, f"Gemini key valid — model '{self.model}' ready."
            if resp.status_code in (400, 401, 403):
                return False, "Gemini rejected the key — check it on the API Keys page."
            return False, f"Gemini returned HTTP {resp.status_code} — try again shortly."
        except Exception:
            return False, "could not reach Google AI Studio — check your connection."

    def generate(
        self,
        system: str,
        prompt: str,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.8,
        json_response: bool = True,
    ) -> str:
        if not self.api_key:
            raise ProviderError(self.name, "GEMINI_API_KEY missing — add your free "
                                           "AI Studio key on the API Keys page")
        import httpx

        generation_config: dict = {"temperature": temperature,
                                   "maxOutputTokens": max_tokens}
        if json_response:
            generation_config["responseMimeType"] = "application/json"
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": generation_config,
        }
        try:
            with httpx.Client(timeout=300.0) as client:
                resp = client.post(
                    f"{_BASE}/models/{self.model}:generateContent",
                    headers={"x-goog-api-key": self.api_key},
                    json=payload,
                )
                if resp.status_code == 429:
                    raise ProviderError(self.name, "Gemini free-tier rate limit hit — "
                                                   "wait a minute or the pipeline will retry")
                resp.raise_for_status()
                data = resp.json()
            parts = data["candidates"][0]["content"]["parts"]
            content = "".join(p.get("text", "") for p in parts)
        except ProviderError:
            raise
        except (httpx.HTTPError, KeyError, IndexError) as exc:
            raise ProviderError(self.name, f"Gemini request failed: {exc}") from exc
        if json_response:
            try:
                return _extract_json(content)
            except Exception as exc:
                raise ProviderError(self.name, "Gemini did not return valid JSON") from exc
        return content
