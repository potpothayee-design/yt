"""Built-in offline voice provider.

Resolution order (automatic):

1. ``espeak``/``espeak-ng`` if present (Linux distros, Termux...)
2. **System TTS**: Windows SAPI (Microsoft voices via PowerShell) or macOS
   ``say`` — genuinely intelligible, installed by default on those OSes
3. Compact formant synthesizer as the universal fallback ("electronic
   storyteller" character designed for predictable timing)

All tiers fill the same ``VoiceResult`` contract (path, duration, per-word
timings) so karaoke captions stay aligned. For production-quality narration,
select OpenAI TTS, ElevenLabs or Google Cloud TTS on the API Keys page.
"""

from __future__ import annotations

import base64
import math
import re
import shutil
import subprocess
import sys
import wave
from dataclasses import dataclass

import numpy as np
from scipy.signal import lfilter

from app.services.providers.base import VoiceResult, WordTiming

SAMPLE_RATE = 22050

# Grapheme -> phoneme rules (longest match first within a word)
_DIGRAPHS = {
    "sh": "SH", "ch": "CH", "th": "TH", "ph": "F", "ng": "NG", "wh": "W",
    "ee": "IY", "ea": "IY", "ai": "EY", "ay": "EY", "oa": "OW", "ow": "AW",
    "ou": "AW", "oo": "UW", "oi": "OY", "oy": "OY", "ar": "AR",
    "er": "ER", "or": "OR", "ur": "ER", "ir": "ER", "ck": "K", "qu": "KW",
    "igh": "AY",
}
_LETTERS = {
    "a": "AA", "b": "B", "c": "K", "d": "D", "e": "EH", "f": "F", "g": "G",
    "h": "HH", "i": "IH", "j": "JH", "k": "K", "l": "L", "m": "M", "n": "N",
    "o": "OW", "p": "P", "q": "KW", "r": "R", "s": "S", "t": "T", "u": "AH",
    "v": "V", "w": "W", "x": "KS", "y": "Y", "z": "Z",
}
_SILENT_E = re.compile(r"e$")

# formants: (F1 Hz, F2 Hz, bandwidth) | voiced?
_VOWELS = {
    "AA": (730, 1090), "AE": (660, 1720), "AH": (520, 1190), "AO": (570, 840),
    "EH": (530, 1840), "ER": (490, 1350), "IH": (390, 1990), "IY": (270, 2290),
    "OW": (450, 800), "UH": (440, 1020), "UW": (300, 870), "EY": (400, 2000),
    "AY": (700, 1800), "AW": (600, 1200), "OY": (400, 1900), "AR": (690, 1660),
    "OR": (500, 1000),
}
_VOICED_CONS = {"M": (200, 900), "N": (250, 1400), "NG": (230, 2000),
                "L": (360, 1300), "R": (400, 1300), "W": (300, 610),
                "Y": (250, 2200), "V": (220, 1100), "Z": (240, 2100)}
_NOISE_CONS = {  # center freq, bandwidth
    "S": (6500, 3000), "SH": (2600, 1500), "F": (4500, 3500), "TH": (6000, 4000),
    "HH": (1500, 3000), "K": (1800, 2500), "P": (900, 1500), "T": (4500, 4000),
    "CH": (3000, 2000), "JH": (2500, 1800), "B": (800, 1200), "D": (1600, 2200),
    "G": (1400, 2000), "KS": (5500, 3500), "KW": (1100, 1800),
}


@dataclass
class _Unit:
    kind: str          # vowel | vcons | ncons | pause
    label: str
    dur: float         # seconds (natural)


def _word_to_units(word: str) -> list[_Unit]:
    w = re.sub(r"[^a-z']", "", word.lower())
    if not w:
        return []
    phones: list[str] = []
    i = 0
    while i < len(w):
        matched = False
        for n in (3, 2):
            chunk = w[i:i + n]
            if chunk in _DIGRAPHS:
                phones.append(_DIGRAPHS[chunk])
                i += n
                matched = True
                break
        if matched:
            continue
        phones.append(_LETTERS.get(w[i], ""))
        i += 1
    return [_unit_for(p) for p in phones if p]


def _unit_for(ph: str) -> _Unit:
    if ph in _VOWELS:
        return _Unit("vowel", ph, 0.105)
    if ph in _VOICED_CONS:
        return _Unit("vcons", ph, 0.065)
    if ph in _NOISE_CONS:
        return _Unit("ncons", ph, 0.07 if ph not in ("K", "P", "T", "B", "D", "G") else 0.055)
    return _Unit("pause", ph, 0.02)


def _resonator(x: np.ndarray, freq: float, bw: float, sr: int) -> np.ndarray:
    r = math.exp(-math.pi * bw / sr)
    w = 2 * math.pi * freq / sr
    return lfilter([1.0 - r], [1.0, -2 * r * math.cos(w), r * r], x)


def _voiced(dur: float, f0: np.ndarray, f1: float, f2: float, sr: int) -> np.ndarray:
    n = max(8, int(dur * sr))
    phase = np.cumsum(f0) / sr
    t = np.arange(n)
    # harmonic source (mellow triangle-ish buzz)
    sig = (np.sin(2 * np.pi * phase)
           + 0.45 * np.sin(4 * np.pi * phase)
           + 0.20 * np.sin(6 * np.pi * phase)
           + 0.10 * np.sin(8 * np.pi * phase))
    out = _resonator(sig, f1, 110, sr) + 0.65 * _resonator(sig, f2, 140, sr)
    env = np.minimum(1.0, t / (0.018 * sr)) * np.minimum(1.0, (n - 1 - t) / (0.03 * sr))
    return out * np.clip(env, 0, 1)


def _noise(dur: float, f0: float, f1: float, f2: float, sr: int, rng: np.random.Generator) -> np.ndarray:
    n = max(8, int(dur * sr))
    sig = rng.standard_normal(n)
    out = _resonator(sig, f1, max(200, f2 - f1), sr) + 0.5 * _resonator(sig, f2, 900, sr)
    if f0 > 0:  # voiced fricative — add buzz
        phase = np.cumsum(np.full(n, f0)) / sr
        out += 0.25 * _resonator(np.sin(2 * np.pi * phase), 300, 150, sr)
    t = np.arange(n)
    env = np.minimum(1.0, t / (0.008 * sr)) * np.minimum(1.0, (n - 1 - t) / (0.02 * sr))
    return out * np.clip(env, 0, 1)


class LocalVoiceProvider:
    name = "local"
    label = "Built-in Voice (offline)"
    requires_key = False

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.options = options or {}

    # ------------------------------------------------------------------
    def synthesize(self, text: str, out_path: str, *, voice: str = "female",
                   language: str = "en", target_duration: float | None = None) -> VoiceResult:
        text = _clean_spoken_text(text)
        espeak = shutil.which("espeak") or shutil.which("espeak-ng")
        if espeak:
            result = self._synthesize_espeak(espeak, text, out_path, voice, target_duration)
            if result:
                return result
        if language == "en":
            # Piper neural TTS (optional pip package) — best offline quality
            from app.services.providers.voice.piper import synthesize_via_piper

            result = synthesize_via_piper(text, out_path, voice)
            if result:
                return result
            result = self._synthesize_system(text, out_path, voice)
            if result:
                return result
        return self._synthesize_formant(text, out_path, voice, target_duration)

    # ------------------------------------------------------------------
    def _synthesize_system(self, text: str, out_path: str, voice: str) -> VoiceResult | None:
        """Human-sounding offline TTS that ships with the OS (Windows/macOS)."""
        if sys.platform == "win32":
            return self._synthesize_sapi(text, out_path, voice)
        if sys.platform == "darwin":
            return self._synthesize_say(text, out_path)
        return None

    def _synthesize_sapi(self, text: str, out_path: str, voice: str) -> VoiceResult | None:
        """Windows Speech API — natural Microsoft voices, no install needed.

        Text is passed base64-encoded so quoting/punctuation cannot break the
        PowerShell command line.
        """
        powershell = shutil.which("powershell") or shutil.which("powershell.exe")
        if not powershell:
            return None
        gender = "Male" if voice == "male" else "Female"
        age_hint = "Child" if voice == "child" else "Adult"
        b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::{gender}, "
            f"[System.Speech.Synthesis.VoiceAge]::{age_hint}); "
            "$s.Rate = -1; "
            f"$s.SetOutputToWaveFile('{out_path}'); "
            f"$t = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('{b64}')); "
            "$s.Speak($t); $s.Dispose();"
        )
        try:
            subprocess.run([powershell, "-NoProfile", "-NonInteractive", "-Command", script],
                           check=True, capture_output=True, timeout=180)
            return _result_from_wav(text, out_path)
        except Exception:
            return None

    def _synthesize_say(self, text: str, out_path: str) -> VoiceResult | None:
        """macOS `say` command via the bundled ffmpeg for aiff -> wav."""
        say = shutil.which("say")
        if not say:
            return None
        from app.services.rendering.ffmpeg_utils import run_ffmpeg

        tmp = out_path + ".aiff"
        try:
            subprocess.run([say, "-o", tmp, text], check=True, capture_output=True, timeout=180)
            run_ffmpeg(["-y", "-i", tmp, out_path], timeout=120)
            return _result_from_wav(text, out_path)
        except Exception:
            return None

    # ------------------------------------------------------------------
    def _synthesize_formant(self, text: str, out_path: str, voice: str,
                            target_duration: float | None) -> VoiceResult:
        sr = SAMPLE_RATE
        rng = np.random.default_rng(7)
        base_f0 = 285.0 if voice != "male" else 210.0

        tokens = re.findall(r"[A-Za-z']+|[\d]+|[.!?,;:]", text)
        words: list[tuple[str, list[_Unit], str]] = []  # (word, units, trailing punct)
        for tok in tokens:
            if re.fullmatch(r"[.!?,;:]", tok) and words:
                w, u, p = words[-1]
                words[-1] = (w, u, p + tok)
            elif re.fullmatch(r"[\d]+", tok):
                expanded = _speak_number(tok)
                words.append((tok, _word_to_units(expanded), ""))
            else:
                words.append((tok, _word_to_units(tok), ""))

        natural = 0.0
        for _w, units, punct in words:
            natural += sum(u.dur for u in units) + 0.045
            natural += 0.16 if "," in punct else (
                0.26 if any(c in punct for c in (".", "!", "?")) else 0.0
            )
        scale = 1.0
        if target_duration and natural > 0:
            # honor the planned scene slot within natural-sounding limits;
            # remaining slack is padded with silence by the composer
            scale = float(np.clip(target_duration / natural, 0.65, 2.2))

        audio_parts: list[np.ndarray] = []
        timings: list[WordTiming] = []
        cursor = 0.0
        sentence_t = 0  # position in sentence for pitch contour
        for word, units, punct in words:
            is_question = "?" in punct
            word_start = cursor
            wlen = max(1, sum(u.dur for u in units) * scale)
            for ui, unit in enumerate(units):
                dur = unit.dur * scale
                n = max(8, int(dur * sr))
                tt = np.linspace(0, 1, n)
                # pitch: gentle arc per word; rise at sentence end for questions
                contour = 1.0 + 0.06 * math.sin(math.pi * (sentence_t + tt[0] * 0.5))
                if is_question:
                    contour *= 1.0 + 0.12 * (ui / max(1, len(units) - 0.001))
                elif any(c in punct for c in ".!"):
                    contour *= 1.0 - 0.08 * (ui / max(1, len(units) - 0.001))
                f0 = base_f0 * contour * (1 + 0.015 * np.sin(2 * math.pi * 5.2 * tt * dur))
                f0 = np.full(n, f0 if np.isscalar(f0) else f0.mean())
                if unit.kind == "vowel":
                    f1, f2 = _VOWELS[unit.label]
                    seg = _voiced(dur, f0, f1, f2, sr) * 1.15
                elif unit.kind == "vcons":
                    f1, f2 = _VOICED_CONS[unit.label]
                    seg = _voiced(dur, f0, f1, f2, sr) * 0.8
                elif unit.kind == "ncons":
                    f1, f2 = _NOISE_CONS[unit.label]
                    voiced = unit.label in ("V", "Z", "B", "D", "G", "JH")
                    seg = _noise(dur, f0[-1] if voiced else 0.0, f1, f2, sr, rng) * 0.55
                else:
                    seg = np.zeros(n)
                audio_parts.append(seg.astype(np.float64))
                cursor += dur
            gap = 0.045 * scale
            audio_parts.append(np.zeros(int(gap * sr)))
            cursor += gap
            if punct:
                pdur = (0.17 if "," in punct else 0.27) * scale
                audio_parts.append(np.zeros(int(pdur * sr)))
                cursor += pdur
                sentence_t = 0
            else:
                sentence_t += wlen / max(0.3, natural)
            timings.append(WordTiming(word=word, start=round(word_start, 3),
                                      end=round(cursor, 3)))

        audio = np.concatenate(audio_parts) if audio_parts else np.zeros(sr)
        audio = np.tanh(audio * 1.6)
        peak = np.max(np.abs(audio)) or 1.0
        audio = audio / peak * 0.72
        if target_duration:  # final trim/pad to respect the requested slot
            want = int(min(target_duration * 1.08, cursor) * sr)
            audio = audio[:want] if len(audio) > want else np.pad(audio, (0, want - len(audio)))
        _write_wav(out_path, audio, sr)
        return VoiceResult(path=out_path, duration=len(audio) / sr, word_timings=timings)

    # ------------------------------------------------------------------
    def _synthesize_espeak(self, binary: str, text: str, out_path: str,
                           voice: str, target_duration: float | None) -> VoiceResult | None:
        try:
            args = [binary, "-w", out_path, "-s", "155", "-p", "62"]
            if voice == "male":
                args += ["-v", "en+m2"]
            else:
                args += ["-v", "en+f3"]
            args.append(text)
            subprocess.run(args, check=True, capture_output=True, timeout=120)
            with wave.open(out_path, "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
            dur = frames / float(rate)
            words = re.findall(r"[A-Za-z']+|\d+", text)
            timings = _spread_timings(words, dur)
            return VoiceResult(path=out_path, duration=dur, word_timings=timings)
        except Exception:
            return None


def _clean_spoken_text(text: str) -> str:
    """Strip anything that must never be spoken aloud.

    Parenthetical fragments — e.g. "(Ages 7-9)" — are visual/SEO metadata;
    narration must never read them out. Also collapses stray whitespace.
    """
    cleaned = re.sub(r"\s*\([^)]*\)", " ", text)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def _result_from_wav(text: str, out_path: str) -> VoiceResult | None:
    """Build a VoiceResult from an externally-produced wav (proportional timings)."""
    import contextlib

    with contextlib.suppress(OSError):
        with wave.open(out_path, "rb") as wf:
            if wf.getnframes() == 0:
                return None
            dur = wf.getnframes() / float(wf.getframerate())
        words = re.findall(r"[A-Za-z']+|\d+", text)
        timings = _spread_timings(words, dur)
        return VoiceResult(path=out_path, duration=dur, word_timings=timings)
    return None


def _spread_timings(words: list[str], total: float) -> list[WordTiming]:
    """Estimate word timings proportionally to word length (fallback path)."""
    weights = [max(1.5, len(w)) + 1.0 for w in words]
    total_w = sum(weights) or 1.0
    t = 0.0
    out: list[WordTiming] = []
    for w, wt in zip(words, weights, strict=True):
        d = total * wt / total_w
        out.append(WordTiming(word=w, start=round(t, 3), end=round(t + d, 3)))
        t += d
    return out


def _speak_number(num: str) -> str:
    """Convert a number to speakable English words (supports 0–999)."""
    ones = ["zero", "one", "two", "three", "four", "five", "six", "seven",
            "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
            "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    n = int(num)
    if n < 20:
        return ones[n]
    if n < 100:
        return tens[n // 10] + ((" " + ones[n % 10]) if n % 10 else "")
    head = ones[n // 100] + " hundred"
    return head + ((" " + _speak_number(str(n % 100))) if n % 100 else "")


def _write_wav(path: str, audio: np.ndarray, sr: int) -> None:
    pcm = (audio * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
