"""MusicGen (Meta) — open-source instrumental music generation.

Upstream: https://github.com/facebookresearch/audiocraft
Model: MIT license; weights CC-BY-NC 4.0 (non-commercial use only — review
before publishing videos commercially).

Setup (heavyweight, optional):
    pip install torch audiocraft           # ~4 GB incl. CPU wheels
    # weights download once from HuggingFace on first use (~1.6 GB)

Runs on CPU (slow: ~1-4 min per 15s clip on a laptop); a GPU makes it fast.
Longer videos are covered by generating a seamless-ish chunk and tiling it
with a short crossfade, same as the built-in composer.
"""

from __future__ import annotations

import os
import wave

import numpy as np

from app.services.providers.base import MusicResult, ProviderError

_MODEL: dict[str, object] = {}
SR = 32000  # MusicGen native sample rate
_CHUNK = 20.0  # seconds generated per MusicGen call (CPU-friendly)
_FADE = 0.35  # crossfade seconds when tiling chunks


def musicgen_installed() -> bool:
    try:
        import audiocraft  # noqa: F401
        import torch  # noqa: F401

        return True
    except Exception:
        return False


def _model():
    if "gen" in _MODEL:
        return _MODEL["gen"]
    from audiocraft.models import MusicGen

    name = os.environ.get("MUSICGEN_MODEL", "facebook/musicgen-small")
    gen = MusicGen.get_pretrained(name)
    _MODEL["gen"] = gen
    return gen


def _write_wav(path: str, audio: np.ndarray) -> None:
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


def _tile(audio: np.ndarray, target: int, fade: int) -> np.ndarray:
    """Loop audio to exactly `target` samples with raised-cosine crossfades."""
    if len(audio) == 0:
        return np.zeros(target)
    out = np.zeros(target)
    pos = 0
    ramp = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade))
    while pos < target:
        seg = audio
        take = min(len(seg), target - pos)
        if pos > 0 and take > fade:
            out[pos:pos + fade] *= (1 - ramp)
            seg = seg.copy()
            seg[:fade] *= ramp
            out[pos:pos + take] += seg[:take]
        else:
            out[pos:pos + take] = seg[:take]
        pos += take
    return out


class MusicGenProvider:
    name = "musicgen"
    label = "MusicGen (open-source, offline)"
    requires_key = False

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.options = options or {}

    def probe(self) -> tuple[bool, str]:
        if not musicgen_installed():
            return False, ("torch/audiocraft not installed — optional heavyweight: "
                           "pip install torch audiocraft (needs ~6GB disk + RAM; "
                           "model weights download on first use)")
        return True, ("MusicGen available. Weights (~1.6GB) download once on first use; "
                      "CPU generation is slow on laptops (minutes per clip).")

    def generate_track(self, mood: str, duration: float, out_path: str) -> MusicResult:
        if not musicgen_installed():
            raise ProviderError(self.name, "pip install torch audiocraft first "
                                           "(see docs/PROVIDERS.md → Open-source providers)")
        import torch  # noqa: F401 — needed by audiocraft internals

        gen = _model()
        prompt = (
            f"gentle {mood} children's instrumental: soft music box and ukulele, "
            "cheerful and calm, simple loopable melody, no vocals, clean mix"
        )
        seconds = max(4.0, min(float(duration), 600.0))
        chunk_s = min(_CHUNK, seconds)
        gen.set_generation_params(duration=chunk_s, top_k=240, temperature=1.0)
        wav = gen.generate([prompt])  # (1, channels, samples) @ 32kHz
        audio = wav[0].mean(dim=0).detach().cpu().numpy()  # mono
        target = int(seconds * SR)
        audio = _tile(audio * 0.9, target, int(_FADE * SR))
        _write_wav(out_path, audio)
        return MusicResult(path=out_path, duration=seconds,
                           credits="MusicGen (facebookresearch/audiocraft, MIT code / "
                                   "CC-BY-NC-4.0 weights — non-commercial)")
