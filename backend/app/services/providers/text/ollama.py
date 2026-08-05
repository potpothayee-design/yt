"""Ollama — local LLMs via the open-source runner (no API key, fully private).

Upstream: https://github.com/ollama/ollama

Setup (once):
    winget install Ollama.Ollama        # or https://ollama.com/download
    ollama pull qwen2.5:3b              # small, good at structured JSON

The studio talks to the local server at OLLAMA_HOST (default
http://localhost:11434) with model OLLAMA_MODEL (default qwen2.5:3b).
The pipeline still steers the model with its knowledge base, originality and
age-appropriateness rules; responses are extracted as strict JSON.
"""

from __future__ import annotations

import json
import os
import re

from app.services.providers.base import ProviderError

DEFAULT_MODEL = "qwen2.5:3b"


def _host() -> str:
    return os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def _model() -> str:
    return os.environ.get("OLLAMA_MODEL", DEFAULT_MODEL)


def _extract_json(text: str) -> str:
    """Return a JSON payload string from possibly prose-wrapped model output."""
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate, flags=re.S).strip()
    try:
        json.loads(candidate)
        return candidate
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", candidate, re.S)
        if match:
            json.loads(match.group(0))  # raises -> caller turns into ProviderError
            return match.group(0)
        raise


class OllamaTextProvider:
    name = "ollama"
    label = "Ollama local LLM (open-source, offline)"
    requires_key = False

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.options = options or {}
        self.model = self.options.get("model") or _model()
        self.host = self.options.get("host") or _host()

    def probe(self) -> tuple[bool, str]:
        import httpx

        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self.host}/api/tags")
                resp.raise_for_status()
            models = [m.get("name", "") for m in resp.json().get("models", [])]
            if any(m.split(":")[0] == self.model.split(":")[0] for m in models):
                return True, f"Ollama running with model '{self.model}'."
            return False, (f"Ollama is running but model '{self.model}' is not pulled yet — "
                           f"run: ollama pull {self.model}")
        except Exception:
            return False, ("Ollama not reachable — install from https://ollama.com and run "
                           f"`ollama pull {_model()}` (takes a few minutes, one time).")

    def generate(
        self,
        system: str,
        prompt: str,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.8,
        json_response: bool = True,
    ) -> str:
        import httpx

        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if json_response:
            payload["format"] = "json"
        try:
            with httpx.Client(timeout=600.0) as client:
                resp = client.post(f"{self.host}/api/chat", json=payload)
                resp.raise_for_status()
                content = resp.json()["message"]["content"]
        except httpx.HTTPError as exc:
            raise ProviderError(self.name, f"Ollama request failed: {exc}") from exc
        if json_response:
            try:
                return _extract_json(content)
            except Exception as exc:
                raise ProviderError(self.name, "model did not return valid JSON") from exc
        return content
