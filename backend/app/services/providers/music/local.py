"""Built-in composer (offline music provider).

Generates an ORIGINAL, royalty-free, loopable music-box track: soft marimba
plucks over a I–V–vi–IV progression, a warm pad, gentle bass and sleepy
hi-hats. Mood presets adjust tempo, scale and brightness. Because every note
is synthesized here, the output is license-free by construction — safe for
monetized kids content.
"""

from __future__ import annotations

import math
import wave

import numpy as np

from app.services.providers.base import MusicResult

SR = 22050

_MOODS = {
    "cheerful": {"bpm": 104, "root": 261.63, "brightness": 1.0, "swing": 0.0},
    "calm": {"bpm": 84, "root": 246.94, "brightness": 0.8, "swing": 0.04},
    "adventure": {"bpm": 120, "root": 293.66, "brightness": 1.1, "swing": 0.02},
    "bedtime": {"bpm": 72, "root": 220.00, "brightness": 0.65, "swing": 0.05},
}
# pentatonic degrees (semitone offsets from root)
_PENTA = [0, 2, 4, 7, 9, 12, 14]
# I V vi IV as chord tone offsets
_PROGRESSION = [[0, 4, 7], [7, 11, 14], [9, 12, 16], [5, 9, 12]]


def _note(freq: float, dur: float, brightness: float) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = np.exp(-t * 6.5)
    sig = (np.sin(2 * np.pi * freq * t)
           + 0.4 * brightness * np.sin(2 * np.pi * freq * 2 * t)
           + 0.18 * brightness * np.sin(2 * np.pi * freq * 3 * t)
           + 0.08 * brightness * np.sin(2 * np.pi * freq * 4.01 * t))
    return sig * env


def _pad(freqs: list[float], dur: float) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        out += np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * (f * 1.003) * t)
    # slow in/out
    env = np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 1.2)
    return out * np.clip(env, 0, 1) / max(1, len(freqs))


def _kick(dur: float = 0.18) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 120 * np.exp(-t * 24) + 50
    phase = np.cumsum(f) / SR
    return np.sin(2 * np.pi * phase) * np.exp(-t * 14)


def _hat(dur: float = 0.05, seed: int = 1) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    sig = rng.standard_normal(n)
    # crude highpass: difference
    sig = np.diff(sig, prepend=0.0)
    t = np.arange(n) / SR
    return sig * np.exp(-t * 90)


def _st(freq_root: float, semis: float) -> float:
    return freq_root * (2 ** (semis / 12))


def _mix(track: np.ndarray, segment: np.ndarray, start_sec: float,
         gain: float = 1.0) -> None:
    """Bounds-safe additive mixing into a timeline track."""
    i0 = int(start_sec * SR)
    if i0 >= len(track):
        return
    end = min(len(track), i0 + len(segment))
    track[i0:end] += segment[: end - i0] * gain


class LocalMusicProvider:
    name = "local"
    label = "Built-in Composer (offline)"
    requires_key = False
    CREDITS = "AI Kids Video Studio Music Box (original, royalty-free)"

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.options = options or {}

    def generate_track(self, mood: str, duration: float, out_path: str) -> MusicResult:
        cfg = _MOODS.get(mood, _MOODS["cheerful"])
        bpm, root = cfg["bpm"], cfg["root"]
        beat = 60.0 / bpm
        bar = beat * 4
        loop_len = bar * 4  # one full progression cycle
        rng = np.random.default_rng(2024)

        loop = np.zeros(int(loop_len * SR) + SR)
        # ---- marimba melody: playful 8ths with rests -------------------
        step = beat / 2
        melody_deg = 0
        for bar_i in range(4):
            chord = _PROGRESSION[bar_i]
            for step_i in range(8):
                t = bar_i * bar + step_i * step + (cfg["swing"] * (step_i % 2))
                if rng.random() < 0.22 and step_i != 0:
                    continue
                if step_i % 2 == 0 and rng.random() < 0.55:
                    semi = chord[int(rng.integers(0, 3))] + 12
                else:
                    melody_deg += int(rng.integers(-2, 3))
                    semi = _PENTA[melody_deg % len(_PENTA)] + 12
                _mix(loop, _note(_st(root, semi), 0.42, cfg["brightness"]), t, 0.5)
        # ---- pad --------------------------------------------------------
        for bar_i in range(4):
            chord = _PROGRESSION[bar_i]
            _mix(loop, _pad([_st(root / 2, s) for s in chord], bar), bar_i * bar, 0.16)
        # ---- bass -------------------------------------------------------
        for bar_i in range(4):
            _mix(loop, _note(_st(root / 2, _PROGRESSION[bar_i][0]), beat * 1.6, 0.6),
                 bar_i * bar, 0.34)
        # ---- hats -------------------------------------------------------
        for bar_i in range(4):
            for step_i in range(1, 8, 2):
                _mix(loop, _hat(0.05, seed=bar_i * 8 + step_i),
                     bar_i * bar + step_i * step, 0.06)
        # ---- soft kick on beat 1 ---------------------------------------
        for bar_i in range(4):
            _mix(loop, _kick(), bar_i * bar, 0.25)

        # ---- tile the loop ----------------------------------------------
        total = int(duration * SR) + SR
        tile_unit = loop[: int(loop_len * SR)]
        reps = int(math.ceil(total / len(tile_unit)))
        out = np.tile(tile_unit, reps)[:total]
        # gentle master: normalize quiet, fade in/out
        peak = np.max(np.abs(out)) or 1.0
        out = out / peak
        fade_in = np.minimum(1, np.arange(total) / (1.2 * SR))
        fade_out = np.minimum(1, (total - np.arange(total)) / (1.8 * SR))
        out = out * fade_in * fade_out * 0.32
        pcm = (np.clip(out, -1, 1) * 32767).astype(np.int16)
        with wave.open(out_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SR)
            wf.writeframes(pcm.tobytes())
        return MusicResult(path=out_path, duration=duration, credits=self.CREDITS)
