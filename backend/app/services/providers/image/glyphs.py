"""Flat-design educational glyph library.

Each glyph draws one recognizable object (centered, roughly square bounding
box) using Pillow primitives with a consistent soft storybook look: round
corners, big shapes, gentle highlights. These power the offline illustrator
so the studio works end-to-end with zero external API keys.

Add new glyphs by registering a function in ``GLYPHS``.
"""

from __future__ import annotations

import math
import random

from PIL import ImageDraw

from app.services.providers.image.character import shade

D = ImageDraw.ImageDraw  # type alias


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def star_points(cx: float, cy: float, r: float, n: int = 5, inner: float = 0.45):
    pts = []
    for i in range(n * 2):
        ang = -math.pi / 2 + i * math.pi / n
        rad = r if i % 2 == 0 else r * inner
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    return pts


def sparkle(draw: D, cx: float, cy: float, r: float, color: str = "#FFF6C9") -> None:
    draw.polygon([(cx, cy - r), (cx + r * 0.28, cy - r * 0.28), (cx + r, cy),
                  (cx + r * 0.28, cy + r * 0.28), (cx, cy + r),
                  (cx - r * 0.28, cy + r * 0.28), (cx - r, cy), (cx - r * 0.28, cy - r * 0.28)],
                 fill=color)


def eyes(draw: D, cx: float, cy: float, dx: float, r: float) -> None:
    """Cute dot eyes with highlight."""
    for sx in (-dx, dx):
        draw.ellipse([cx + sx - r, cy - r, cx + sx + r, cy + r], fill="#2B2B3A")
        draw.ellipse([cx + sx - r * 0.35, cy - r * 0.55, cx + sx + r * 0.05, cy - r * 0.15],
                     fill="white")


def smile(draw: D, cx: float, cy: float, w: float, h: float, width: int = 4) -> None:
    draw.arc([cx - w, cy - h, cx + w, cy + h], start=15, end=165, fill="#7A3B3B", width=width)


def cloud_shape(draw: D, cx: float, cy: float, s: float, fill: str = "white") -> None:
    for dx, dy, r in ((-0.9, 0.15, 0.45), (0, -0.1, 0.6), (0.9, 0.15, 0.5), (0, 0.3, 0.55)):
        draw.ellipse([cx + dx * s - r * s, cy + dy * s - r * s, cx + dx * s + r * s, cy + dy * s + r * s], fill=fill)


# ---------------------------------------------------------------------------
# fruits & food
# ---------------------------------------------------------------------------

def g_apple(draw: D, cx, cy, s, rng: random.Random) -> None:
    u = s / 100
    draw.ellipse([cx - 42 * u, cy - 30 * u, cx + 6 * u, cy + 42 * u], fill="#E5484D")
    draw.ellipse([cx - 6 * u, cy - 30 * u, cx + 42 * u, cy + 42 * u], fill="#E5484D")
    draw.ellipse([cx - 28 * u, cy - 24 * u, cx - 12 * u, cy - 4 * u], fill="#F26D6D")
    draw.line([cx, cy - 32 * u, cx + 6 * u, cy - 46 * u], fill="#7A4A21", width=max(3, int(4 * u)))
    draw.ellipse([cx + 4 * u, cy - 48 * u, cx + 30 * u, cy - 36 * u], fill="#6BCB77")
    eyes(draw, cx, cy + 6 * u, 16 * u, 5 * u)
    smile(draw, cx, cy + 14 * u, 10 * u, 8 * u, max(3, int(3 * u)))


def g_banana(draw: D, cx, cy, s, rng: random.Random) -> None:
    u = s / 100
    # crescent from two overlapping arcs
    draw.pieslice([cx - 46 * u, cy - 46 * u, cx + 46 * u, cy + 46 * u], start=20, end=160,
                  fill="#FFD93D")
    draw.pieslice([cx - 42 * u, cy - 52 * u, cx + 42 * u, cy + 40 * u], start=20, end=160,
                  fill=None)  # cutout drawn by scene bg later; approximate with lighter inner
    draw.pieslice([cx - 42 * u, cy - 52 * u, cx + 42 * u, cy + 40 * u], start=20, end=160,
                  outline="#E8B93B", width=max(2, int(3 * u)))
    draw.ellipse([cx - 46 * u + 4 * u, cy + 6 * u, cx - 34 * u, cy + 18 * u], fill="#B9862F")
    draw.ellipse([cx + 34 * u, cy + 6 * u, cx + 46 * u - 4 * u, cy + 18 * u], fill="#B9862F")
    eyes(draw, cx, cy - 2 * u, 14 * u, 4.5 * u)


def g_strawberry(draw: D, cx, cy, s, rng: random.Random) -> None:
    u = s / 100
    draw.polygon([(cx - 40 * u, cy - 12 * u), (cx + 40 * u, cy - 12 * u), (cx, cy + 46 * u)], fill="#E5484D")
    draw.ellipse([cx - 40 * u, cy - 30 * u, cx + 40 * u, cy + 6 * u], fill="#E5484D")
    for _ in range(12):
        rx = rng.uniform(-26, 26) * u
        ry = rng.uniform(-14, 26) * u
        if rx * rx / (34 * u) ** 2 + (ry + 4 * u) ** 2 / (36 * u) ** 2 < 0.8:
            draw.ellipse([cx + rx - 2.4 * u, cy + ry - 3.4 * u, cx + rx + 2.4 * u, cy + ry + 3.4 * u],
                         fill="#FFE9A8")
    for i in range(5):  # leaves
        x = cx - 34 * u + i * 17 * u
        draw.polygon([(x, cy - 26 * u), (x + 12 * u, cy - 26 * u), (x + 6 * u, cy - 40 * u)], fill="#6BCB77")
    eyes(draw, cx, cy - 2 * u, 14 * u, 5 * u)
    smile(draw, cx, cy + 8 * u, 9 * u, 7 * u)


def g_watermelon(draw: D, cx, cy, s, rng: random.Random) -> None:
    u = s / 100
    draw.pieslice([cx - 48 * u, cy - 24 * u, cx + 48 * u, cy + 72 * u], start=200, end=340,
                  fill="#2E9E5B")
    draw.pieslice([cx - 42 * u, cy - 18 * u, cx + 42 * u, cy + 66 * u], start=200, end=340,
                  fill="#EFFAE3")
    draw.pieslice([cx - 36 * u, cy - 12 * u, cx + 36 * u, cy + 58 * u], start=200, end=340,
                  fill="#E5484D")
    for i in range(6):
        t = i / 5
        x = cx - 24 * u + t * 48 * u
        y = cy + 14 * u + (abs(t - 0.5)) * 18 * u
        draw.ellipse([x - 2.6 * u, y - 4 * u, x + 2.6 * u, y + 4 * u], fill="#2B2B3A")


def g_orange(draw: D, cx, cy, s, rng: random.Random) -> None:
    u = s / 100
    draw.ellipse([cx - 42 * u, cy - 34 * u, cx + 42 * u, cy + 44 * u], fill="#FF9F45")
    draw.ellipse([cx - 30 * u, cy - 24 * u, cx - 12 * u, cy - 8 * u], fill="#FFB870")
    draw.ellipse([cx + 2 * u, cy - 44 * u, cx + 26 * u, cy - 30 * u], fill="#6BCB77")
    eyes(draw, cx, cy + 8 * u, 15 * u, 5 * u)
    smile(draw, cx, cy + 16 * u, 10 * u, 8 * u)


def g_grapes(draw: D, cx, cy, s, rng: random.Random) -> None:
    u = s / 100
    positions = [(-20, 0), (0, -4), (20, 0), (-30, 20), (-10, 18), (10, 18), (30, 20), (0, 38)]
    for dx, dy in positions:
        draw.ellipse([cx + (dx - 15) * u, cy + (dy - 17) * u, cx + (dx + 15) * u, cy + (dy + 13) * u],
                     fill="#9B72CF", outline="#7A54A8", width=max(2, int(2 * u)))
    draw.line([cx, cy - 20 * u, cx + 8 * u, cy - 42 * u], fill="#7A4A21", width=max(3, int(4 * u)))
    draw.ellipse([cx + 4 * u, cy - 46 * u, cx + 30 * u, cy - 32 * u], fill="#6BCB77")
    draw.ellipse([cx - 24 * u, cy - 12 * u, cx - 14 * u, cy - 4 * u], fill="#BEA3E0")


# ---------------------------------------------------------------------------
# space
# ---------------------------------------------------------------------------

def g_sun(draw: D, cx, cy, s, rng: random.Random) -> None:
    u = s / 100
    for i in range(12):
        ang = i * math.pi / 6
        x1 = cx + 38 * u * math.cos(ang)
        y1 = cy + 38 * u * math.sin(ang)
        x2 = cx + 52 * u * math.cos(ang)
        y2 = cy + 52 * u * math.sin(ang)
        draw.line([x1, y1, x2, y2], fill="#FFB020", width=max(4, int(6 * u)))
    draw.ellipse([cx - 36 * u, cy - 36 * u, cx + 36 * u, cy + 36 * u], fill="#FFD93D",
                 outline="#FFB020", width=max(3, int(4 * u)))
    eyes(draw, cx, cy - 4 * u, 14 * u, 5 * u)
    smile(draw, cx, cy + 8 * u, 12 * u, 9 * u)


def g_moon(draw: D, cx, cy, s, rng: random.Random) -> None:
    u = s / 100
    draw.ellipse([cx - 38 * u, cy - 38 * u, cx + 38 * u, cy + 38 * u], fill="#FFF3D6")
    draw.ellipse([cx - 38 * u, cy - 38 * u, cx + 38 * u, cy + 38 * u], outline="#E8D9B0",
                 width=max(3, int(3 * u)))
    for dx, dy, r in ((-14, -10, 7), (12, 12, 5), (10, -16, 4)):
        draw.ellipse([cx + dx * u - r * u, cy + dy * u - r * u, cx + dx * u + r * u, cy + dy * u + r * u],
                     fill="#EDE2C4")
    # sleepy smile + eyes closed
    for sx in (-13 * u, 13 * u):
        draw.arc([cx + sx - 6 * u, cy - 10 * u, cx + sx + 6 * u, cy + 2 * u], start=15, end=165,
                 fill="#8A7A55", width=max(2, int(3 * u)))
    smile(draw, cx, cy + 8 * u, 10 * u, 7 * u)


def _planet(draw: D, cx, cy, s, color, detail: str) -> None:
    u = s / 100
    draw.ellipse([cx - 38 * u, cy - 38 * u, cx + 38 * u, cy + 38 * u], fill=color,
                 outline=shade(color, 0.8), width=max(2, int(3 * u)))
    if detail == "earth":
        for dx, dy, r in ((-14, -8, 12), (16, 6, 10), (-4, 20, 8)):
            draw.ellipse([cx + dx * u - r * u, cy + dy * u - r * u, cx + dx * u + r * u, cy + dy * u + r * u],
                         fill="#6BCB77")
        draw.ellipse([cx - 30 * u, cy - 30 * u, cx - 12 * u, cy - 12 * u], fill="#BFE7FF")
    elif detail == "jupiter":
        for dy in (-18, -2, 14):
            draw.line([cx - 34 * u, cy + dy * u, cx + 34 * u, cy + dy * u],
                      fill=shade(color, 0.85), width=max(3, int(6 * u)))
        draw.ellipse([cx + 6 * u, cy + 8 * u, cx + 24 * u, cy + 20 * u], fill="#E5484D")
    elif detail == "mars":
        for dx, dy, r in ((-12, 6, 5), (14, -12, 4), (10, 18, 3)):
            draw.ellipse([cx + dx * u - r * u, cy + dy * u - r * u, cx + dx * u + r * u, cy + dy * u + r * u],
                         fill=shade(color, 0.8))
    elif detail == "gray":
        for dx, dy, r in ((-12, -6, 8), (12, 10, 6), (16, -14, 4)):
            draw.ellipse([cx + dx * u - r * u, cy + dy * u - r * u, cx + dx * u + r * u, cy + dy * u + r * u],
                         fill=shade(color, 0.75))
    eyes(draw, cx, cy - 2 * u, 13 * u, 4.5 * u)
    smile(draw, cx, cy + 8 * u, 10 * u, 7 * u)


def g_planet_earth(draw, cx, cy, s, rng): _planet(draw, cx, cy, s, "#4D96FF", "earth")
def g_planet_mars(draw, cx, cy, s, rng): _planet(draw, cx, cy, s, "#E07856", "mars")
def g_planet_jupiter(draw, cx, cy, s, rng): _planet(draw, cx, cy, s, "#D8A56A", "jupiter")
def g_planet_gray(draw, cx, cy, s, rng): _planet(draw, cx, cy, s, "#B9BCCB", "gray")


def g_planet_saturn(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    draw.ellipse([cx - 34 * u, cy - 34 * u, cx + 34 * u, cy + 34 * u], fill="#E9C37F")
    draw.arc([cx - 56 * u, cy - 16 * u, cx + 56 * u, cy + 16 * u], start=180, end=360,
             fill="#C99A5B", width=max(4, int(7 * u)))
    draw.ellipse([cx - 34 * u, cy - 34 * u, cx + 34 * u, cy + 34 * u], outline="#C99A5B",
                 width=max(2, int(3 * u)))
    draw.arc([cx - 56 * u, cy - 16 * u, cx + 56 * u, cy + 16 * u], start=0, end=180,
             fill="#E5C48B", width=max(4, int(7 * u)))
    eyes(draw, cx, cy - 6 * u, 13 * u, 4.5 * u)
    smile(draw, cx, cy + 4 * u, 10 * u, 7 * u)


def g_rocket(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    draw.ellipse([cx - 20 * u, cy - 46 * u, cx + 20 * u, cy + 30 * u], fill="#F5F6FA",
                 outline="#C9CDDA", width=max(2, int(3 * u)))
    draw.polygon([(cx - 20 * u, cy - 26 * u), (cx + 20 * u, cy - 26 * u), (cx, cy - 58 * u)], fill="#E5484D")
    draw.ellipse([cx - 10 * u, cy - 20 * u, cx + 10 * u, cy + 0 * u], fill="#4D96FF",
                 outline="#34648F", width=max(2, int(3 * u)))
    for sx in (-1, 1):
        draw.polygon([(cx + sx * 20 * u, cy + 10 * u), (cx + sx * 36 * u, cy + 34 * u),
                      (cx + sx * 14 * u, cy + 30 * u)], fill="#E5484D")
    draw.polygon([(cx - 10 * u, cy + 30 * u), (cx + 10 * u, cy + 30 * u),
                  (cx + 6 * u, cy + 48 * u), (cx, cy + 40 * u), (cx - 6 * u, cy + 48 * u)],
                 fill="#FFB020")
    draw.polygon([(cx - 5 * u, cy + 30 * u), (cx + 5 * u, cy + 30 * u), (cx, cy + 42 * u)],
                 fill="#FFD93D")


def g_star_obj(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    draw.polygon(star_points(cx, cy, 44 * u), fill="#FFD93D", outline="#E8B93B")
    eyes(draw, cx, cy + 2 * u, 12 * u, 4.5 * u)
    smile(draw, cx, cy + 12 * u, 9 * u, 6 * u)


def g_balloon(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    color = rng.choice(["#FF6B6B", "#4D96FF", "#FFD93D", "#9B72CF", "#6BCB77"])
    draw.ellipse([cx - 26 * u, cy - 44 * u, cx + 26 * u, cy + 8 * u], fill=color,
                 outline=shade(color, 0.8), width=max(2, int(3 * u)))
    draw.ellipse([cx - 16 * u, cy - 32 * u, cx - 6 * u, cy - 18 * u], fill=shade(color, 1.3))
    draw.polygon([(cx - 4 * u, cy + 8 * u), (cx + 4 * u, cy + 8 * u), (cx, cy + 16 * u)], fill=shade(color, 0.8))
    draw.arc([cx - 8 * u, cy + 14 * u, cx + 8 * u, cy + 46 * u], start=80, end=260,
             fill="#8A8FA3", width=max(2, int(2 * u)))


# ---------------------------------------------------------------------------
# animals (parametric critter builder + species)
# ---------------------------------------------------------------------------

def _critter(draw: D, cx, cy, s, body_color, *, belly=None, ears="round", legs=4) -> None:
    u = s / 100
    dark = shade(body_color, 0.8)
    for i in range(legs):
        dx = (-24 + i * 16) * u
        draw.rounded_rectangle([cx + dx - 5 * u, cy + 26 * u, cx + dx + 5 * u, cy + 48 * u],
                               radius=4 * u, fill=dark)
    draw.ellipse([cx - 36 * u, cy - 22 * u, cx + 36 * u, cy + 30 * u], fill=body_color)
    if belly:
        draw.ellipse([cx - 20 * u, cy - 4 * u, cx + 20 * u, cy + 26 * u], fill=belly)
    # head
    hx, hy, hr = cx, cy - 34 * u, 24 * u
    if ears == "pointy":
        for sx in (-1, 1):
            draw.polygon([(hx + sx * 6 * u, hy - 18 * u), (hx + sx * 22 * u, hy - 18 * u),
                          (hx + sx * 16 * u, hy - 34 * u)], fill=body_color)
    elif ears == "round":
        for sx in (-1, 1):
            draw.ellipse([hx + sx * 14 * u - 8 * u, hy - 30 * u, hx + sx * 14 * u + 8 * u, hy - 14 * u],
                         fill=body_color)
    draw.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=body_color)
    eyes(draw, hx, hy - 2 * u, 9 * u, 4.2 * u)
    draw.ellipse([hx - 3.4 * u, hy + 5 * u, hx + 3.4 * u, hy + 10 * u], fill="#2B2B3A")
    smile(draw, hx, hy + 10 * u, 7 * u, 5 * u, max(2, int(2.6 * u)))


def g_cat(draw, cx, cy, s, rng): _critter(draw, cx, cy, s, "#F2A65A", belly="#FFE3C2", ears="pointy")
def g_dog(draw, cx, cy, s, rng): _critter(draw, cx, cy, s, "#B98A5A", belly="#EAD3B2", ears="round")


def g_fish(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    color = "#4D96FF"
    draw.polygon([(cx + 30 * u, cy), (cx + 52 * u, cy - 18 * u), (cx + 52 * u, cy + 18 * u)], fill=shade(color, 0.8))
    draw.ellipse([cx - 42 * u, cy - 26 * u, cx + 34 * u, cy + 26 * u], fill=color)
    draw.ellipse([cx - 34 * u, cy - 18 * u, cx - 16 * u, cy - 4 * u], fill=shade(color, 1.3))
    draw.polygon([(cx - 6 * u, cy - 26 * u), (cx + 8 * u, cy - 40 * u),
                  (cx + 18 * u, cy - 24 * u)], fill=shade(color, 0.8))
    eyes(draw, cx - 18 * u, cy - 2 * u, 0.1 * u, 5 * u)
    draw.arc([cx - 40 * u, cy + 2 * u, cx - 24 * u, cy + 12 * u], start=30, end=150,
             fill="#2B2B3A", width=max(2, int(3 * u)))
    for i in range(3):  # bubbles
        bx, by, br = cx - (50 + i * 12) * u, cy - (18 + i * 10) * u, (5 - i) * u
        draw.ellipse([bx - br, by - br, bx + br, by + br], outline="#BFE7FF", width=max(2, int(2.4 * u)))


def g_lion(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    mane = "#E0832F"
    draw.ellipse([cx - 40 * u, cy - 56 * u, cx + 40 * u, cy + 28 * u], fill=mane)
    for i in range(12):
        ang = i * math.pi / 6
        x = cx + 40 * u * math.cos(ang)
        y = (cy - 14 * u) + 40 * u * math.sin(ang)
        draw.ellipse([x - 9 * u, y - 9 * u, x + 9 * u, y + 9 * u], fill=mane)
    _critter_head(draw, cx, cy - 14 * u, 30 * u, "#F2B45A", muzzle="#FFE3C2")
    draw.ellipse([cx - 34 * u, cy + 8 * u, cx + 34 * u, cy + 48 * u], fill="#F2B45A")


def _critter_head(draw: D, hx, hy, hr, color, muzzle=None) -> None:
    for sx in (-1, 1):
        draw.ellipse([hx + sx * hr * 0.7 - hr * 0.34, hy - hr * 1.25, hx + sx * hr * 0.7 + hr * 0.34, hy - hr * 0.6],
                     fill=color)
    draw.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=color)
    if muzzle:
        draw.ellipse([hx - hr * 0.55, hy + hr * 0.05, hx + hr * 0.55, hy + hr * 0.75], fill=muzzle)
    eyes(draw, hx, hy - hr * 0.15, hr * 0.4, hr * 0.18)
    draw.ellipse([hx - hr * 0.14, hy + hr * 0.28, hx + hr * 0.14, hy + hr * 0.48], fill="#2B2B3A")
    smile(draw, hx, hy + hr * 0.5, hr * 0.3, hr * 0.22, max(2, int(hr * 0.1)))


def g_elephant(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    color = "#9BA6C9"
    draw.ellipse([cx - 40 * u, cy - 18 * u, cx + 36 * u, cy + 34 * u], fill=color)
    for dx in (-22, 8):
        draw.rounded_rectangle([cx + dx * u, cy + 18 * u, cx + (dx + 14) * u, cy + 48 * u],
                               radius=5 * u, fill=shade(color, 0.85))
    hx, hy = cx - 8 * u, cy - 26 * u
    draw.ellipse([hx - 38 * u, hy - 14 * u, hx - 12 * u, hy + 16 * u], fill=shade(color, 1.15))  # ear
    draw.ellipse([hx - 26 * u, hy - 26 * u, hx + 26 * u, hy + 26 * u], fill=color)
    # trunk
    draw.rounded_rectangle([hx - 8 * u, hy + 8 * u, hx + 10 * u, hy + 46 * u], radius=8 * u, fill=color)
    draw.ellipse([hx - 8 * u, hy + 38 * u, hx + 10 * u, hy + 50 * u], fill=shade(color, 0.85))
    eyes(draw, hx, hy - 6 * u, 12 * u, 4.2 * u)
    draw.arc([hx - 16 * u, hy + 6 * u, hx - 2 * u, hy + 14 * u], start=200, end=340,
             fill="#2B2B3A", width=max(2, int(2.4 * u)))


def g_penguin(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    draw.ellipse([cx - 30 * u, cy - 44 * u, cx + 30 * u, cy + 40 * u], fill="#3B4256")
    draw.ellipse([cx - 20 * u, cy - 30 * u, cx + 20 * u, cy + 36 * u], fill="white")
    for sx in (-1, 1):
        draw.ellipse([cx + sx * 32 * u - 7 * u, cy - 8 * u, cx + sx * 32 * u + 7 * u, cy + 26 * u],
                     fill="#3B4256")
        draw.ellipse([cx + sx * 14 * u - 11 * u, cy + 36 * u, cx + sx * 14 * u + 11 * u, cy + 48 * u],
                     fill="#FFB020")
    eyes(draw, cx, cy - 20 * u, 11 * u, 4.2 * u)
    draw.polygon([(cx - 6 * u, cy - 10 * u), (cx + 6 * u, cy - 10 * u), (cx, cy + 0 * u)], fill="#FFB020")
    # earmuffs
    for sx in (-1, 1):
        draw.ellipse([cx + sx * 26 * u - 8 * u, cy - 32 * u, cx + sx * 26 * u + 8 * u, cy - 16 * u],
                     fill="#E5484D")


def g_frog(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    color = "#6BCB77"
    draw.ellipse([cx - 42 * u, cy - 12 * u, cx + 42 * u, cy + 38 * u], fill=color)
    draw.ellipse([cx - 28 * u, cy + 4 * u, cx + 28 * u, cy + 34 * u], fill="#EFFAE3")
    for sx in (-1, 1):
        bx = cx + sx * 22 * u
        draw.ellipse([bx - 12 * u, cy - 34 * u, bx + 12 * u, cy - 10 * u], fill=color)
        draw.ellipse([bx - 8 * u, cy - 30 * u, bx + 8 * u, cy - 14 * u], fill="white")
        draw.ellipse([bx - 4 * u, cy - 25 * u, bx + 4 * u, cy - 17 * u], fill="#2B2B3A")
    draw.arc([cx - 20 * u, cy - 2 * u, cx + 20 * u, cy + 16 * u], start=20, end=160,
             fill="#2B2B3A", width=max(3, int(4 * u)))
    for sx in (-1, 1):
        draw.ellipse([cx + sx * 40 * u - 12 * u, cy + 24 * u, cx + sx * 40 * u + 12 * u, cy + 42 * u],
                     fill=shade(color, 0.85))


def g_octopus(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    color = "#9B72CF"
    for i in range(8):
        ang = math.pi * (0.1 + 0.8 * i / 7)
        x1 = cx + 30 * u * math.cos(ang)
        y1 = cy + 14 * u
        x2 = cx + 52 * u * math.cos(ang + (0.25 if i % 2 else -0.25))
        y2 = cy + 14 * u + 26 * u * math.sin(ang) + 14 * u
        draw.line([x1, y1, x2, y2], fill=shade(color, 0.9), width=max(5, int(9 * u)))
    draw.ellipse([cx - 34 * u, cy - 40 * u, cx + 34 * u, cy + 20 * u], fill=color)
    draw.ellipse([cx - 24 * u, cy - 32 * u, cx - 6 * u, cy - 16 * u], fill=shade(color, 1.25))
    eyes(draw, cx, cy - 8 * u, 13 * u, 5 * u)
    smile(draw, cx, cy + 2 * u, 9 * u, 7 * u)


def g_giraffe(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    color = "#F2C94C"
    # neck
    draw.rounded_rectangle([cx - 10 * u, cy - 46 * u, cx + 12 * u, cy + 14 * u], radius=9 * u, fill=color)
    # body
    draw.ellipse([cx - 36 * u, cy - 4 * u, cx + 40 * u, cy + 34 * u], fill=color)
    for dx in (-18, 12):
        draw.rounded_rectangle([cx + dx * u, cy + 22 * u, cx + (dx + 12) * u, cy + 50 * u],
                               radius=5 * u, fill=shade(color, 0.9))
    for dx, dy, r in ((-16, 10, 5), (8, 16, 6), (24, 6, 4), (0, -26, 4), (4, -10, 3.4)):
        draw.ellipse([cx + dx * u - r * u, cy + dy * u - r * u, cx + dx * u + r * u, cy + dy * u + r * u],
                     fill="#B9862F")
    # head + ossicones
    hx, hy = cx + 2 * u, cy - 50 * u
    for sx in (-1, 1):
        draw.line([hx + sx * 8 * u, hy - 6 * u, hx + sx * 10 * u, hy - 18 * u], fill="#B9862F",
                  width=max(2, int(3.4 * u)))
        draw.ellipse([hx + sx * 10 * u - 3.6 * u, hy - 22 * u, hx + sx * 10 * u + 3.6 * u, hy - 15 * u],
                     fill="#B9862F")
    draw.ellipse([hx - 18 * u, hy - 12 * u, hx + 22 * u, hy + 14 * u], fill=color)
    draw.ellipse([hx + 4 * u, hy - 2 * u, hx + 22 * u, hy + 12 * u], fill="#FFE9A8")
    eyes(draw, hx - 2 * u, hy - 2 * u, 9 * u, 3.8 * u)


# ---------------------------------------------------------------------------
# dinosaurs
# ---------------------------------------------------------------------------

def _dino(draw: D, cx, cy, s, color, *, neck=0.0, plates=False, frill=False,
          horns=0, tiny_arms=False, teeth=False) -> None:
    u = s / 100
    dark = shade(color, 0.8)
    # tail
    draw.polygon([(cx - 30 * u, cy + 4 * u), (cx - 58 * u, cy - 14 * u), (cx - 30 * u, cy + 22 * u)], fill=color)
    # legs
    for dx in (-16, 14):
        draw.rounded_rectangle([cx + dx * u, cy + 20 * u, cx + (dx + 14) * u, cy + 48 * u],
                               radius=6 * u, fill=dark)
    # body
    draw.ellipse([cx - 36 * u, cy - 16 * u, cx + 38 * u, cy + 30 * u], fill=color)
    draw.ellipse([cx - 22 * u, cy + 0 * u, cx + 24 * u, cy + 26 * u], fill=shade(color, 1.25))
    # neck + head position
    hx = cx + 34 * u + (6 * u if neck else 0)
    hy = cy - (18 + neck * 34) * u
    if neck:
        draw.line([cx + 22 * u, cy - 8 * u, hx, hy + 8 * u], fill=color, width=int(16 * u))
    if frill:
        draw.ellipse([hx - 26 * u, hy - 26 * u, hx + 26 * u, hy + 26 * u], fill=dark)
    draw.ellipse([hx - 20 * u, hy - 16 * u, hx + 22 * u, hy + 18 * u], fill=color)
    if horns:
        for i in range(horns):
            px = hx - 6 * u + i * 11 * u
            draw.polygon([(px, hy - 14 * u), (px + 6 * u, hy - 14 * u), (px + 3 * u, hy - 30 * u)], fill="white")
    if plates:
        for i in range(4):
            px = cx - 24 * u + i * 17 * u
            draw.polygon([(px, cy - 14 * u), (px + 9 * u, cy - 14 * u), (px + 4.5 * u, cy - 30 * u)],
                         fill="#E5484D")
    if tiny_arms:
        draw.line([cx + 22 * u, cy + 4 * u, cx + 30 * u, cy + 12 * u], fill=dark, width=max(3, int(4 * u)))
    eyes(draw, hx + 4 * u, hy - 4 * u, 8 * u, 4 * u)
    if teeth:
        for i in range(3):
            tx = hx + 2 * u + i * 7 * u
            draw.polygon([(tx, hy + 10 * u), (tx + 4 * u, hy + 10 * u), (tx + 2 * u, hy + 4 * u)], fill="white")
        draw.arc([hx - 4 * u, hy + 4 * u, hx + 20 * u, hy + 14 * u], start=10, end=170,
                 fill="#2B2B3A", width=max(2, int(2.6 * u)))
    else:
        smile(draw, hx + 4 * u, hy + 6 * u, 8 * u, 5 * u, max(2, int(2.6 * u)))


def g_trex(draw, cx, cy, s, rng): _dino(draw, cx, cy, s, "#6BCB77", tiny_arms=True, teeth=True)
def g_triceratops(draw, cx, cy, s, rng): _dino(draw, cx, cy, s, "#E0832F", frill=True, horns=3)
def g_brachiosaurus(draw, cx, cy, s, rng): _dino(draw, cx, cy, s, "#4D96FF", neck=1.0)
def g_stegosaurus(draw, cx, cy, s, rng): _dino(draw, cx, cy, s, "#9B72CF", plates=True)
def g_raptor(draw, cx, cy, s, rng): _dino(draw, cx, cy, s, "#E07856", teeth=True)


def g_fossil(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    draw.ellipse([cx - 44 * u, cy - 36 * u, cx + 44 * u, cy + 44 * u], fill="#D9C9A8")
    # ammonite spiral
    r = 4 * u
    ang = 0.0
    x, y = cx, cy
    pts = [(x, y)]
    for _ in range(26):
        ang += 0.42
        r += 1.6 * u
        x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
        pts.append((x, y))
    draw.line(pts, fill="#8A7A55", width=max(3, int(5 * u)))


# ---------------------------------------------------------------------------
# vehicles
# ---------------------------------------------------------------------------

def _wheels(draw: D, positions, y, r) -> None:
    for x in positions:
        draw.ellipse([x - r, y - r, x + r, y + r], fill="#2B2B3A")
        draw.ellipse([x - r * 0.45, y - r * 0.45, x + r * 0.45, y + r * 0.45], fill="#8A8FA3")


def g_car(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    draw.rounded_rectangle([cx - 46 * u, cy - 6 * u, cx + 46 * u, cy + 28 * u], radius=10 * u, fill="#E5484D")
    draw.rounded_rectangle([cx - 26 * u, cy - 24 * u, cx + 22 * u, cy + 2 * u], radius=8 * u, fill="#E5484D")
    draw.rounded_rectangle([cx - 20 * u, cy - 18 * u, cx - 2 * u, cy - 2 * u], radius=4 * u, fill="#BFE7FF")
    draw.rounded_rectangle([cx + 4 * u, cy - 18 * u, cx + 18 * u, cy - 2 * u], radius=4 * u, fill="#BFE7FF")
    draw.rectangle([cx - 46 * u, cy + 18 * u, cx + 46 * u, cy + 28 * u], fill="#B03648")
    draw.ellipse([cx + 34 * u, cy + 2 * u, cx + 44 * u, cy + 10 * u], fill="#FFF6C9")
    _wheels(draw, [cx - 26 * u, cx + 26 * u], cy + 30 * u, 11 * u)


def g_firetruck(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    draw.rounded_rectangle([cx - 52 * u, cy - 12 * u, cx + 48 * u, cy + 26 * u], radius=8 * u, fill="#E5484D")
    draw.rounded_rectangle([cx - 52 * u, cy - 12 * u, cx - 16 * u, cy + 8 * u], radius=8 * u, fill="#D0342C")
    draw.rectangle([cx - 12 * u, cy - 20 * u, cx + 46 * u, cy - 12 * u], fill="#C9CDDA")
    draw.rectangle([cx - 46 * u, cy - 8 * u, cx - 24 * u, cy + 2 * u], fill="#BFE7FF")  # cab window
    draw.ellipse([cx - 6 * u, cy - 2 * u, cx + 10 * u, cy + 14 * u], fill="#8A8FA3")  # hose reel
    draw.rounded_rectangle([cx - 10 * u, cy - 24 * u, cx + 2 * u, cy - 16 * u], radius=3 * u, fill="#FFD93D")  # siren
    draw.rectangle([cx - 52 * u, cy + 14 * u, cx + 48 * u, cy + 20 * u], fill="white")
    _wheels(draw, [cx - 34 * u, cx - 6 * u, cx + 30 * u], cy + 28 * u, 10 * u)


def g_plane(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    draw.ellipse([cx - 52 * u, cy - 14 * u, cx + 52 * u, cy + 14 * u], fill="#F5F6FA")
    draw.pieslice([cx + 26 * u, cy - 14 * u, cx + 66 * u, cy + 14 * u], start=270, end=90, fill="#4D96FF")
    draw.polygon([(cx - 6 * u, cy - 10 * u), (cx + 18 * u, cy - 38 * u), (cx + 30 * u, cy - 34 * u),
                  (cx + 16 * u, cy - 6 * u)], fill="#E5484D")
    draw.polygon([(cx - 6 * u, cy + 10 * u), (cx + 18 * u, cy + 38 * u), (cx + 30 * u, cy + 34 * u),
                  (cx + 16 * u, cy + 6 * u)], fill="#E5484D")
    draw.polygon([(cx - 46 * u, cy - 8 * u), (cx - 58 * u, cy - 26 * u), (cx - 40 * u, cy - 12 * u)], fill="#4D96FF")
    for i in range(3):
        wx = cx + 8 * u - i * 16 * u
        draw.ellipse([wx - 4 * u, cy - 9 * u, wx + 4 * u, cy - 1 * u], fill="#BFE7FF",
                     outline="#8A8FA3", width=max(1, int(1.6 * u)))


def g_boat(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    draw.polygon([(cx - 46 * u, cy + 4 * u), (cx + 46 * u, cy + 4 * u), (cx + 30 * u, cy + 34 * u),
                  (cx - 30 * u, cy + 34 * u)], fill="#B9783F")
    draw.line([cx, cy + 4 * u, cx, cy - 44 * u], fill="#7A4A21", width=max(3, int(5 * u)))
    draw.polygon([(cx + 2 * u, cy - 42 * u), (cx + 34 * u, cy - 10 * u), (cx + 2 * u, cy - 6 * u)], fill="#E5484D")
    draw.polygon([(cx - 2 * u, cy - 36 * u), (cx - 28 * u, cy - 12 * u), (cx - 2 * u, cy - 8 * u)], fill="white")
    for sx in (-1, 1):  # waves
        draw.arc([cx + sx * 30 * u - 16 * u, cy + 34 * u, cx + sx * 30 * u + 16 * u, cy + 50 * u],
                 start=20, end=160, fill="#7EC8E3", width=max(2, int(4 * u)))


def g_train(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    # engine
    draw.rounded_rectangle([cx - 52 * u, cy - 10 * u, cx - 4 * u, cy + 24 * u], radius=6 * u, fill="#4D96FF")
    draw.rounded_rectangle([cx - 52 * u, cy - 30 * u, cx - 24 * u, cy - 8 * u], radius=6 * u, fill="#34648F")
    draw.rectangle([cx - 46 * u, cy - 26 * u, cx - 30 * u, cy - 12 * u], fill="#BFE7FF")
    draw.rectangle([cx - 16 * u, cy - 34 * u, cx - 8 * u, cy - 10 * u], fill="#2B2B3A")
    draw.ellipse([cx - 18 * u, cy - 44 * u, cx - 6 * u, cy - 32 * u], fill="#C9CDDA")  # smoke
    draw.ellipse([cx - 26 * u, cy - 52 * u, cx - 10 * u, cy - 36 * u], fill="#E3E7F0")
    # car
    draw.rounded_rectangle([cx + 0 * u, cy - 6 * u, cx + 48 * u, cy + 24 * u], radius=6 * u, fill="#E5484D")
    draw.rectangle([cx + 8 * u, cy - 2 * u, cx + 24 * u, cy + 12 * u], fill="#BFE7FF")
    _wheels(draw, [cx - 40 * u, cx - 12 * u, cx + 12 * u, cx + 36 * u], cy + 26 * u, 9 * u)


# ---------------------------------------------------------------------------
# misc educational
# ---------------------------------------------------------------------------

def g_magnifier(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    draw.ellipse([cx - 30 * u, cy - 42 * u, cx + 22 * u, cy + 10 * u], fill="#DFF4FF",
                 outline="#4D96FF", width=max(4, int(8 * u)))
    draw.line([cx + 16 * u, cy + 6 * u, cx + 42 * u, cy + 34 * u], fill="#7A4A21",
              width=max(5, int(9 * u)))
    draw.arc([cx - 22 * u, cy - 34 * u, cx + 4 * u, cy - 8 * u], start=120, end=230,
             fill="white", width=max(3, int(5 * u)))


def g_lightbulb(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    draw.ellipse([cx - 28 * u, cy - 42 * u, cx + 28 * u, cy + 12 * u], fill="#FFD93D",
                 outline="#E8B93B", width=max(2, int(3 * u)))
    draw.rounded_rectangle([cx - 14 * u, cy + 10 * u, cx + 14 * u, cy + 30 * u], radius=4 * u, fill="#8A8FA3")
    for dy in (16, 24):
        draw.line([cx - 14 * u, cy + dy * u, cx + 14 * u, cy + dy * u], fill="#5A5F73",
                  width=max(2, int(3 * u)))
    for i in range(8):
        ang = i * math.pi / 4
        draw.line([cx + 40 * u * math.cos(ang), cy - 16 * u + 40 * u * math.sin(ang),
                   cx + 50 * u * math.cos(ang), cy - 16 * u + 50 * u * math.sin(ang)],
                  fill="#FFE9A8", width=max(2, int(4 * u)))
    eyes(draw, cx, cy - 18 * u, 11 * u, 4.5 * u)
    smile(draw, cx, cy - 8 * u, 8 * u, 6 * u)


def g_trophy(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    gold = "#FFD93D"
    for sx in (-1, 1):
        draw.arc([cx + sx * 20 * u - 16 * u, cy - 30 * u, cx + sx * 20 * u + 16 * u, cy + 2 * u],
                 start=250 if sx < 0 else 110, end=90 if sx < 0 else 270, fill=gold, width=max(4, int(7 * u)))
    draw.polygon([(cx - 26 * u, cy - 34 * u), (cx + 26 * u, cy - 34 * u), (cx + 16 * u, cy + 6 * u),
                  (cx - 16 * u, cy + 6 * u)], fill=gold)
    draw.rectangle([cx - 6 * u, cy + 6 * u, cx + 6 * u, cy + 20 * u], fill="#D9A82E")
    draw.rounded_rectangle([cx - 22 * u, cy + 20 * u, cx + 22 * u, cy + 32 * u], radius=5 * u, fill="#B9862F")
    draw.polygon(star_points(cx, cy - 16 * u, 9 * u), fill="#FFF6C9")
    sparkle(draw, cx + 30 * u, cy - 38 * u, 8 * u)
    sparkle(draw, cx - 32 * u, cy - 44 * u, 6 * u)


def g_heart(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    draw.ellipse([cx - 36 * u, cy - 28 * u, cx + 0 * u, cy + 8 * u], fill="#E5484D")
    draw.ellipse([cx + 0 * u, cy - 28 * u, cx + 36 * u, cy + 8 * u], fill="#E5484D")
    draw.polygon([(cx - 35 * u, cy - 8 * u), (cx + 35 * u, cy - 8 * u), (cx, cy + 42 * u)], fill="#E5484D")
    draw.ellipse([cx - 24 * u, cy - 18 * u, cx - 10 * u, cy - 6 * u], fill="#F26D6D")


def g_flower(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    for i in range(6):
        ang = i * math.pi / 3
        px = cx + 24 * u * math.cos(ang)
        py = cy - 8 * u + 24 * u * math.sin(ang)
        draw.ellipse([px - 14 * u, py - 14 * u, px + 14 * u, py + 14 * u], fill="#F7A8B8")
    draw.ellipse([cx - 14 * u, cy - 22 * u, cx + 14 * u, cy + 6 * u], fill="#FFD93D")
    draw.line([cx, cy + 6 * u, cx, cy + 46 * u], fill="#3D9B6F", width=max(3, int(6 * u)))
    draw.ellipse([cx + 2 * u, cy + 24 * u, cx + 20 * u, cy + 34 * u], fill="#6BCB77")


def g_tree(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    draw.rounded_rectangle([cx - 8 * u, cy + 4 * u, cx + 8 * u, cy + 46 * u], radius=4 * u, fill="#8A5A2B")
    for dx, dy, r in ((-18, -6, 22), (18, -6, 22), (0, -24, 26)):
        draw.ellipse([cx + dx * u - r * u, cy + dy * u - r * u, cx + dx * u + r * u, cy + dy * u + r * u],
                     fill="#6BCB77")
    for dx, dy in ((-14, -12), (10, -20), (4, 2)):
        draw.ellipse([cx + dx * u - 4 * u, cy + dy * u - 4 * u, cx + dx * u + 4 * u, cy + dy * u + 4 * u],
                     fill="#E5484D")


def g_question(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    from app.services.rendering.fonts import draw_text_center, get_font
    draw.ellipse([cx - 44 * u, cy - 44 * u, cx + 44 * u, cy + 44 * u], fill="#9B72CF",
                 outline="#7A54A8", width=max(3, int(5 * u)))
    draw.ellipse([cx - 30 * u, cy - 34 * u, cx - 14 * u, cy - 20 * u], fill="#BEA3E0")
    font = get_font(int(56 * u))
    draw_text_center(draw, (cx, cy + 2 * u), "?", font, fill="white")


def g_number(draw: D, cx, cy, s, rng, value: str, color: str = "#4D96FF") -> None:
    u = s / 100
    from app.services.rendering.fonts import draw_text_center, get_font
    draw.ellipse([cx - 46 * u, cy - 46 * u, cx + 46 * u, cy + 46 * u], fill=color,
                 outline=shade(color, 0.8), width=max(3, int(6 * u)))
    draw.ellipse([cx - 30 * u, cy - 36 * u, cx - 10 * u, cy - 18 * u], fill=shade(color, 1.35))
    font = get_font(int((64 if len(value) == 1 else 46) * u))
    draw_text_center(draw, (cx, cy + 3 * u), value, font, fill="white",
                     stroke=shade(color, 0.65), stroke_width=max(2, int(3 * u)))


GLYPHS = {
    "apple": g_apple, "banana": g_banana, "strawberry": g_strawberry,
    "watermelon": g_watermelon, "orange": g_orange, "grapes": g_grapes,
    "sun": g_sun, "moon": g_moon, "star": g_star_obj, "balloon": g_balloon,
    "planet_earth": g_planet_earth, "planet_mars": g_planet_mars,
    "planet_jupiter": g_planet_jupiter, "planet_saturn": g_planet_saturn,
    "planet_gray": g_planet_gray, "rocket": g_rocket,
    "cat": g_cat, "dog": g_dog, "fish": g_fish, "lion": g_lion,
    "elephant": g_elephant, "penguin": g_penguin, "frog": g_frog,
    "octopus": g_octopus, "giraffe": g_giraffe,
    "trex": g_trex, "triceratops": g_triceratops, "brachiosaurus": g_brachiosaurus,
    "stegosaurus": g_stegosaurus, "raptor": g_raptor, "fossil": g_fossil,
    "car": g_car, "firetruck": g_firetruck, "plane": g_plane, "boat": g_boat,
    "train": g_train,
    "magnifier": g_magnifier, "lightbulb": g_lightbulb, "trophy": g_trophy,
    "heart": g_heart, "flower": g_flower, "tree": g_tree, "question": g_question,
}


def g_ball(draw: D, cx, cy, s, rng) -> None:
    u = s / 100
    draw.ellipse([cx - 40 * u, cy - 40 * u, cx + 40 * u, cy + 40 * u], fill="#E5484D")
    draw.pieslice([cx - 40 * u, cy - 40 * u, cx + 40 * u, cy + 40 * u], start=60, end=180, fill="#4D96FF")
    draw.pieslice([cx - 40 * u, cy - 40 * u, cx + 40 * u, cy + 40 * u], start=180, end=300, fill="#FFD93D")
    draw.arc([cx - 40 * u, cy - 40 * u, cx + 40 * u, cy + 40 * u], start=0, end=360,
             fill="white", width=max(3, int(4 * u)))
    draw.line([cx - 40 * u, cy, cx + 40 * u, cy], fill="white", width=max(3, int(4 * u)))
    draw.ellipse([cx - 24 * u, cy - 26 * u, cx - 10 * u, cy - 14 * u], fill=shade("#FFFFFF", 1.0))


GLYPHS["ball"] = g_ball


def draw_glyph_by_name(draw: D, name: str, cx: float, cy: float, size: float,
                       rng: random.Random | None = None) -> bool:
    """Draw registered glyph. Returns False if unknown (caller falls back)."""
    rng = rng or random.Random(0)
    fn = GLYPHS.get(name)
    if fn:
        fn(draw, cx, cy, size, rng)
        return True
    # dynamic: numbers / single letters / color circles
    if name.isdigit():
        g_number(draw, cx, cy, size, rng, name, "#4D96FF")
        return True
    if len(name) == 1 and name.isalpha():
        g_number(draw, cx, cy, size, rng, name.upper(), "#E5484D")
        return True
    return False
