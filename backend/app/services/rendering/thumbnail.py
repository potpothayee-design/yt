"""Thumbnail concept generator.

Produces several high-contrast, large-subject, minimal-text thumbnail
concepts optimized for readability at small sizes (the CTR playbook):
bright background frame, giant title text with heavy outline, the mascot
front and center, and a color accent banner.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from app.services.providers.image.character import draw_mascot, hex_to_rgb, shade
from app.services.rendering.fonts import (
    clean_text,
    draw_text_center,
    get_font,
    text_size,
)

_BG = [("#FF6B6B", "#FFD93D"), ("#4D96FF", "#8ED6FF"), ("#6BCB77", "#C9F299"),
       ("#9B72CF", "#E5C3FF")]
_ACCENTS = ["#FFD93D", "#FF6B6B", "#FFFFFF", "#4D96FF"]


def generate_thumbnails(base_image: str | None, title: str, sheet: dict,
                        out_dir: str, *, width: int = 1280, height: int = 720,
                        count: int = 3) -> list[str]:
    """Render ``count`` thumbnail concepts; returns their paths."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    words = clean_text(title).split()
    paths: list[str] = []

    for v in range(count):
        bg_top, bg_bottom = _BG[v % len(_BG)]
        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)
        top, bot = hex_to_rgb(bg_top), hex_to_rgb(bg_bottom)
        for y in range(height):
            t = y / height
            draw.line([(0, y), (width, y)],
                      fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))

        # rays behind subject (variant dependent)
        if v % 2 == 0:
            for i in range(0, 360, 20):
                import math
                x2 = width * 0.70 + width * math.cos(math.radians(i))
                y2 = height * 0.52 + width * math.sin(math.radians(i))
                draw.line([(width * 0.70, height * 0.52), (x2, y2)],
                          fill=shade(bg_top, 1.25), width=int(width * 0.035))

        accent = _ACCENTS[v % len(_ACCENTS)]
        # giant subject: the mascot, right side, oversized
        draw_mascot(draw, sheet, width * 0.72, height * 0.52, min(width, height) * 0.62,
                    expression="excited", wave=True)

        # bold outlined title, left aligned, stacked lines of <=2 words
        size = int(height * 0.13)
        font = get_font(size)
        lines: list[str] = []
        cur = ""
        for w in words[:6]:
            trial = (cur + " " + w).strip()
            if text_size(draw, trial.upper(), font)[0] > width * 0.52 and cur:
                lines.append(cur.upper())
                cur = w
            else:
                cur = trial
        if cur:
            lines.append(cur.upper())
        lines = lines[:3]
        y = height * 0.5 - (len(lines) * size * 1.12) / 2
        for line in lines:
            draw_text_center(draw, (width * 0.28, y), line, font,
                             fill="#FFFFFF", stroke="#2B2B3A",
                             stroke_width=max(4, size // 9))
            y += size * 1.12

        # accent banner bottom-left: "AGES 3-6"-style chip slot / brand mark
        chip_w, chip_h = width * 0.30, height * 0.105
        draw.rounded_rectangle([width * 0.04, height * 0.85, width * 0.04 + chip_w,
                                height * 0.85 + chip_h], radius=chip_h / 2, fill=accent)
        small = get_font(int(chip_h * 0.48))
        draw_text_center(draw, (width * 0.04 + chip_w / 2, height * 0.85 + chip_h / 2),
                         "FUN LEARNING!", small,
                         fill="#2B2B3A" if accent != "#2B2B3A" else "#FFFFFF")

        out = str(Path(out_dir) / f"thumbnail_{v + 1}.jpg")
        img.save(out, "JPEG", quality=92)
        paths.append(out)
    return paths
