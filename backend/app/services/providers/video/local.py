"""Built-in motion engine (offline video provider).

Turns each rendered scene image into a smooth animated clip with ffmpeg:
Ken-Burns zooms, directional pans, gentle "float" moves, and a fade in/out
at the edges so clips blend seamlessly when merged. Because the pipeline
plans scene durations up front, clips tile perfectly — short provider clips
(5–10 s limits on external services) are merged the exact same way by the
composer, so continuity is guaranteed regardless of provider.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.services.providers.base import ClipResult, VideoPrompt
from app.services.rendering.ffmpeg_utils import run_ffmpeg


class LocalVideoProvider:
    name = "local"
    label = "Built-in Motion Engine (offline)"
    requires_key = False

    def __init__(self, api_key: str | None = None, options: dict | None = None):
        options = options or {}
        settings = get_settings()
        self.width = int(options.get("width", settings.RENDER_WIDTH))
        self.height = int(options.get("height", settings.RENDER_HEIGHT))
        self.fps = int(options.get("fps", settings.RENDER_FPS))
        self.quality = options.get("quality", "standard")

    # ------------------------------------------------------------------
    def generate_clip(self, image_path: str, prompt: VideoPrompt, out_path: str) -> ClipResult:
        W, H, fps = self.width, self.height, self.fps
        frames = max(8, int(prompt.duration * fps))
        vf = self._filter(prompt.motion, W, H, fps, frames)
        crf = {"draft": 24, "standard": 21, "high": 18}.get(self.quality, 21)
        fade_out_start = max(0.0, prompt.duration - 0.4)
        full_vf = (
            f"{vf},fade=t=in:st=0:d=0.35,fade=t=out:st={fade_out_start:.3f}:d=0.35,"
            f"format=yuv420p"
        )
        run_ffmpeg([
            "-loop", "1", "-t", f"{prompt.duration:.3f}", "-i", image_path,
            "-vf", full_vf,
            "-r", str(fps), "-c:v", "libx264", "-preset", "veryfast",
            "-crf", str(crf), "-movflags", "+faststart",
            "-an", out_path,
        ], timeout=600)
        return ClipResult(path=out_path, duration=prompt.duration)

    # ------------------------------------------------------------------
    @staticmethod
    def _filter(motion: str, W: int, H: int, fps: int, frames: int) -> str:
        """Build the per-motion video filter chain."""
        big = f"scale={W * 2}:{H * 2}:flags=lanczos"
        portrait = H > W
        if motion == "zoom_out":
            return (
                f"{big},zoompan=z='max(1.14-0.14*on/{frames},1.0)'"
                f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={fps}"
            )
        if motion.startswith("pan"):
            scaled_h = int(H * 1.18)
            scaled_w = int(W * 1.18)
            if portrait:  # vertical drift for portrait frames
                y_expr = (
                    f"(ih-oh)*(1-min(n,{frames})/{frames})" if motion == "pan_left"
                    else f"(ih-oh)*min(n,{frames})/{frames}"
                )
                return (
                    f"scale=-2:{scaled_h}:flags=lanczos,"
                    f"crop={W}:{H}:x='(iw-ow)/2':y='{y_expr}',setsar=1,fps={fps}"
                )
            x_expr = (
                f"(iw-ow)*min(n,{frames})/{frames}" if motion == "pan_left"
                else f"(iw-ow)*(1-min(n,{frames})/{frames})"
            )
            return (
                f"scale={scaled_w}:-2:flags=lanczos,"
                f"crop={W}:{H}:x='{x_expr}':y='(ih-oh)/2',setsar=1,fps={fps}"
            )
        if motion == "float":
            return (
                f"{big},zoompan=z='1.07+0.05*sin(2*3.14159*on/{max(frames, 1)})'"
                f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={fps}"
            )
        # default: zoom_in
        return (
            f"{big},zoompan=z='min(1+0.14*on/{frames},1.14)'"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={fps}"
        )
