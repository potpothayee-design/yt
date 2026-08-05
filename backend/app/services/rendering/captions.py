"""Subtitle generation: cue chunking, SRT, ASS (karaoke highlighting).

Cues are built from per-word narration timings (absolute timeline) and laid
out for readability: max 6 words or 2 lines, max ~3.4 s per cue, splitting on
punctuation when possible.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.providers.base import WordTiming

MAX_WORDS_PER_CUE = 6
MAX_CUE_SECONDS = 3.4


@dataclass
class Cue:
    start: float
    end: float
    words: list[WordTiming] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(w.word for w in self.words)


def build_cues(words: list[WordTiming]) -> list[Cue]:
    """Chunk word timings into display cues."""
    cues: list[Cue] = []
    current: list[WordTiming] = []
    cue_start = 0.0
    for w in words:
        if not current:
            cue_start = w.start
        current.append(w)
        long_enough = w.end - cue_start >= MAX_CUE_SECONDS
        full = len(current) >= MAX_WORDS_PER_CUE
        hard_break = w.word.endswith((".", "!", "?"))
        if long_enough or full or hard_break:
            cues.append(Cue(start=cue_start, end=w.end + 0.12, words=list(current)))
            current = []
    if current:
        cues.append(Cue(start=cue_start, end=current[-1].end + 0.12, words=list(current)))
    return cues


def offset_words(words: list[WordTiming], offset: float) -> list[WordTiming]:
    return [WordTiming(word=w.word, start=w.start + offset, end=w.end + offset)
            for w in words]


# ---------------------------------------------------------------------------
# SRT / ASS serialization
# ---------------------------------------------------------------------------

def _ts_srt(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _ts_ass(t: float) -> str:
    cs = int(round(t * 100))
    h, cs = divmod(cs, 3600_00)
    m, cs = divmod(cs, 60_00)
    s, cs = divmod(cs, 100)
    return f"{h:01d}:{m:02d}:{s:02d}.{cs:02d}"


def to_srt(cues: list[Cue]) -> str:
    blocks = []
    for i, cue in enumerate(cues, 1):
        blocks.append(
            f"{i}\n{_ts_srt(cue.start)} --> {_ts_srt(cue.end)}\n{cue.text}\n"
        )
    return "\n".join(blocks)


_ASS_FIELDS = (
    "Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
    "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, "
    "Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, "
    "Encoding"
)


def to_ass(cues: list[Cue], *, play_res_x: int = 1280, play_res_y: int = 720,
           font: str = "DejaVu Sans", font_size: int = 52,
           highlight: str = "&H0000D7FF") -> str:
    """ASS with karaoke word highlighting (\\k tags)."""
    style_values = (
        f"Default,{font},{font_size},&H00FFFFFF,{highlight},&H002B2B3A,"
        f"&H96000000,1,0,0,0,100,100,0,0,3,6,0,2,40,40,{int(play_res_y * 0.08)},1"
    )
    header = (
        "[Script Info]\n"
        "Title: AI Kids Video Studio captions\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {play_res_x}\n"
        f"PlayResY: {play_res_y}\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        f"Format: {_ASS_FIELDS}\n"
        f"Style: {style_values}\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    lines = [header]
    for cue in cues:
        kar = "".join(
            f"{{\\k{max(1, int((w.end - w.start) * 100))}}}{w.word} " for w in cue.words
        ).strip()
        lines.append(
            f"Dialogue: 0,{_ts_ass(cue.start)},{_ts_ass(cue.end)},Default,,0,0,0,,{kar}"
        )
    return "\n".join(lines) + "\n"
