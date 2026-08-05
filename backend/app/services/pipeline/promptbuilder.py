"""Construction of every prompt sent to text/image/video providers.

Keeping prompt-building in one place guarantees the character sheet, style
tokens and negative prompts are IDENTICAL across scenes — the backbone of
visual consistency.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

# ---------------------------------------------------------------------------
# Character sheet — one consistent mascot per project
# ---------------------------------------------------------------------------

_MASCOT_NAMES = ["Pip", "Luna", "Bibo", "Momo", "Zuzu", "Kiki", "Nino", "Taffy"]
_BODY_COLORS = [
    ("coral", "#FF6B6B"), ("sunny", "#FFD93D"), ("leaf", "#6BCB77"),
    ("sky", "#4D96FF"), ("grape", "#9B72CF"), ("tangerine", "#FF9F45"),
]
_BELLY_COLORS = ["#FFF3D6", "#EAF6FF", "#FFE9F3", "#EFFAE3", "#F3EDFF"]
_ACCESSORIES = ["yellow star badge", "blue explorer hat", "red bow tie",
                "green scarf", "round purple glasses", "tiny backpack"]


def seed_for(topic: str, project_id: int | None = None) -> int:
    base = f"{topic.strip().lower()}::{project_id or 0}"
    return int(hashlib.sha256(base.encode()).hexdigest()[:12], 16)


def character_sheet(topic: str, project_id: int | None = None) -> dict[str, Any]:
    """Deterministic mascot description reused in EVERY prompt & render."""
    seed = seed_for(topic, project_id)
    body_name, body_hex = _BODY_COLORS[seed % len(_BODY_COLORS)]
    belly = _BELLY_COLORS[(seed >> 4) % len(_BELLY_COLORS)]
    return {
        "seed": seed,
        "name": _MASCOT_NAMES[(seed >> 8) % len(_MASCOT_NAMES)],
        "species": "small round friendly storybook creature",
        "body_color": body_name,
        "body_hex": body_hex,
        "belly_hex": belly,
        "eyes": "large round sparkling dark eyes with white highlights",
        "cheeks": "soft rosy cheeks",
        "accessory": _ACCESSORIES[(seed >> 12) % len(_ACCESSORIES)],
        "consistency_rules": [
            "same body shape, size and proportions in every scene",
            "same body color, belly color and accessory in every scene",
            "same eye style and face proportions in every scene",
            "same lighting style (soft warm daylight) throughout",
            "same 3D cartoon / storybook art style throughout",
        ],
    }


def character_sentence(sheet: dict[str, Any]) -> str:
    return (
        f"a consistent cute mascot named {sheet['name']}: a {sheet['species']} with "
        f"{sheet['body_color']} fur ({sheet['body_hex']}), a cream round belly, "
        f"{sheet['eyes']}, {sheet['cheeks']}, wearing a {sheet['accessory']}"
    )


# ---------------------------------------------------------------------------
# Shared negative prompt (hard quality gates)
# ---------------------------------------------------------------------------

NEGATIVE_PROMPT = (
    "morphing, flickering, warping, distorted anatomy, extra limbs, missing limbs, "
    "bad hands, extra fingers, text artifacts, watermark, logo, random object changes, "
    "broken physics, style change, inconsistent character, changing clothes, changing "
    "colors, scary, dark, violent, realistic human face, copyrighted characters"
)


def image_prompt(scene: dict[str, Any], sheet: dict[str, Any], style: str) -> str:
    """Long, explicit, consistent image prompt for one scene."""
    visual = scene.get("visual_description", scene.get("focus", ""))
    camera = scene.get("camera", "medium shot")
    return (
        f"{style} children's educational illustration. {visual}. "
        f"Featuring {character_sentence(sheet)}, {scene.get('character_action', 'smiling and waving')}. "
        f"Camera: {camera}; composition: clear focal point, generous negative space for captions; "
        f"lighting: soft warm daylight with gentle shadows; mood: joyful, safe, curious; "
        f"colors: bright cheerful palette, high saturation, consistent color grading; "
        f"textures: soft rounded shapes, smooth gradients; depth: layered background with soft blur; "
        f"perspective: child eye-level; style reference: modern storybook 3D cartoon. "
        f"On-screen text area at top center for the caption '{scene.get('on_screen_text', '')}'."
    )


def video_prompt(scene: dict[str, Any], sheet: dict[str, Any]) -> str:
    """Motion prompt for a scene clip (camera + character + object motion)."""
    motion = scene.get("motion", "gentle zoom in")
    return (
        f"Animate this scene as a smooth child's educational video shot. "
        f"Camera movement: {motion} at constant speed, no shake. "
        f"The mascot {sheet['name']} {scene.get('character_motion', 'bounces softly and waves happily')} "
        f"with natural physics, squash-and-stretch within storybook style. "
        f"Background: {scene.get('background_motion', 'clouds drift slowly, sparkles shimmer gently')}. "
        f"Timing: continuous smooth motion, 24fps. Lighting and shadows stay stable. "
        f"Keep the character's appearance, clothing, colors and the environment EXACTLY consistent. "
        f"No morphing, no flickering, no warping, no text artifacts."
    )


# ---------------------------------------------------------------------------
# Script brief (for LLM providers; the local engine consumes the same JSON)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are the head writer for a beloved children's educational channel. "
    "Write ORIGINAL, warm, energetic scripts for ages given. Never copy existing "
    "text, never use clichés, never include anything scary, violent, or "
    "inappropriate. Keep sentences short, rhythmic and speakable. Always answer "
    "with STRICT JSON matching the requested schema — no markdown fences."
)


def script_brief(knowledge: dict[str, Any], params: dict[str, Any], scene_plan: dict[str, Any]) -> str:
    brief = {
        "task": "write_script",
        "knowledge": knowledge,
        "params": params,
        "scene_plan": scene_plan,
    }
    return (
        "Write a complete kids educational video script as strict JSON with keys "
        '"title" (<=80 chars, catchy) and "scenes" (array). Each scene has keys: '
        '"index" (int), "type" (intro|lesson|question|fact|quiz|recap|outro), '
        '"focus" (short string), "on_screen_text" (<=30 chars), "narration" (string), '
        '"planned_duration" (seconds float). '
        "Rules: conversational, curious, encouraging; include questions, tiny story "
        "moments, fun facts, smooth transitions and a curiosity hook in the intro; "
        "no repeated sentence openers; no clichés; 100% original. "
        "The brief below tells you the learning objectives, the vocabulary, the "
        "facts to weave in, the topic, target age, target length and exactly how "
        "many lesson scenes to write (each lesson scene teaches ONE scene_seed). "
        f"BRIEF:\n{json.dumps(brief, indent=2)}"
    )


def metadata_brief(script: dict[str, Any], knowledge: dict[str, Any]) -> str:
    brief = {
        "task": "write_metadata",
        "script": {
            "title": script.get("title"),
            "target_age": script.get("target_age"),
            "scenes": [s.get("on_screen_text") for s in script.get("scenes", [])],
        },
        "knowledge": {"learning_objectives": knowledge.get("learning_objectives"),
                      "display_name": knowledge.get("display_name")},
    }
    return (
        "Create YouTube metadata as strict JSON with keys: title (<=90 chars), "
        "description (kid-safe, with a chapters section), tags (<=18 items), "
        "hashtags (<=6 items), keywords (<=12 items), audience (object with "
        "made_for_kids bool and age_range), disclosure (one-line synthetic media "
        "disclosure), music_credits. "
        f"BRIEF:\n{json.dumps(brief, indent=2)}"
    )
