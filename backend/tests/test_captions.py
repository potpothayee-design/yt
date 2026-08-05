"""Caption chunking + serialization tests."""

from app.services.providers.base import WordTiming
from app.services.rendering.captions import build_cues, offset_words, to_ass, to_srt

_WORDS = [
    "Hi", "there", "explorer", "today", "we", "are", "learning",
    "about", "colors", "and", "it", "is", "going", "to", "be", "amazing",
]
WORDS = [
    WordTiming(word=w, start=i * 0.32, end=(i + 1) * 0.32 - 0.02)
    for i, w in enumerate(_WORDS)
]


def test_cue_chunking_limits():
    cues = build_cues(WORDS)
    assert cues
    for cue in cues:
        assert len(cue.words) <= 6
        assert cue.end - cue.start <= 4.0
    # full coverage, in order
    flat = [w.word for cue in cues for w in cue.words]
    assert flat == [w.word for w in WORDS]


def test_offset():
    shifted = offset_words(WORDS, 2.5)
    assert shifted[0].start == WORDS[0].start + 2.5


def test_srt_format():
    srt = to_srt(build_cues(WORDS))
    assert "1\n00:00:00,000 --> " in srt
    assert "-->" in srt
    assert "Hi there explorer" in srt


def test_ass_karaoke():
    ass = to_ass(build_cues(WORDS), play_res_x=1280, play_res_y=720)
    assert "[V4+ Styles]" in ass
    assert "{\\k" in ass          # karaoke tags present
    assert "Dialogue: 0,0:00:00.00" in ass
