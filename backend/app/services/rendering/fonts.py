"""Font discovery and text-drawing helpers shared by all renderers.

Resolution order:
1. ``STUDIO_FONT`` env override
2. Common bundled/system font locations (DejaVu ships with most Linux
   distros, python:slim images and matplotlib)
3. Pillow's built-in scalable ``load_default`` (always available)
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from PIL import ImageDraw, ImageFont

FONT_SEARCH_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def _matplotlib_font() -> str | None:
    try:
        import matplotlib
        base = Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf"
        for name in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
            if (base / name).exists():
                return str(base / name)
    except Exception:
        return None
    return None


@lru_cache(maxsize=1)
def find_font_file() -> str | None:
    override = os.environ.get("STUDIO_FONT")
    if override and Path(override).exists():
        return override
    for path in FONT_SEARCH_PATHS:
        if Path(path).exists():
            return path
    return _matplotlib_font()


@lru_cache(maxsize=64)
def get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    path = find_font_file()
    if path:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=max(12, size))
    except TypeError:  # very old Pillow
        return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font, stroke_width=0)
    return box[2] - box[0], box[3] - box[1]


def clean_text(text: str) -> str:
    """Strip characters the renderer can't draw (color emoji etc.).

    Emojis are kept in YouTube titles/descriptions (they render there), but
    the bundled bitmap renderer has no color-emoji glyphs — so for pixels we
    drop astral-plane characters.
    """
    return "".join(ch for ch in text if ord(ch) < 0x2FFF).strip()


def draw_text_center(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    font,
    fill: str = "#FFFFFF",
    stroke: str | None = None,
    stroke_width: int = 0,
) -> None:
    w, h = text_size(draw, text, font)
    draw.text(
        (xy[0] - w / 2, xy[1] - h / 2), text, font=font, fill=fill,
        stroke_width=stroke_width, stroke_fill=stroke,
    )


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    """Greedy word wrap measured against the actual font."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if text_size(draw, trial, font)[0] <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
