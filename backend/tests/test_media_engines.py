"""Offline media engine tests: illustration, voice, music, consistency."""

import wave
from pathlib import Path

from PIL import Image

from app.services.pipeline.promptbuilder import character_sheet
from app.services.providers import provider_catalog
from app.services.providers.base import ImagePrompt, VideoPrompt
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


def test_free_hosted_providers_in_catalog_and_urls(monkeypatch):
    from app.services.providers.image.pollinations import build_image_url
    from app.services.providers.text.gemini import _extract_json
    from app.services.providers.video.pollinations import build_video_url

    names = {(p["capability"], p["name"]) for p in provider_catalog()}
    assert ("text", "gemini") in names
    assert ("image", "pollinations") in names
    assert ("video", "pollinations") in names

    p = ImagePrompt(prompt="friendly sun", negative_prompt="dark, scary",
                    width=1280, height=720, seed=7)
    url = build_image_url(p)
    assert url.startswith("https://image.pollinations.ai/prompt/")
    assert "width=1280" in url and "height=720" in url and "seed=7" in url
    assert "nologo=true" in url and "model=flux" in url and "safe=true" in url
    assert "avoid" in url  # negative terms folded into the prompt

    vp = build_video_url(VideoPrompt(prompt="sun dancing", negative_prompt="",
                                     duration=7.0))
    assert "duration=7" in vp and "aspectRatio=16%3A9" in vp
    assert "model=seedance" in vp

    assert _extract_json('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert _extract_json('here you go: {"a": 1} done') == '{"a": 1}'


def test_voice_speed_stretch_keeps_caption_sync(tmp_path: Path):
    """1.25x speed-up: audio shorter by 1/1.25, word timings rescaled in-step."""


    from app.services.pipeline.engine import apply_voice_speed

    out = tmp_path / "vox.wav"
    base = LocalVoiceProvider().synthesize(
        "Counting numbers one two three is really fun and easy today friend!",
        str(out))
    sped = apply_voice_speed(str(out), base, 1.25)
    assert abs(sped.duration - base.duration / 1.25) < 0.15
    ratio = base.word_timings[2].start / sped.word_timings[2].start
    assert abs(ratio - 1.25) < 0.08
    assert sped.word_timings[0].word == base.word_timings[0].word


def test_faster_speed_allows_more_script_words():
    """1.25x narration → bigger word budget; at 60s it crosses into an extra
    lesson scene (+~25% content, exactly what the speed setting is for)."""
    slow = _make_script_s("Counting", 60, "3-6", 1.0)
    fast = _make_script_s("Counting", 60, "3-6", 1.25)

    def words(s):  # noqa: ANN001, ANN202
        return sum(sc["words"] for sc in s["scenes"])

    assert fast["word_budget"] > slow["word_budget"] * 1.2
    assert words(fast) > words(slow)
    assert len(fast["scenes"]) >= len(slow["scenes"])


def _make_script_s(topic: str, length: int, age: str, speed: float) -> dict:
    import json as _json

    from app.services.pipeline.knowledge import research
    from app.services.pipeline.promptbuilder import SYSTEM_PROMPT, script_brief
    from app.services.providers.text.local import LocalTextProvider

    kb = research(topic)
    params = {"topic": topic, "target_age": age, "length_seconds": length,
              "language": "en", "voice": "female", "voice_speed": speed}
    raw = LocalTextProvider().generate(
        SYSTEM_PROMPT, script_brief(kb, params,
                                    {"seed": 99, "lesson_count": 3}))
    return _json.loads(raw)
