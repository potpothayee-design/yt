"""The automated editor — merges every asset into one polished video.

Responsibilities ("Step 9: Editing"):
* Normalize every scene clip (any provider) to a uniform WxH/fps/codec
* Branded intro & outro cards with gentle motion
* Seamless crossfade transitions between all clips
* Perfectly timed narration mix (per-scene audio placement)
* Quiet, loopable background music bed + loudness normalization (EBU R128)
* Burned-in captions with animated word highlighting (+ SRT/ASS sidecars)
* Chapter timeline for YouTube metadata
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw

from app.services.providers.base import WordTiming
from app.services.rendering.captions import Cue, build_cues, offset_words
from app.services.rendering.ffmpeg_utils import probe_duration, run_ffmpeg
from app.services.rendering.fonts import get_font, text_size

TRANSITION = 0.45
INTRO_SECONDS = 2.6
OUTRO_SECONDS = 3.4


@dataclass
class SceneMedia:
    index: int
    clip_path: str          # animated scene clip (silent)
    clip_planned: float     # duration the clip was rendered for
    voice_path: str | None  # narration audio (may be any codec)
    voice_duration: float
    word_timings: list[WordTiming] = field(default_factory=list)
    chapter_label: str = ""
    on_screen_text: str = ""


@dataclass
class ComposeResult:
    final_path: str
    duration: float
    chapters: list[dict]
    scene_starts: dict[int, float]


# ---------------------------------------------------------------------------
# caption PNG rendering
# ---------------------------------------------------------------------------

def render_caption_png(words: list[tuple[str, bool]], out_path: str,
                       box_w: int, font_size: int) -> tuple[int, int]:
    """Render one caption state to a transparent PNG.

    ``words`` = [(word, highlighted)]. Returns (width, height) of the PNG.
    """
    font = get_font(font_size)
    pad_x, pad_y = int(font_size * 0.55), int(font_size * 0.42)
    probe = Image.new("RGBA", (10, 10))
    pd = ImageDraw.Draw(probe)
    space_w, _ = text_size(pd, " ", font)
    widths = [text_size(pd, w, font)[0] for w, _ in words]
    text_w = sum(widths) + space_w * (len(words) - 1)
    line_h = int(font_size * 1.35)
    scale = min(1.0, (box_w - 2 * pad_x) / max(1, text_w))
    if scale < 1.0:
        font = get_font(max(16, int(font_size * scale)))
        space_w, _ = text_size(pd, " ", font)
        widths = [text_size(pd, w, font)[0] for w, _ in words]
        text_w = sum(widths) + space_w * (len(words) - 1)
        line_h = int(font.size * 1.35)

    img = Image.new("RGBA", (text_w + 2 * pad_x, line_h + 2 * pad_y), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, img.width - 1, img.height - 1],
                           radius=int(line_h * 0.5), fill=(18, 18, 32, 190))
    x = pad_x
    cy = img.height / 2
    for (word, hot), w in zip(words, widths, strict=True):
        color = "#FFD93D" if hot else "#FFFFFF"
        draw.text((x, cy - line_h / 2 + 2), word, font=font, fill=color,
                  stroke_width=max(1, font_size // 16), stroke_fill="#1E2140")
        x += w + space_w
    img.save(out_path, "PNG")
    return img.width, img.height


def build_caption_overlays(cues: list[Cue], work_dir: Path, W: int, H: int,
                           style: str = "word") -> list[dict]:
    """Render every caption state PNG; returns overlay descriptors.

    style="word": one PNG per word (animated highlight).
    style="cue": one PNG per cue (static while visible).
    """
    out: list[dict] = []
    m = min(W, H)
    font_size = max(26, int(m * 0.055))
    if style == "cue":
        for ci, cue in enumerate(cues):
            path = work_dir / f"cap_{ci:04d}.png"
            render_caption_png([(w.word, False) for w in cue.words], str(path),
                               int(W * 0.9), font_size)
            out.append({"path": str(path), "start": cue.start, "end": cue.end})
        return out
    wi = 0
    for cue in cues:
        all_words = cue.words
        for hot_idx, wt in enumerate(all_words):
            path = work_dir / f"cap_{wi:04d}.png"
            render_caption_png(
                [(w.word, j == hot_idx) for j, w in enumerate(all_words)],
                str(path), int(W * 0.9), font_size,
            )
            out.append({"path": str(path), "start": wt.start,
                        "end": wt.end + (0.08 if hot_idx < len(all_words) - 1 else 0.15)})
            wi += 1
    return out


# ---------------------------------------------------------------------------
# normalization pre-pass (any provider's clip -> uniform silent h264)
# ---------------------------------------------------------------------------

def _normalize_clip(src: str, target: float, out: str, W: int, H: int, fps: int,
                    is_image: bool) -> None:
    base = f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,fps={fps}"
    args: list[str] = []
    if is_image:
        # subtle zoom on the card image
        frames = max(8, int(target * fps))
        args += ["-loop", "1", "-t", f"{target:.3f}", "-i", src]
        vf = (f"scale={W * 2}:{H * 2}:flags=lanczos,"
              f"zoompan=z='min(1+0.09*on/{frames},1.09)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
              f":d=1:s={W}x{H}:fps={fps},setsar=1,format=yuv420p")
        args += ["-vf", vf, "-t", f"{target:.3f}"]
    else:
        args += ["-i", src]
        vf = base + ",format=yuv420p"
        args += ["-vf", vf, "-an", "-t", f"{target:.3f}"]
    args += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", out]
    run_ffmpeg(args, timeout=600)
    # extend short clips by cloning the last frame (smooth continuity fix)
    have = probe_duration(out)
    if have < target - 0.05:
        tmp = out + ".pad.mp4"
        run_ffmpeg([
            "-i", out,
            "-vf", f"tpad=stop_mode=clone:stop={target - have:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-an", tmp,
        ], timeout=600)
        Path(tmp).replace(out)


# ---------------------------------------------------------------------------
# main entry
# ---------------------------------------------------------------------------

def compose(scenes: list[SceneMedia], intro_card: str | None, outro_card: str | None,
            music_path: str | None, out_path: str, *, width: int, height: int,
            fps: int, quality: str, caption_style: str, work_dir: str,
            cue_source_words: list[WordTiming] | None = None) -> ComposeResult:
    W, H = width, height
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)

    # 1) per-clip targets ----------------------------------------------------
    targets: dict[int, float] = {}
    for s in scenes:
        targets[s.index] = max(s.clip_planned, s.voice_duration + 0.5, 3.2)

    ordered: list[tuple[str, float, int | None]] = []  # (src, dur, scene_index|None)
    if intro_card:
        ordered.append((intro_card, INTRO_SECONDS, None))
    ordered += [(s.clip_path, targets[s.index], s.index)
                for s in sorted(scenes, key=lambda x: x.index)]
    if outro_card:
        ordered.append((outro_card, OUTRO_SECONDS, None))

    # 2) normalize ------------------------------------------------------------
    norm_paths: list[str] = []
    for i, (src, dur, _idx) in enumerate(ordered):
        is_image = src.lower().endswith((".png", ".jpg", ".jpeg"))
        norm = str(work / f"norm_{i:02d}.mp4")
        _normalize_clip(src, dur, norm, W, H, fps, is_image)
        norm_paths.append(norm)

    # 3) graph inputs ---------------------------------------------------------
    inputs: list[str] = []
    file_idx = 0  # counts ffmpeg INPUT FILES (arg counts differ per input type)
    for p in norm_paths:
        inputs += ["-i", p]
        file_idx += 1
    voice_inputs: dict[int, int] = {}  # scene_index -> input idx
    for s in scenes:
        if s.voice_path and s.voice_duration > 0.1:
            voice_inputs[s.index] = file_idx
            inputs += ["-i", s.voice_path]
            file_idx += 1
    music_idx = None
    if music_path:
        music_idx = file_idx
        inputs += ["-i", music_path]
        file_idx += 1

    # 4) video chain: crossfades ----------------------------------------------
    durs = [d for (_p, d, _i) in ordered]
    scene_of_input: list[int | None] = [i for (_p, _d, i) in ordered]
    filters: list[str] = []
    cur_label = "0:v"
    cur_dur = durs[0]
    starts: list[float] = [0.0]
    for j in range(1, len(norm_paths)):
        offset = cur_dur - TRANSITION
        lbl = f"vx{j}"
        filters.append(
            f"[{cur_label}][{j}:v]xfade=transition=fade:duration={TRANSITION}:offset={max(0.05, offset):.3f}[{lbl}]"
        )
        cur_label = lbl
        cur_dur = max(0.05, offset) + durs[j]
        starts.append(max(0.05, offset))
    total_video = cur_dur
    scene_starts = {scene_of_input[j]: starts[j] for j in range(len(ordered))
                    if scene_of_input[j] is not None}

    # 5) captions --------------------------------------------------------------
    all_words: list[WordTiming] = []
    for s in scenes:
        if s.index in scene_starts:
            all_words += offset_words(s.word_timings, scene_starts[s.index] + 0.12)
    all_words.sort(key=lambda w: w.start)
    cues = build_cues(all_words)
    overlays: list[dict] = []
    if caption_style != "off" and all_words:
        n_words = sum(len(c.words) for c in cues)
        effective_style = "cue" if n_words > 260 else caption_style
        overlays = build_caption_overlays(cues, work, W, H, effective_style)
    cap_in_start = file_idx
    for ov in overlays:
        inputs += ["-loop", "1", "-i", ov["path"]]
        file_idx += 1

    vpre = cur_label
    for k, ov in enumerate(overlays):
        lbl = f"vc{k}"
        x = "(main_w-overlay_w)/2"
        y = f"main_h*{0.84 if W >= H else 0.80:.2f}-overlay_h/2"
        filters.append(
            f"[{vpre}][{cap_in_start + k}:v]overlay=x={x}:y={y}"
            f":enable='between(t,{ov['start']:.3f},{ov['end']:.3f})'[{lbl}]"
        )
        vpre = lbl
    filters.append(f"[{vpre}]format=yuv420p[vout]")

    # 6) audio mix --------------------------------------------------------------
    filters += _audio_stage(scenes, voice_inputs, music_idx, scene_starts, total_video)

    # 7) run the master pass -----------------------------------------------------
    crf = {"draft": 24, "standard": 21, "high": 18}.get(quality, 21)
    args = inputs + [
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", "[afin]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf),
        "-r", str(fps), "-c:a", "aac", "-b:a", "160k",
        "-movflags", "+faststart", "-shortest", out_path,
    ]
    run_ffmpeg(args, timeout=1800)

    # 8) chapters ----------------------------------------------------------------
    chapters = _chapters(scenes, scene_starts, total_video,
                         has_outro=outro_card is not None)

    return ComposeResult(
        final_path=out_path,
        duration=probe_duration(out_path) or total_video,
        chapters=chapters,
        scene_starts={k: round(v, 3) for k, v in scene_starts.items()},
    )


def _audio_stage(scenes: list[SceneMedia], voice_inputs: dict[int, int],
                 music_idx: int | None, scene_starts: dict[int, float],
                 total_video: float) -> list[str]:
    """Narration placement + music bed + loudness normalization filters."""
    filters: list[str] = []
    a_mix_labels: list[str] = []
    for s in scenes:
        inp = voice_inputs.get(s.index)
        if inp is None or s.index not in scene_starts:
            continue
        delay_ms = int((scene_starts[s.index] + 0.12) * 1000)
        lbl = f"ad{s.index}"
        filters.append(f"[{inp}:a]aformat=sample_rates=22050:channel_layouts=mono,"
                       f"adelay={delay_ms}|{delay_ms},apad[{lbl}]")
        a_mix_labels.append(lbl)
    if a_mix_labels:
        joined = "".join(f"[{label}]" for label in a_mix_labels)
        filters.append(f"{joined}amix=inputs={len(a_mix_labels)}:normalize=0[vmix]")
    else:
        filters.append(f"anullsrc=r=22050:cl=mono:d={total_video:.3f}[vmix]")
    if music_idx is not None:
        filters.append(
            f"[{music_idx}:a]aformat=sample_rates=22050:channel_layouts=mono,"
            f"aloop=loop=-1:size=2e9,atrim=0:{total_video:.3f},volume=0.85[mus]"
        )
        filters.append(
            "[vmix][mus]amix=inputs=2:normalize=0,"
            "loudnorm=I=-14:TP=-1.5:LRA=11[aout]"
        )
    else:
        filters.append("[vmix]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    filters.append(f"[aout]atrim=0:{total_video:.3f},asetpts=PTS-STARTPTS[afin]")
    return filters


def _chapters(scenes: list[SceneMedia], scene_starts: dict[int, float],
              total_video: float, has_outro: bool) -> list[dict]:
    chapters = [{"time": 0.0, "label": "Welcome!"}]
    for s in scenes:
        if s.index in scene_starts:
            label = (s.chapter_label or s.on_screen_text or f"Scene {s.index + 1}")[:40]
            chapters.append({"time": round(scene_starts[s.index], 2), "label": label})
    if has_outro:
        chapters.append({"time": round(total_video - OUTRO_SECONDS, 2),
                         "label": "Recap & goodbye"})
    return chapters
