"""Pipeline engine — the 12-step kids video production workflow.

The engine is persistence-agnostic: it works against a filesystem work
directory and an in-memory ``state`` dict (mirrored to ``state.json`` after
every step, which makes interrupted jobs resumable). The DB-backed job
orchestrator and the GitHub Actions standalone runner both drive this same
engine through the ``ProgressReporter`` protocol.

Steps: research → script → storyboard → prompts → images → voice → video →
music → captions → editing → thumbnails → preview
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from app.services.pipeline.knowledge import research as research_topic
from app.services.pipeline.promptbuilder import (
    NEGATIVE_PROMPT,
    SYSTEM_PROMPT,
    character_sheet,
    image_prompt,
    metadata_brief,
    script_brief,
    seed_for,
    video_prompt,
)
from app.services.providers.base import (
    ImagePrompt,
    VideoPrompt,
    WordTiming,
)
from app.services.providers.image.local import render_intro_card, render_outro_card
from app.services.rendering.captions import to_ass, to_srt
from app.services.rendering.composer import SceneMedia, compose
from app.services.rendering.thumbnail import generate_thumbnails

#: Canonical pipeline step order.
STEP_NAMES = [
    "research", "script", "storyboard", "prompts", "images", "voice",
    "video", "music", "captions", "editing", "thumbnails", "preview", "upload",
]

STEP_LABELS = {
    "research": "Research", "script": "Script", "storyboard": "Storyboard",
    "prompts": "Scene Prompts", "images": "Images", "voice": "Voice",
    "video": "Video", "music": "Music", "captions": "Captions",
    "editing": "Editing", "thumbnails": "Thumbnail", "preview": "Preview",
    "upload": "Upload",
}

_ASPECT_SIZES = {
    ("16:9", "draft"): (854, 480), ("16:9", "standard"): (1280, 720), ("16:9", "high"): (1920, 1080),
    ("9:16", "draft"): (540, 960), ("9:16", "standard"): (720, 1280), ("9:16", "high"): (1080, 1920),
    ("1:1", "draft"): (640, 640), ("1:1", "standard"): (960, 960), ("1:1", "high"): (1080, 1080),
}

_MOTIONS = ["zoom_in", "pan_right", "zoom_out", "pan_left", "float"]
_VISUAL_BY_TYPE = {
    "intro": "Welcome stage: bright stage with bunting flags and floating confetti",
    "lesson": "Learning scene: big educational subject on a soft meadow stage",
    "fact": "Discovery scene: glowing lightbulb moment with sparkles",
    "question": "Thinking scene: big friendly question badge floating in the sky",
    "quiz": "Quiz scene: giant playful question mark with balloons",
    "recap": "Celebration scene: all treasures collected on a picnic cloth",
    "outro": "Celebration finale: confetti rain over a sunny meadow",
}
_CAMERA_BY_TYPE = {
    "intro": "gentle push in", "lesson": "medium shot, slow drift",
    "fact": "close shot with slow zoom out", "question": "medium close shot",
    "quiz": "medium shot with subtle float", "recap": "wide shot",
    "outro": "wide shot, gentle pull back",
}


class ProgressReporter(Protocol):
    def __call__(self, step: str, status: str, message: str = "") -> None: ...


class CancelledError(RuntimeError):
    pass


@dataclass
class EngineContext:
    work_dir: Path
    params: dict[str, Any]
    providers: dict[str, Any]
    project_id: int | None = None
    progress: ProgressReporter = lambda s, st, m="": None
    should_cancel: Callable[[], bool] = lambda: False
    state: dict[str, Any] = field(default_factory=dict)

    @property
    def width(self) -> int:
        return _ASPECT_SIZES.get(
            (self.params.get("aspect_ratio", "16:9"), self.params.get("quality", "standard")),
            (1280, 720),
        )[0]

    @property
    def height(self) -> int:
        return _ASPECT_SIZES.get(
            (self.params.get("aspect_ratio", "16:9"), self.params.get("quality", "standard")),
            (1280, 720),
        )[1]

    @property
    def fps(self) -> int:
        return 24

    def cancel_check(self) -> None:
        if self.should_cancel():
            raise CancelledError("job cancelled by user")

    def save_state(self) -> None:
        (self.work_dir / "state.json").write_text(json.dumps(self.state, indent=2))

    def load_state(self) -> None:
        f = self.work_dir / "state.json"
        if f.exists():
            try:
                self.state = json.loads(f.read_text())
            except json.JSONDecodeError:
                self.state = {}


class PipelineEngine:
    """Runs pipeline steps against an EngineContext."""

    def __init__(self, ctx: EngineContext):
        self.ctx = ctx
        ctx.work_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    def run(self, steps: list[str] | None = None, only_scene: int | None = None,
            resume: bool = True) -> dict[str, Any]:
        steps = steps or [s for s in STEP_NAMES if s != "upload"]
        if resume:
            self.ctx.load_state()
        for name in steps:
            if name == "upload":
                continue
            self.ctx.cancel_check()
            fn = getattr(self, f"step_{name}", None)
            if fn is None:
                continue
            self.ctx.progress(name, "running", STEP_LABELS.get(name, name))
            if name in ("images", "voice", "video"):
                fn(only_scene=only_scene)
            else:
                fn()
            self.ctx.save_state()
            self.ctx.progress(name, "done", STEP_LABELS.get(name, name))
        return self.ctx.state

    # ------------------------------------------------------------------
    # Step 1: research
    # ------------------------------------------------------------------
    def step_research(self) -> None:
        kb = research_topic(self.ctx.params["topic"])
        self.ctx.state["knowledge"] = kb

    # ------------------------------------------------------------------
    # Step 2: script
    # ------------------------------------------------------------------
    def step_script(self) -> None:
        kb = self.ctx.state["knowledge"]
        params = self.ctx.params
        length = params.get("length_seconds", 30)
        lesson_count = max(2, min(10, round((length - 15) / 5)))
        scene_plan = {"seed": seed_for(params["topic"], self.ctx.project_id),
                      "lesson_count": lesson_count}
        raw = self.ctx.providers["text"].generate(
            SYSTEM_PROMPT, script_brief(kb, params, scene_plan),
            json_response=True,
        )
        script = self._parse_script(raw, kb, params, scene_plan)
        self.ctx.state["script"] = script

    def _parse_script(self, raw: str, kb: dict, params: dict, scene_plan: dict) -> dict:
        try:
            import json as _json
            return _json.loads(raw)
        except Exception:
            # malformed LLM output -> retry once, then fall back to built-in engine
            from app.services.providers.text.local import LocalTextProvider
            try:
                import json as _json
                retry = self.ctx.providers["text"].generate(
                    SYSTEM_PROMPT, script_brief(kb, params, scene_plan),
                    json_response=True, temperature=0.4,
                )
                return _json.loads(retry)
            except Exception:
                return LocalTextProvider().write_script(kb, params, scene_plan)

    # ------------------------------------------------------------------
    # Step 3: storyboard
    # ------------------------------------------------------------------
    def step_storyboard(self) -> None:
        script = self.ctx.state["script"]
        kb = self.ctx.state["knowledge"]
        seed_by_focus = {s["focus"]: s for s in kb.get("scene_seeds", [])}
        storyboard: list[dict[str, Any]] = []
        for i, scene in enumerate(script["scenes"]):
            stype = scene.get("type", "lesson")
            seed = seed_by_focus.get(scene.get("focus"), {})
            visual = _VISUAL_BY_TYPE.get(stype, _VISUAL_BY_TYPE["lesson"])
            obj = seed.get("object") or {"intro": "star", "quiz": "question",
                                          "question": "question", "fact": "lightbulb",
                                          "outro": "trophy", "recap": "star"}.get(stype, "star")
            focus = scene.get("focus", "")
            if stype == "lesson":
                friendly_obj = obj.replace("_", " ")
                visual = (f"Close-up learning scene about {focus}: a big friendly "
                          f"{friendly_obj} presented stage-center")
            storyboard.append({
                "index": i,
                "type": stype,
                "focus": focus,
                "narration": scene["narration"],
                "on_screen_text": scene.get("on_screen_text", ""),
                "planned_duration": scene.get("planned_duration", 5.0),
                "visual_description": visual,
                "object": obj,
                "camera": _CAMERA_BY_TYPE.get(stype, "medium shot"),
                "motion": _MOTIONS[i % len(_MOTIONS)],
                "character_action": "smiling and waving at the viewer" if stype == "intro"
                    else ("celebrating happily" if stype == "outro"
                          else "pointing excitedly at the subject"),
                "character_motion": "bounces softly and waves" if stype in ("intro", "outro")
                    else "gently hops and gestures toward the subject",
                "background_motion": "clouds drift slowly, sparkles shimmer gently, grass sways",
            })
        self.ctx.state["storyboard"] = storyboard

    # ------------------------------------------------------------------
    # Step 4: scene prompts (consistency contract)
    # ------------------------------------------------------------------
    def step_prompts(self) -> None:
        sheet = character_sheet(self.ctx.params["topic"], self.ctx.project_id)
        style = self.ctx.params.get("style", "3D Cartoon")
        prompts = {
            "character_sheet": sheet,
            "negative_prompt": NEGATIVE_PROMPT,
            "style": style,
            "scenes": [],
        }
        for scene in self.ctx.state["storyboard"]:
            prompts["scenes"].append({
                "index": scene["index"],
                "image_prompt": image_prompt(scene, sheet, style),
                "video_prompt": video_prompt(scene, sheet),
                "negative_prompt": NEGATIVE_PROMPT,
            })
        self.ctx.state["prompts"] = prompts

    # ------------------------------------------------------------------
    # Step 5: images
    # ------------------------------------------------------------------
    def step_images(self, only_scene: int | None = None) -> None:
        prompts = self.ctx.state["prompts"]
        sheet = prompts["character_sheet"]
        provider = self.ctx.providers["image"]
        images = self.ctx.state.setdefault("images", {})
        for scene in self.ctx.state["storyboard"]:
            idx = scene["index"]
            if only_scene is not None and idx != only_scene:
                continue
            out = self.ctx.work_dir / f"scene_{idx:02d}.png"
            sheet_local = {**sheet, "scene": scene}  # consumed by local illustrator
            prompt = ImagePrompt(
                prompt=prompts["scenes"][idx]["image_prompt"],
                negative_prompt=prompts["negative_prompt"],
                width=self.ctx.width, height=self.ctx.height,
                seed=sheet["seed"] + idx,
                character_sheet=sheet_local,
            )
            provider.generate_image(prompt, str(out))
            images[str(idx)] = {"path": out.name}
        self.ctx.progress("images", "running",
                          f"rendered {len(images)} scene images")

    # ------------------------------------------------------------------
    # Step 6: voice (before video so clip length matches narration)
    # ------------------------------------------------------------------
    def step_voice(self, only_scene: int | None = None) -> None:
        script = self.ctx.state["script"]
        provider = self.ctx.providers["voice"]
        voice_data = self.ctx.state.setdefault("voice", {})
        for scene in self.ctx.state["storyboard"]:
            idx = scene["index"]
            if only_scene is not None and idx != only_scene:
                continue
            out = self.ctx.work_dir / f"voice_{idx:02d}.wav"
            result = provider.synthesize(
                scene["narration"], str(out),
                voice=self.ctx.params.get("voice", "female"),
                language=script.get("language", "en"),
                target_duration=scene.get("planned_duration"),
            )
            voice_data[str(idx)] = {
                "path": out.name,
                "duration": result.duration,
                "word_timings": [w.__dict__ for w in result.word_timings],
            }
            # update the scene budget so clips fit the real narration
            scene["planned_duration"] = max(scene.get("planned_duration", 0),
                                            result.duration + 0.4)

    # ------------------------------------------------------------------
    # Step 7: video clips
    # ------------------------------------------------------------------
    def step_video(self, only_scene: int | None = None) -> None:
        prompts = self.ctx.state["prompts"]
        provider = self.ctx.providers["video"]
        clips = self.ctx.state.setdefault("clips", {})
        for scene in self.ctx.state["storyboard"]:
            idx = scene["index"]
            if only_scene is not None and idx != only_scene:
                continue
            image = self.ctx.work_dir / self.ctx.state["images"][str(idx)]["path"]
            out = self.ctx.work_dir / f"clip_{idx:02d}.mp4"
            result = provider.generate_clip(
                str(image),
                VideoPrompt(prompt=prompts["scenes"][idx]["video_prompt"],
                            negative_prompt=prompts["negative_prompt"],
                            duration=max(3.0, scene.get("planned_duration", 5.0)),
                            motion=scene.get("motion", "zoom_in")),
                str(out),
            )
            clips[str(idx)] = {"path": out.name, "duration": result.duration or scene.get("planned_duration", 5.0)}

    # ------------------------------------------------------------------
    # Step 8: music
    # ------------------------------------------------------------------
    def step_music(self) -> None:
        total = self._estimated_total()
        out = self.ctx.work_dir / "music.wav"
        result = self.ctx.providers["music"].generate_track(
            self.ctx.params.get("music_mood", "cheerful"), total, str(out)
        )
        self.ctx.state["music"] = {"path": out.name, "duration": result.duration,
                                   "credits": result.credits}

    def _estimated_total(self) -> float:
        storyboard = self.ctx.state.get("storyboard", [])
        return 2.6 + 3.4 + sum(float(s.get("planned_duration", 5.0)) for s in storyboard)

    # ------------------------------------------------------------------
    # Step 9: captions (sidecar files; burn-in happens in editing)
    # ------------------------------------------------------------------
    def step_captions(self) -> None:
        voice = self.ctx.state.get("voice", {})
        from app.services.rendering.captions import build_cues, offset_words
        words: list[WordTiming] = []
        cursor = 2.6  # intro card
        for scene in self.ctx.state.get("storyboard", []):
            vd = voice.get(str(scene["index"]))
            if vd:
                words += offset_words(
                    [WordTiming(**w) for w in vd["word_timings"]], cursor + 0.12
                )
            cursor += max(scene.get("planned_duration", 5.0), (vd or {}).get("duration", 0) + 0.5)
        words.sort(key=lambda w: w.start)
        cues = build_cues(words)
        W, H = self.ctx.width, self.ctx.height
        (self.ctx.work_dir / "captions.srt").write_text(to_srt(cues))
        (self.ctx.work_dir / "captions.ass").write_text(
            to_ass(cues, play_res_x=W, play_res_y=H)
        )
        self.ctx.state["captions"] = {"words": [w.__dict__ for w in words],
                                      "cue_count": len(cues)}

    # ------------------------------------------------------------------
    # Step 10: editing
    # ------------------------------------------------------------------
    def step_editing(self) -> None:
        sheet = self.ctx.state["prompts"]["character_sheet"]
        params = self.ctx.params
        W, H = self.ctx.width, self.ctx.height

        intro = self.ctx.work_dir / "intro_card.png"
        outro = self.ctx.work_dir / "outro_card.png"
        render_intro_card(self.ctx.state.get("script", {}).get("title", params["topic"]),
                          sheet, W, H, str(intro))
        render_outro_card(sheet, W, H, str(outro))

        scenes_media: list[SceneMedia] = []
        for scene in self.ctx.state["storyboard"]:
            idx = scene["index"]
            vd = self.ctx.state.get("voice", {}).get(str(idx), {})
            clip = self.ctx.state.get("clips", {}).get(str(idx), {})
            clip_name = clip.get("path", f"clip_{idx:02d}.mp4")
            scenes_media.append(SceneMedia(
                index=idx,
                clip_path=str(self.ctx.work_dir / clip_name),
                clip_planned=float(scene.get("planned_duration", 5.0)),
                voice_path=str(self.ctx.work_dir / vd["path"]) if vd else None,
                voice_duration=float(vd.get("duration", 0.0)),
                word_timings=[WordTiming(**w) for w in vd.get("word_timings", [])],
                chapter_label=scene.get("focus", ""),
                on_screen_text=scene.get("on_screen_text", ""),
            ))
        music = self.ctx.state.get("music", {})
        result = compose(
            scenes_media, str(intro), str(outro),
            str(self.ctx.work_dir / music["path"]) if music else None,
            str(self.ctx.work_dir / "final.mp4"),
            width=W, height=H, fps=self.ctx.fps,
            quality=params.get("quality", "standard"),
            caption_style=params.get("caption_style", "word"),
            work_dir=str(self.ctx.work_dir / "compose_tmp"),
        )
        self.ctx.state["final"] = {
            "path": "final.mp4", "duration": result.duration,
            "chapters": result.chapters, "scene_starts": result.scene_starts,
        }
        self._rewrite_captions_with_true_offsets(result.scene_starts)
        shutil.rmtree(self.ctx.work_dir / "compose_tmp", ignore_errors=True)

    def _rewrite_captions_with_true_offsets(self, scene_starts: dict[int, float]) -> None:
        from app.services.rendering.captions import build_cues, offset_words
        words: list[WordTiming] = []
        for scene in self.ctx.state.get("storyboard", []):
            vd = self.ctx.state.get("voice", {}).get(str(scene["index"]))
            offset = scene_starts.get(scene["index"])
            if vd and offset is not None:
                words += offset_words([WordTiming(**w) for w in vd["word_timings"]],
                                      offset + 0.12)
        words.sort(key=lambda w: w.start)
        cues = build_cues(words)
        (self.ctx.work_dir / "captions.srt").write_text(to_srt(cues))
        (self.ctx.work_dir / "captions.ass").write_text(
            to_ass(cues, play_res_x=self.ctx.width, play_res_y=self.ctx.height)
        )
        self.ctx.state["captions"] = {"words": [w.__dict__ for w in words],
                                      "cue_count": len(cues)}

    # ------------------------------------------------------------------
    # Step 11: thumbnails
    # ------------------------------------------------------------------
    def step_thumbnails(self) -> None:
        sheet = self.ctx.state["prompts"]["character_sheet"]
        title = self.ctx.state.get("script", {}).get("title", self.ctx.params["topic"])
        thumb_dir = self.ctx.work_dir / "thumbnails"
        base = self.ctx.state.get("images", {}).get("0")
        base_path = str(self.ctx.work_dir / base["path"]) if base else None
        landscape = self.ctx.width >= self.ctx.height
        paths = generate_thumbnails(
            base_path, title, sheet, str(thumb_dir),
            width=min(1280, self.ctx.width),
            height=min(720, int(self.ctx.width * 9 / 16)) if landscape else 720,
            count=3)
        rel = [str(Path(p).relative_to(self.ctx.work_dir)) for p in paths]
        self.ctx.state["thumbnails"] = rel

    # ------------------------------------------------------------------
    # Step 12: metadata + preview readiness
    # ------------------------------------------------------------------
    def step_preview(self) -> None:
        script = self.ctx.state.get("script", {})
        kb = self.ctx.state.get("knowledge", {})
        try:
            raw = self.ctx.providers["text"].generate(
                SYSTEM_PROMPT, metadata_brief(script, kb), json_response=True,
                temperature=0.5,
            )
            metadata = json.loads(raw)
        except Exception:
            from app.services.providers.text.local import LocalTextProvider
            metadata = LocalTextProvider().write_metadata(script, kb)
        # merge true chapter times into the description
        chapters = self.ctx.state.get("final", {}).get("chapters", [])
        if chapters:
            lines = ["", "⏱️ Chapters:"]
            for ch in chapters:
                ts = _fmt_ts(ch.get("time", 0))
                lines.append(f"  {ts}  {ch.get('label', '')}")
            metadata["description"] = str(metadata.get("description", "")) + "\n".join(lines) + "\n"
            metadata["chapters"] = chapters
        metadata.setdefault("music_credits", self.ctx.state.get("music", {}).get(
            "credits", "AI Kids Video Studio Music Box (original, royalty-free)"))
        self.ctx.state["metadata"] = metadata


def _fmt_ts(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 60:02d}:{s % 60:02d}"
