"""Standalone pipeline runner — used by GitHub Actions for long jobs.

Usage (local):
    python -m app.workers.runner --standalone --topic "ABCs" \
        --params '{"target_age":"3-6","length_seconds":30}' --out ./dist

Usage (GitHub Actions): the workflow passes --callback-url and --job-token so
the runner reports progress and uploads artifacts back to the dashboard API.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.services.pipeline.engine import STEP_LABELS, EngineContext, PipelineEngine


def _report_stdout(step: str, status: str, message: str = "") -> None:
    print(json.dumps({"event": "progress", "step": step,
                      "label": STEP_LABELS.get(step, step),
                      "status": status, "message": message}), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Kids Video Studio pipeline runner")
    parser.add_argument("--standalone", action="store_true",
                        help="run without a database, writing to --out")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--params", default="{}",
                        help="JSON generation params (age, length, style...)")
    parser.add_argument("--out", default="./dist")
    parser.add_argument("--callback-url", default="")
    parser.add_argument("--job-token", default="")
    args = parser.parse_args()

    params = json.loads(args.params)
    params.setdefault("topic", args.topic)
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    posts_enabled = bool(args.callback_url and args.job_token)

    def progress(step: str, status: str, message: str = "") -> None:
        _report_stdout(step, status, message)
        if posts_enabled:
            _post(args.callback_url, args.job_token,
                  {"step": step, "status": status, "message": message})

    from app.services.providers import get_provider
    providers = {cap: get_provider(cap)
                 for cap in ("text", "image", "video", "voice", "music")}

    ctx = EngineContext(work_dir=out_dir, params=params, providers=providers,
                        progress=progress)
    engine = PipelineEngine(ctx)
    try:
        state = engine.run()
    except Exception as exc:  # noqa: BLE001
        _report_stdout("error", "failed", str(exc))
        if posts_enabled:
            _post(args.callback_url + "/complete", args.job_token,
                  {"status": "failed", "error": str(exc)})
        return 1

    if posts_enabled:
        _push_artifacts(args.callback_url, args.job_token, out_dir, state)
        _post(args.callback_url + "/complete", args.job_token, {"status": "succeeded"})
    _report_stdout("preview", "done", "standalone run complete")
    print(f"\nArtifacts written to: {out_dir}", flush=True)
    return 0


def _post(url: str, token: str, payload: dict) -> None:
    import httpx

    try:
        httpx.post(url, json=payload, headers={"X-Job-Token": token}, timeout=30)
    except Exception as exc:  # noqa: BLE001
        print(f"callback post failed: {exc}", file=sys.stderr)


def _push_artifacts(url: str, token: str, out_dir: Path, state: dict) -> None:
    """Upload finished artifacts back to the dashboard API."""
    import httpx

    uploads: list[tuple[str, str, int | None]] = [("state", "state.json", None)]
    if (out_dir / "final.mp4").exists():
        uploads.append(("final_video", "final.mp4", None))
    for i in range(3):
        p = out_dir / "thumbnails" / f"thumbnail_{i + 1}.jpg"
        if p.exists():
            uploads.append(("thumbnail", f"thumbnails/thumbnail_{i + 1}.jpg", i))
    if (out_dir / "captions.srt").exists():
        uploads.append(("captions", "captions.srt", None))
    with httpx.Client(timeout=600) as client:
        for kind, rel, sidx in uploads:
            path = out_dir / rel
            if not path.exists():
                continue
            data = {"kind": kind}
            if sidx is not None:
                data["scene_index"] = str(sidx)
            try:
                client.post(
                    f"{url}/artifact",
                    headers={"X-Job-Token": token},
                    data=data,
                    files={"file": (path.name, path.open("rb"))},
                )
            except Exception as exc:  # noqa: BLE001
                print(f"artifact upload failed ({rel}): {exc}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
