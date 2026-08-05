"""Piper TTS — MIT-licensed neural TTS, runs fully offline on CPU.

Upstream: https://github.com/rhasspy/piper  (voices: rhasspy/piper-voices)

Install once:  ``pip install piper-tts``
Voice models (~60 MB, MIT) auto-download from HuggingFace on first use into
``backend/storage/models/piper`` and are reused afterwards. If Piper (or the
download) is unavailable, synthesis falls back to the built-in offline chain
so a job never fails because of this provider.
"""

from __future__ import annotations

import os
import urllib.request
import wave
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.providers.base import VoiceResult

log = get_logger("studio.providers.piper")

_HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"

# voice style -> (name, quality) — bright, kid-friendly defaults
_STYLE_MAP = {
    "female": ("amy", "medium"),
    "child": ("amy", "medium"),
    "male": ("libritts_r", "medium"),
}

_MAX_MODEL_BYTES = 200 * 1024 * 1024
_LOADED: dict[str, object] = {}


def piper_installed() -> bool:
    try:
        import piper  # noqa: F401

        return True
    except Exception:
        return False


def _model_dir() -> Path:
    override = os.environ.get("PIPER_MODEL_DIR")
    root = Path(override) if override else (
        Path(get_settings().MEDIA_ROOT).parent / "models" / "piper"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def _voice_paths(voice: str) -> tuple[Path, Path]:
    """Local .onnx (+ config) paths for the requested voice style."""
    override = os.environ.get("PIPER_VOICE_NAME")  # e.g. "en_US-lessac-medium"
    if override:
        name, _, quality = override.replace("en_US-", "").partition("-")
    else:
        name, quality = _STYLE_MAP.get(voice, _STYLE_MAP["female"])
    onnx = _model_dir() / f"en_US-{name}-{quality}.onnx"
    return onnx, Path(str(onnx) + ".json")


def _voice_urls(onnx: Path) -> tuple[str, str]:
    stem = onnx.stem  # en_US-amy-medium
    _, _, tail = stem.partition("_")
    name, _, quality = tail.partition("-")
    base = f"{_HF_BASE}/en/en_US/{name}/{quality}/{stem}.onnx"
    return base, base + ".json"


def _download(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    if not url.startswith("https://"):
        raise ValueError("refusing non-https model URL")
    log.info("downloading piper voice model %s (one-time, ~60MB)…", dest.name)
    tmp = Path(str(dest) + ".part")
    with urllib.request.urlopen(url, timeout=120) as resp, open(tmp, "wb") as fh:
        total = 0
        while chunk := resp.read(1 << 18):
            total += len(chunk)
            if total > _MAX_MODEL_BYTES:
                raise ValueError("piper model larger than expected — aborting")
            fh.write(chunk)
    tmp.replace(dest)
    log.info("piper voice model ready: %s", dest.name)


def _ensure_voice(voice: str) -> tuple[Path, Path]:
    onnx, cfg = _voice_paths(voice)
    u_onnx, u_cfg = _voice_urls(onnx)
    _download(u_onnx, onnx)
    _download(u_cfg, cfg)
    return onnx, cfg


def _load(voice: str):
    """Load and cache a PiperVoice instance keyed by style."""
    key = os.environ.get("PIPER_VOICE_NAME") or voice
    if key in _LOADED:
        return _LOADED[key]
    from piper import PiperVoice

    onnx, cfg = _ensure_voice(voice)
    instance = PiperVoice.load(str(onnx), config_path=str(cfg), use_cuda=False)
    _LOADED[key] = instance
    return instance


def _wav_duration(path: str) -> float:
    with wave.open(path, "rb") as wf:
        return wf.getnframes() / float(wf.getframerate())


def synthesize_via_piper(text: str, out_path: str, voice: str) -> VoiceResult | None:
    """Try Piper; return None so callers can fall back on any failure."""
    if not piper_installed():
        return None
    try:
        pv = _load(voice)
        try:
            pv.synthesize_wav(text, out_path)  # piper-tts >= 1.2
        except TypeError:  # older streaming API
            with wave.open(out_path, "wb") as wav_file:
                pv.synthesize(text, wav_file)  # type: ignore[arg-type]
        from app.services.providers.voice.local import _result_from_wav

        return _result_from_wav(text, out_path)
    except Exception as exc:  # download/network/model errors are all non-fatal
        log.warning("piper synthesis failed (%s) — falling back", exc)
        return None


class PiperVoiceProvider:
    name = "piper"
    label = "Piper TTS (open-source, offline)"
    requires_key = False

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.options = options or {}

    def probe(self) -> tuple[bool, str]:
        if not piper_installed():
            return False, ("piper-tts is not installed — run: pip install piper-tts "
                           "(the launcher scripts already try this automatically)")
        onnx, _ = _voice_paths("female")
        if onnx.exists():
            return True, "Piper ready — neural voice model cached locally."
        return True, ("Piper installed. The neural voice model (~60MB, open-source) "
                      "downloads once on first narration.")

    def synthesize(self, text: str, out_path: str, *, voice: str = "female",
                   language: str = "en", target_duration: float | None = None) -> VoiceResult:
        from app.services.providers.voice.local import LocalVoiceProvider, _clean_spoken_text

        text = _clean_spoken_text(text)
        result = synthesize_via_piper(text, out_path, voice)
        if result:
            return result
        # never fail a job — reuse the complete built-in chain
        return LocalVoiceProvider().synthesize(
            text, out_path, voice=voice, language=language, target_duration=target_duration
        )


def voice_model_info() -> dict[str, str | bool]:
    onnx, _ = _voice_paths("female")
    return {"installed": piper_installed(), "model_cached": onnx.exists()}
