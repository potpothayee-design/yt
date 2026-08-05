"""Built-in storybook illustrator (offline image provider).

Composes full scenes with Pillow: gradient sky, layered hills, animated
props, the consistent project mascot, a large educational focal glyph, an
on-screen text banner and sparkle accents.

Everything is seeded per project so style, palette and character stay
perfectly consistent between scenes — the same contract we demand from
external image providers via character-sheet prompts.
"""

from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw

from app.services.providers.base import ImagePrompt, ImageResult
from app.services.providers.image.character import draw_mascot, hex_to_rgb
from app.services.providers.image.glyphs import (
    cloud_shape,
    draw_glyph_by_name,
    g_number,
    sparkle,
)
from app.services.rendering.fonts import draw_text_center, get_font, text_size

# Cheerful sky palettes (top, bottom) cycled by scene index
_SKIES = [
    ("#8ED6FF", "#DFF4FF"), ("#9BE7C4", "#F0FFF4"), ("#FFD9A0", "#FFF6E5"),
    ("#C3B6FF", "#F1ECFF"), ("#FFC3D9", "#FFF0F6"), ("#A0E4FF", "#EAFBFF"),
]
_HILLS = ["#8FD694", "#6BCB77"], ["#7BC96F", "#57B35C"], ["#9BD97B", "#6BCB77"]
_SCENE_EXPRESSION = {"intro": "excited", "quiz": "surprised", "fact": "surprised",
                     "outro": "excited", "lesson": "happy"}


class LocalImageProvider:
    name = "local"
    label = "Built-in Illustrator (offline)"
    requires_key = False

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.options = options or {}

    def generate_image(self, prompt: ImagePrompt, out_path: str) -> ImageResult:
        sheet = prompt.character_sheet or {}
        seed = prompt.seed
        scene = sheet.get("scene", {})  # filled by the pipeline for local renders
        rng = random.Random(seed)

        W, H = prompt.width, prompt.height
        m = min(W, H)
        img, draw = self._sky(W, H, seed)
        self._clouds(draw, rng, W, H, n=4 if W > H else 3)
        self._hills(draw, rng, W, H, seed)

        # ground shadow layer
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.ellipse([W * 0.5 - m * 0.22, H * 0.79, W * 0.5 + m * 0.22, H * 0.86], fill=(30, 60, 40, 55))
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)

        # focal educational glyph (right-of-center in wide frames, center otherwise)
        gx, gy, gs = W * 0.63, H * 0.56, m * 0.42
        if W <= H:  # portrait/square: glyph lower-center, mascot under
            gx, gy = W * 0.5, H * 0.45
        obj = scene.get("object") or "star"
        focus = scene.get("focus") or ""
        if not draw_glyph_by_name(draw, obj, gx, gy, gs, rng):
            g_number(draw, gx, gy, gs, rng, focus[:2] or "★", "#E5484D")
        # giant letter/number badge for alphabet/counting lessons
        if focus and len(focus.strip()) <= 2 and any(ch.isalnum() for ch in focus):
            bx = gx + gs * 0.62
            by = gy - gs * 0.68
            g_number(draw, bx, by, gs * 0.42, rng, focus.strip().upper(), "#E5484D")
        for _ in range(6):
            sparkle(draw, gx + rng.uniform(-1, 1) * gs * 0.95,
                    gy + rng.uniform(-1, 1) * gs * 0.9, rng.uniform(4, 10) * m / 720)

        # mascot — opposite side, consistent pose/size
        mx, my, ms = W * 0.18, H * 0.68, m * 0.34
        if W <= H:
            mx, my, ms = W * 0.28, H * 0.80, m * 0.28
        expression = _SCENE_EXPRESSION.get(scene.get("type", "lesson"), "happy")
        draw_mascot(draw, sheet, mx, my, ms, expression=expression,
                    wave=scene.get("type") in ("intro", "outro"))

        # on-screen text banner
        if scene.get("on_screen_text"):
            self._banner(draw, img, W, H, m, scene["on_screen_text"])

        # soft sparkles on the sky
        for _ in range(8):
            sparkle(draw, rng.uniform(0.05, 0.95) * W, rng.uniform(0.05, 0.42) * H,
                    rng.uniform(3, 7) * m / 720, color="#FFFFFF")

        img = img.convert("RGB")
        img.save(out_path, "PNG")
        return ImageResult(path=out_path, width=W, height=H)

    # ------------------------------------------------------------------

    @staticmethod
    def _sky(W: int, H: int, seed: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        top_h, bot_h = _SKIES[seed % len(_SKIES)]
        top, bot = hex_to_rgb(top_h), hex_to_rgb(bot_h)
        img = Image.new("RGBA", (W, H))
        draw = ImageDraw.Draw(img)
        for y in range(H):
            t = y / max(1, H - 1)
            color = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (255,)
            draw.line([(0, y), (W, y)], fill=color)
        return img, draw

    @staticmethod
    def _clouds(draw, rng: random.Random, W: int, H: int, n: int = 4) -> None:
        for _ in range(n):
            cloud_shape(draw, rng.uniform(0.1, 0.9) * W, rng.uniform(0.06, 0.3) * H,
                        rng.uniform(30, 80) * min(W, H) / 720)

    @staticmethod
    def _hills(draw, rng: random.Random, W: int, H: int, seed: int) -> None:
        near, far = _HILLS[seed % len(_HILLS)]
        base_y = H * 0.78
        # far hill
        pts_far = [(0, H)] + [
            (x, base_y + (math.sin(x / W * math.pi * 1.6 + seed) * 0.05 - 0.06) * H)
            for x in range(0, W + 1, max(8, W // 60))
        ] + [(W, H)]
        draw.polygon(pts_far, fill=far)
        # near meadow
        draw.rectangle([0, base_y + H * 0.05, W, H], fill=near)
        draw.line([0, base_y + H * 0.05, W, base_y + H * 0.05], fill=far,
                  width=max(2, int(H * 0.008)))

    @staticmethod
    def _banner(draw, img: Image.Image, W: int, H: int, m: int, text: str) -> None:
        # shrink-to-fit the banner font
        size = max(26, int(m * 0.052))
        font = get_font(size)
        tw, th = text_size(draw, text, font)
        while tw > W * 0.72 and size > 16:
            size -= 2
            font = get_font(size)
            tw, th = text_size(draw, text, font)
        pad_x, pad_y = size * 0.85, size * 0.45
        x0 = W / 2 - tw / 2 - pad_x
        y0 = H * 0.045
        box = [x0, y0, x0 + tw + pad_x * 2, y0 + th + pad_y * 2]
        # translucent rounded banner badge on an overlay layer
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rounded_rectangle(box, radius=size * 0.7, fill=(35, 38, 68, 185))
        img.paste(Image.alpha_composite(img, overlay), (0, 0))
        draw2 = ImageDraw.Draw(img)
        draw_text_center(draw2, (W / 2, y0 + (th + pad_y * 2) / 2), text, font,
                         fill="white", stroke="#1E2140", stroke_width=max(1, size // 14))


def render_intro_card(title: str, sheet: dict, W: int, H: int, out_path: str,
                      subtitle: str = "A fun learning adventure") -> None:
    """Professional branded intro card used by the composer."""
    prov = LocalImageProvider()
    prompt = ImagePrompt(prompt="", negative_prompt="", width=W, height=H,
                         seed=sheet.get("seed", 1),
                         character_sheet={**sheet, "scene": {"type": "intro", "object": "star"}})
    tmp = out_path + ".scene.png"
    prov.generate_image(prompt, tmp)
    img = Image.open(tmp).convert("RGB")
    draw = ImageDraw.Draw(img)
    m = min(W, H)
    # big colorful title, wrapped
    from app.services.rendering.fonts import (
        clean_text,
        draw_text_center,
        get_font,
        wrap_text,
    )
    size = int(m * 0.11)
    font = get_font(size)
    lines = wrap_text(draw, clean_text(title), font, int(W * 0.8))
    y = H * 0.35
    for line in lines:
        draw_text_center(draw, (W / 2, y), line, font, fill="#FFFFFF",
                         stroke="#2B2B3A", stroke_width=max(3, size // 12))
        y += size * 1.18
    small = get_font(int(m * 0.045))
    draw_text_center(draw, (W / 2, H * 0.115), "AI KIDS VIDEO STUDIO", small,
                     fill="#2B2B3A")
    draw_text_center(draw, (W / 2, H * 0.72), subtitle, get_font(int(m * 0.055)),
                     fill="#FFFFFF", stroke="#2B2B3A", stroke_width=max(2, size // 20))
    img.save(out_path, "PNG")


def render_outro_card(sheet: dict, W: int, H: int, out_path: str) -> None:
    prov = LocalImageProvider()
    prompt = ImagePrompt(prompt="", negative_prompt="", width=W, height=H,
                         seed=(sheet.get("seed", 1) + 3),
                         character_sheet={**sheet, "scene": {"type": "outro", "object": "trophy",
                                                             "on_screen_text": "Great job today!"}})
    tmp = out_path + ".scene.png"
    prov.generate_image(prompt, tmp)
    img = Image.open(tmp).convert("RGB")
    draw = ImageDraw.Draw(img)
    from app.services.rendering.fonts import draw_text_center, get_font
    m = min(W, H)
    draw_text_center(draw, (W / 2, H * 0.30), "You're a superstar learner!", get_font(int(m * 0.085)),
                     fill="#FFFFFF", stroke="#2B2B3A", stroke_width=max(3, int(m * 0.008)))
    draw_text_center(draw, (W / 2, H * 0.80), "See you next time — keep asking big questions!",
                     get_font(int(m * 0.042)), fill="#FFFFFF", stroke="#2B2B3A",
                     stroke_width=max(2, int(m * 0.004)))
    img.save(out_path, "PNG")
