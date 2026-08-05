"""Built-in script writer — the offline text provider.

Generates ORIGINAL educational scripts from the curated knowledge base (or
from the generic topic skeleton). Uses seeded template composition with many
variations so wording never repeats across runs, plus metadata generation.

The same engine could be replaced by an external LLM by changing one line in
the Settings page — the pipeline never notices.
"""

from __future__ import annotations

import json
import random
import re
from typing import Any

# ---------------------------------------------------------------------------
# Voice & pacing constants per age band
# ---------------------------------------------------------------------------

_WPM = {"3-6": 125, "7-9": 140, "10-13": 155}

_GREETINGS = [
    "Hi there, explorer!", "Hello, my curious friend!", "Hey superstar!",
    "Hi, bright spark!", "Hello, little genius!",
]
_HOOKS = [
    "Ready for a brand-new adventure?",
    "Today we unlock a whole new world.",
    "I have a big surprise for you today.",
    "Guess what? Today's quest needs YOUR brain.",
]
_QUESTION_LEADS = [
    "But wait — did you know that", "Hmm, quick question: did you hear that",
    "Okay — here's a fun one: did you notice that",
]
_FACT_LEADS = [
    "Fun fact time!", "Ready for a wow-fact?", "Here's my favorite part:",
    "And now — a jaw-dropper:",
]
_TRANSITIONS = [
    "Let's keep going!", "On to the next one!", "What comes next?",
    "The next one is even cooler!", "Ready for more?",
]
_ENCOURAGEMENTS = [
    "You are doing amazing!", "Great listening!", "Wow — fast learner!",
    "Your brain just grew a little!", "High five!",
]
_OUTROS = [
    "You learned, you laughed, you asked great questions.",
    "Look how much you discovered — be proud of that brain!",
    "You came, you saw, you LEARNED. Official explorer status: unlocked!",
]
_RECAP_LEADS = [
    "Before we go, remember what we found:",
    "Quick treasure check — today we collected:",
    "Let's pack our discoveries for the way home:",
]


def _words(text: str) -> int:
    return len(re.findall(r"\S+", text))


def _fit(parts: list[str], cap: int) -> str:
    """Greedily assemble narration parts within a word budget.

    The core content (first part pair) is always kept; optional flourishes
    (encouragement, transitions) are only added when the budget allows.
    """
    out: list[str] = []
    total = 0
    for i, part in enumerate(parts):
        w = _words(part)
        if i >= 2 and total + w > cap:  # core content exempt, extras budget-gated
            break
        out.append(part)
        total += w
    return " ".join(out)


def _planned_duration(narration: str, age: str) -> float:
    """Seconds the narration should take at kid-friendly pace (+ pad)."""
    wps = _WPM.get(age, 120) / 60.0
    return round(_words(narration) / wps + 0.7, 2)


class LocalTextProvider:
    name = "local"
    label = "Built-in Writer (offline)"
    requires_key = False

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        self.options = options or {}

    # ------------------------------------------------------------------
    def generate(
        self,
        system: str,
        prompt: str,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.8,
        json_response: bool = False,
    ) -> str:
        """Dispatch on the embedded brief task kind."""
        try:
            brief = self._extract_json(prompt)
        except ValueError:
            brief = {}
        task = brief.get("task", "")
        if task == "write_script":
            return json.dumps(self.write_script(brief["knowledge"], brief["params"], brief["scene_plan"]))
        if task == "write_metadata":
            return json.dumps(self.write_metadata(brief["script"], brief["knowledge"]))
        raise ValueError(f"LocalTextProvider: unsupported task '{task}'")

    # ------------------------------------------------------------------
    @staticmethod
    def _extract_json(prompt: str) -> dict[str, Any]:
        match = re.search(r"\{.*\}", prompt, re.DOTALL)
        if not match:
            raise ValueError("no JSON brief found in prompt")
        return json.loads(match.group(0))

    # ------------------------------------------------------------------
    # Script writing
    # ------------------------------------------------------------------

    def write_script(
        self,
        knowledge: dict[str, Any],
        params: dict[str, Any],
        scene_plan: dict[str, Any],
    ) -> dict[str, Any]:
        age = params.get("target_age", "3-6")
        topic_display = knowledge.get("display_name", params.get("topic", "").title())
        rng = random.Random(scene_plan.get("seed", 42))
        seeds = knowledge.get("scene_seeds", [])
        quiz = knowledge.get("quiz", "What was your favorite part today?")
        lesson_count = scene_plan["lesson_count"]

        # ---- word budget so narration actually fits the requested length ----
        length = params.get("length_seconds", 30)
        wps = _WPM.get(age, 125) / 60.0
        budget = max(24.0, wps * max(12.0, length - 7.0))  # minus cards/transitions
        # fixed scene slots (minimum core sizes in words)
        intro_cap = max(10, round(budget * 0.20))
        quiz_cap = max(10, round(budget * 0.16))
        outro_cap = max(12, round(budget * 0.22))
        # how many lesson scenes can possibly fit beneath the budget?
        remaining = budget - intro_cap - quiz_cap - outro_cap
        max_lessons = max(2, int(remaining // 17))  # ~17 words = opener + fact core
        lesson_count = max(2, min(lesson_count, max_lessons))
        fact_cap = max(10, round(budget * 0.16)) if lesson_count >= 4 else 0
        lesson_budget = budget - intro_cap - quiz_cap - outro_cap - fact_cap
        lesson_cap = max(13, round(lesson_budget / max(1, lesson_count)))

        chosen = self._pick_lessons(seeds, lesson_count, rng)

        scenes: list[dict[str, Any]] = []
        intro_text = _fit([
            rng.choice(_GREETINGS),
            f"Today we explore {topic_display}.",
            rng.choice(_HOOKS),
            "Stay for your special question at the end!",
        ], intro_cap)
        scenes.append(self._scene(0, "intro", "Welcome!",
                                  f"Let's explore {topic_display}!", intro_text, age))

        idx = 1
        total = len(chosen)
        for i, seed in enumerate(chosen):
            focus, fact = seed["focus"], seed["fact"]
            parts = [self._lesson_opener(focus, i, total, rng), fact]
            if i == total // 2 and total > 2:
                parts.append(rng.choice(_ENCOURAGEMENTS))
            if i < total - 1:
                parts.append(rng.choice(_TRANSITIONS))
            scenes.append(self._scene(idx, "lesson", focus, seed.get("text", focus),
                                      _fit(parts, lesson_cap), age))
            idx += 1

        if fact_cap and knowledge.get("facts"):
            scenes.insert(
                max(2, len(scenes) - 2),
                self._scene(0, "fact", "Fun fact", "Did you know?",
                            _fit([rng.choice(_FACT_LEADS) + " " + rng.choice(knowledge["facts"])],
                                 fact_cap), age),
            )

        quiz_text = _fit(["Now it's YOUR turn!", quiz,
                          "Say your answer out loud — I am listening!"], quiz_cap)
        scenes.append(self._scene(idx, "quiz", "Your turn", "Your turn!", quiz_text, age))
        idx += 1

        recap_items = ", ".join(s["focus"] for s in scenes
                                if s["type"] == "lesson" and s.get("focus"))
        outro_text = _fit(
            [f"{rng.choice(_RECAP_LEADS)} {recap_items}.",
             rng.choice(_OUTROS), rng.choice(_ENCOURAGEMENTS),
             "See you next time — keep asking big questions!"],
            outro_cap)
        scenes.append(self._scene(idx, "outro", "Goodbye!", "Great job today!", outro_text, age))

        for i, s in enumerate(scenes):
            s["index"] = i  # reindex after insertions

        title = self.make_title(topic_display, age, rng)
        return {
            "title": title,
            "topic": params.get("topic", topic_display),
            "target_age": age,
            "language": params.get("language", "en"),
            "scenes": scenes,
            "learning_objectives": knowledge.get("learning_objectives", []),
            "vocabulary": knowledge.get("vocabulary", []),
            "estimated_narration_seconds": round(sum(s["planned_duration"] for s in scenes), 2),
            "word_budget": round(budget, 1),
            "engine": "local",
        }

    # ------------------------------------------------------------------

    @staticmethod
    def _pick_lessons(seeds: list[dict[str, Any]], count: int, rng: random.Random) -> list[dict[str, Any]]:
        seeds = list(seeds)
        rng.shuffle(seeds)
        if not seeds:
            return []
        out = []
        while len(out) < count:
            out.extend(seeds)
        return out[:count]

    @staticmethod
    def _lesson_opener(focus: str, i: int, total: int, rng: random.Random) -> str:
        if i == 0:
            options = [
                f"First up — {focus}!",
                f"Let's start with our first discovery: {focus}.",
                f"Here comes number one — {focus}!",
            ]
        elif i == total - 1:
            options = [
                f"And our last stop today: {focus}!",
                f"We saved something special for last — {focus}.",
                f"One more before we finish: {focus}!",
            ]
        else:
            options = [
                f"Next up — {focus}!",
                f"Now meet {focus}!",
                f"Look what's ahead: {focus}!",
                f"Hold on tight — here comes {focus}!",
            ]
        return rng.choice(options)

    @staticmethod
    def _scene(index: int, type_: str, focus: str, on_screen: str,
               narration: str, age: str) -> dict[str, Any]:
        return {
            "index": index,
            "type": type_,
            "focus": focus,
            "on_screen_text": on_screen[:40],
            "narration": narration,
            "words": _words(narration),
            "planned_duration": _planned_duration(narration, age),
        }

    # ------------------------------------------------------------------
    # Title & metadata
    # ------------------------------------------------------------------

    @staticmethod
    def make_title(topic_display: str, age: str, rng: random.Random) -> str:
        patterns = [
            "{topic} for Kids | Fun Learning Adventure 🌟",
            "Learn {topic}! 🌟 Fun Educational Video for Kids",
            "{topic} Adventure! | Learn & Play for Kids",
            "Let's Learn {topic} Together! 🎈 Kids Educational Video",
        ]
        title = rng.choice(patterns).format(topic=topic_display, age=age)
        return title[:90]

    def write_metadata(self, script: dict[str, Any], knowledge: dict[str, Any]) -> dict[str, Any]:
        topic_display = knowledge.get("display_name", script.get("topic", "")).strip()
        objectives = knowledge.get("learning_objectives", [])
        lessons = [s for s in script.get("scenes", []) if s.get("type") == "lesson"]
        chapters = [
            {"time": "00:00", "label": "Welcome!"},
        ]
        for i, s in enumerate(lessons, 1):
            chapters.append({"time": s.get("start_time", ""), "label": s.get("focus", f"Part {i}")})
        chapters.append({"time": "", "label": "Quiz time!"})
        chapters.append({"time": "", "label": "Recap & goodbye"})

        description_lines = [
            f"🌟 {script.get('title', f'Learn {topic_display}!')}",
            "",
            f"Join us on a fun learning adventure about {topic_display}! "
            "Made with love for curious kids.",
            "",
            "📚 In this video kids will learn:",
        ]
        description_lines += [f"  ✅ {o}" for o in objectives]
        description_lines += [
            "",
            "⏱️ Chapters are listed as the video plays — follow along!",
            "",
            "🎨 All visuals and music are original, made for this channel. "
            "🎵 Background music: AI Kids Video Studio Music Box (royalty-free, original composition).",
            "",
            "👶 Made for kids. Safe, positive, screen-time-well-spent content. "
            "This video is fully animated — it features no real people or events.",
        ]
        tags = [
            f"{topic_display.lower()} for kids", "kids learning", "educational video",
            "preschool learning", "learn and play", "kids education",
            f"learn {topic_display.lower()}", "toddler learning", "fun learning",
            "educational cartoons", "kids videos", "nursery learning",
        ][:18]
        return {
            "title": script.get("title", f"Learn {topic_display}! 🌟")[:90],
            "description": "\n".join(description_lines),
            "tags": tags,
            "hashtags": [
                "#KidsLearning", "#EducationalVideo",
                f"#{re.sub(r'[^A-Za-z0-9]', '', topic_display) or 'Kids'}",
                "#Preschool", "#LearnAndPlay",
            ][:6],
            "keywords": [topic_display.lower(), "kids", "education", "learn", "fun",
                         "preschool", "kindergarten", "children", "animated lesson"][:12],
            "audience": {"made_for_kids": True, "age_range": script.get("target_age", "3-6")},
            "chapters": chapters,
            "disclosure": "Fully animated synthetic media created for education; "
                          "contains no real people, places or events.",
            "music_credits": "AI Kids Video Studio Music Box (original, royalty-free)",
        }
