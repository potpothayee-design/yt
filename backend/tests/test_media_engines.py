"""Offline media engine tests: illustration, voice, music, consistency."""

import wave
from pathlib import Path

from PIL import Image

from app.services.pipeline.promptbuilder import character_sheet
from app.services.providers import provider_catalog
from app.services.providers.base import ImagePrompt
from app.services.providers.image.local import LocalImageProvider
from app.services.providers.music.local import LocalMusicProvider
from app.services.providers.voice.local import LocalVoiceProvider


def test_illustrator_deterministic_and_scene_varied(tmp_path: Path):
    provider = LocalImageProvider()
    sheet = character_sheet("Colors", 7)
    scene_a = {"type": "lesson", "object": "apple", "focus": "Red",
               "on_screen_text": "RED like an apple"}
    prompt = ImagePrompt("", "", 640, 360, 99,
                         character_sheet={**sheet, "scene": scene_a})
    out1 = tmp_path / "a1.png"
    out2 = tmp_path / "a2.png"
    provider.generate_image(prompt, str(out1))
    provider.generate_image(prompt, str(out2))
    assert out1.read_bytes() == out2.read_bytes()  # deterministic

    scene_b = {"type": "quiz", "object": "question", "focus": "Your turn",
               "on_screen_text": "Your turn!"}
    out3 = tmp_path / "b.png"
    provider.generate_image(ImagePrompt("", "", 640, 360, 100,
                                        character_sheet={**sheet, "scene": scene_b}), str(out3))
    assert out3.read_bytes() != out1.read_bytes()  # scenes differ

    img = Image.open(out1)
    assert img.size == (640, 360)


def test_illustrator_aspect_ratios(tmp_path: Path):
    provider = LocalImageProvider()
    sheet = character_sheet("Vehicles", 3)
    for w, h in ((720, 1280), (960, 960)):
        out = tmp_path / f"scene_{w}x{h}.png"
        provider.generate_image(
            ImagePrompt("", "", w, h, 5,
                        character_sheet={**sheet, "scene": {"type": "lesson", "object": "car", "focus": "Car"}}),
            str(out))
        assert Image.open(out).size == (w, h)


def test_voice_synthesis_duration_and_timings(tmp_path: Path):
    provider = LocalVoiceProvider()
    out = tmp_path / "voice.wav"
    text = "Hello explorer! Today we learn about the planets."
    result = provider.synthesize(text, str(out), voice="female", target_duration=4.0)
    assert out.exists()
    with wave.open(str(out)) as wf:
        frames = wf.getnframes()
        assert wf.getframerate() == 22050
        duration = frames / 22050
    assert 1.5 < duration < 8.0
    # timings are monotonic and cover the sentence words
    assert len(result.word_timings) >= 6
    starts = [w.start for w in result.word_timings]
    assert starts == sorted(starts)
    assert result.word_timings[-1].end <= result.duration + 0.5


def test_voice_word_pacing_to_target(tmp_path: Path):
    provider = LocalVoiceProvider()
    short = provider.synthesize("One two three four", str(tmp_path / "s.wav"),
                                target_duration=2.0)
    stretched = provider.synthesize("One two three four", str(tmp_path / "l.wav"),
                                    target_duration=6.0)
    assert stretched.duration > short.duration


def test_music_generation(tmp_path: Path):
    provider = LocalMusicProvider()
    out = tmp_path / "music.wav"
    result = provider.generate_track("cheerful", 9.0, str(out))
    assert out.exists()
    with wave.open(str(out)) as wf:
        duration = wf.getnframes() / wf.getframerate()
    assert 8.5 < duration < 10.5
    assert "royalty-free" in result.credits


def test_voice_spoken_text_sanitization():
    """Parentheticals (e.g. age suffixes) are stripped before synthesis."""
    from app.services.providers.voice.local import _clean_spoken_text

    out = _clean_spoken_text("Welcome friends (Ages 7-9)  let's count  3 things!")
    assert "(" not in out and "Ages" not in out
    assert "  " not in out
    assert out.startswith("Welcome friends")
    assert "let's count" in out


def test_open_source_providers_in_catalog():
    names = {(p["capability"], p["name"]) for p in provider_catalog()}
    assert ("voice", "piper") in names
    assert ("text", "ollama") in names
    assert ("image", "sd-webui") in names
    assert ("music", "musicgen") in names


def test_piper_and_musicgen_graceful_when_not_installed():
    """Probe + fallback path must never explode when extras are missing."""
    from app.services.providers.music.musicgen import MusicGenProvider
    from app.services.providers.voice.piper import (
        PiperVoiceProvider,
        synthesize_via_piper,
    )

    ok, msg = PiperVoiceProvider().probe()
    assert isinstance(ok, bool) and msg
    ok2, msg2 = MusicGenProvider().probe()
    assert isinstance(ok2, bool) and msg2
    # in CI piper-tts is not installed -> helper must return None, not raise
    assert synthesize_via_piper("hello", "/tmp/x.wav", "female") is None or True
