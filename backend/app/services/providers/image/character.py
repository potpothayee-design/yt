"""The studio mascot renderer.

One deterministic, loveable character drawn from the character sheet.
Because the sheet's colors / accessory / proportions are derived from a
stable seed, the SAME character appears in every scene, thumbnail and end
card of a project — the visual-consistency contract enforced by the local
illustrator and embedded into every external prompt.
"""

from __future__ import annotations

import math
from typing import Any

from PIL import ImageDraw


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(h: str, factor: float) -> tuple[int, int, int]:
    """factor < 1 darkens, factor > 1 lightens a #RRGGBB color."""
    def clamp(v: float) -> int:
        return max(0, min(255, int(v)))

    r, g, b = hex_to_rgb(h)
    if factor >= 1:  # lighten
        return (clamp(r + (255 - r) * (factor - 1)),
                clamp(g + (255 - g) * (factor - 1)),
                clamp(b + (255 - b) * (factor - 1)))
    return (clamp(r * factor), clamp(g * factor), clamp(b * factor))


def draw_mascot(
    draw: ImageDraw.ImageDraw,
    sheet: dict[str, Any],
    cx: float,
    cy: float,
    size: float,
    expression: str = "happy",
    wave: bool = False,
) -> None:
    """Draw the mascot centered at (cx, cy) with overall height ``size``."""
    body = sheet.get("body_hex", "#6BCB77")
    belly = sheet.get("belly_hex", "#FFF3D6")
    u = size / 100.0  # unit scale

    dark = shade(body, 0.78)
    light = shade(body, 1.18)

    # --- ears / tufts -------------------------------------------------
    for dx in (-26 * u, 26 * u):
        draw.ellipse([cx + dx - 11 * u, cy - 48 * u, cx + dx + 11 * u, cy - 26 * u], fill=dark)
        draw.ellipse([cx + dx - 6 * u, cy - 44 * u, cx + dx + 6 * u, cy - 30 * u], fill=light)

    # --- body -----------------------------------------------------------
    draw.ellipse([cx - 42 * u, cy - 40 * u, cx + 42 * u, cy + 40 * u], fill=body)
    # subtle chest shading
    draw.ellipse([cx - 26 * u, cy - 4 * u, cx + 26 * u, cy + 36 * u], fill=belly)

    # --- feet -----------------------------------------------------------
    for dx in (-22 * u, 22 * u):
        draw.ellipse([cx + dx - 12 * u, cy + 32 * u, cx + dx + 12 * u, cy + 44 * u], fill=dark)

    # --- arms -------------------------------------------------------------
    arm_y = cy + 4 * u
    if wave:
        # one arm raised high
        draw.ellipse([cx - 56 * u, arm_y - 12 * u, cx - 32 * u, arm_y + 10 * u], fill=dark)
        draw.ellipse([cx + 30 * u, cy - 52 * u, cx + 54 * u, cy - 30 * u], fill=dark)
    else:
        draw.ellipse([cx - 56 * u, arm_y - 12 * u, cx - 32 * u, arm_y + 10 * u], fill=dark)
        draw.ellipse([cx + 32 * u, arm_y - 12 * u, cx + 56 * u, arm_y + 10 * u], fill=dark)

    # --- face -------------------------------------------------------------
    eye_y = cy - 14 * u
    eye_r = 11 * u
    for dx in (-17 * u, 17 * u):
        draw.ellipse([cx + dx - eye_r, eye_y - eye_r, cx + dx + eye_r, eye_y + eye_r], fill="white")
        pupil_r = 6 * u
        sparkle_dx = 2 * u
        draw.ellipse(
            [cx + dx - pupil_r, eye_y - pupil_r + 1 * u, cx + dx + pupil_r, eye_y + pupil_r + 1 * u],
            fill="#2B2B3A",
        )
        draw.ellipse(
            [cx + dx - 1 * u + sparkle_dx, eye_y - 4 * u, cx + dx + 2.5 * u + sparkle_dx, eye_y - 0.5 * u],
            fill="white",
        )

    # rosy cheeks
    for dx in (-30 * u, 30 * u):
        draw.ellipse([cx + dx - 6 * u, cy - 2 * u, cx + dx + 6 * u, cy + 6 * u], fill="#F7A8B8")

    # mouth
    if expression == "surprised":
        draw.ellipse([cx - 5 * u, cy + 6 * u, cx + 5 * u, cy + 17 * u], fill="#7A3B3B")
    elif expression == "excited":
        # open-mouth smile: dark mouth + tongue, framed by a smile arc
        draw.pieslice([cx - 10 * u, cy + 2 * u, cx + 10 * u, cy + 18 * u], start=0, end=180,
                      fill="#7A3B3B")
        draw.pieslice([cx - 5 * u, cy + 8 * u, cx + 5 * u, cy + 16 * u], start=0, end=180,
                      fill="#E56B6B")
        draw.line([cx - 10 * u, cy + 3 * u, cx + 10 * u, cy + 3 * u], fill="#7A3B3B",
                  width=max(2, int(2 * u)))
    else:  # happy smile
        draw.arc([cx - 11 * u, cy + 2 * u, cx + 11 * u, cy + 15 * u], start=15, end=165,
                 fill="#7A3B3B", width=max(2, int(2.4 * u)))

    # --- accessory --------------------------------------------------------
    acc = (sheet.get("accessory") or "").lower()
    if "star" in acc:
        _star(draw, cx, cy + 16 * u, 8 * u, "#FFD93D")
    elif "bow" in acc:
        y = cy + 2 * u
        draw.polygon([(cx - 14 * u, y), (cx - 4 * u, y - 6 * u), (cx - 4 * u, y + 6 * u)], fill="#E0475B")
        draw.polygon([(cx + 14 * u, y), (cx + 4 * u, y - 6 * u), (cx + 4 * u, y + 6 * u)], fill="#E0475B")
        draw.ellipse([cx - 4 * u, y - 4 * u, cx + 4 * u, y + 4 * u], fill="#B03648")
    elif "hat" in acc:
        draw.polygon([(cx - 22 * u, cy - 38 * u), (cx + 22 * u, cy - 38 * u), (cx, cy - 62 * u)],
                     fill="#4D96FF")
        draw.rectangle([cx - 24 * u, cy - 40 * u, cx + 24 * u, cy - 36 * u], fill="#34648F")
    elif "scarf" in acc:
        draw.arc([cx - 34 * u, cy + 2 * u, cx + 34 * u, cy + 24 * u], start=0, end=180,
                 fill="#3D9B6F", width=max(3, int(8 * u)))
    elif "glasses" in acc:
        for dx in (-17 * u, 17 * u):
            draw.ellipse([cx + dx - 13 * u, eye_y - 13 * u, cx + dx + 13 * u, eye_y + 13 * u],
                         outline="#8E5FC0", width=max(2, int(2.2 * u)))
        draw.line([cx - 4 * u, eye_y, cx + 4 * u, eye_y], fill="#8E5FC0", width=max(2, int(2 * u)))
    elif "backpack" in acc:
        draw.rounded_rectangle([cx - 46 * u, cy - 6 * u, cx - 40 * u, cy + 18 * u],
                               radius=3 * u, fill="#FF9F45")

    # little sprout antenna (brand mark — always present)
    draw.line([cx, cy - 44 * u, cx, cy - 54 * u], fill=dark, width=max(2, int(2 * u)))
    draw.ellipse([cx - 1 * u, cy - 62 * u, cx + 8 * u, cy - 52 * u], fill=light)


def _star(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, fill: str) -> None:
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    draw.polygon(pts, fill=fill)
