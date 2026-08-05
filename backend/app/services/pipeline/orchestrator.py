"""Database-backed job orchestration.

Bridges the persistence-agnostic ``PipelineEngine`` with SQLAlchemy models:
creates/resumes jobs, streams step progress into the DB (polled by the
dashboard), registers produced assets, and handles cancel + resume +
partial regeneration.

Two runners are supported:
* ``local``  — background thread in this API process (default)
* ``github`` — dispatched to GitHub Actions (see .github/workflows/generate.yml)
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, ConflictError
from app.core.logging import get_logger, log_event
from app.core.security import decrypt_secret
from app.db.session import SessionLocal
from app.models.asset import Asset
from app.models.job import PipelineJob
from app.models.project import Project
from app.models.setting import ProviderSetting
from app.services.pipeline.engine import (
    STEP_LABELS,
    STEP_NAMES,
    CancelledError,
    EngineContext,
    PipelineEngine,
)
from app.services.providers import get_provider

logger = get_logger("studio.orchestrator")

_SEMAPHORE = threading.Semaphore(get_settings().MAX_PARALLEL_JOBS)
_THREADS: dict[int, threading.Thread] = {}


def utcnow() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# providers
# ---------------------------------------------------------------------------

def build_providers_for_user(db: Session, user_id: int) -> dict[str, Any]:
    """Resolve one provider instance per capability for a user."""
    providers: dict[str, Any] = {}
    for capability in ("text", "image", "video", "voice", "music"):
        row = (
            db.query(ProviderSetting)
            .filter_by(user_id=user_id, capability=capability)
            .one_or_none()
        )
        provider_name = row.provider if row else None
        api_key = decrypt_secret(row.api_key_encrypted) if row else None
        options = row.options if row else None
        providers[capability] = get_provider(capability, provider_name, api_key, options)
    return providers


# ---------------------------------------------------------------------------
# job creation
# ---------------------------------------------------------------------------

def _fresh_steps() -> list[dict[str, Any]]:
    return [{"name": name, "label": STEP_LABELS[name], "status": "pending",
             "message": "", "started_at": None, "finished_at": None}
            for name in STEP_NAMES]


def enqueue_pipeline(db: Session, project: Project, *, runner: str = "local",
                     kind: str = "generate", resume: bool = True) -> PipelineJob:
    """Create a queued full-generation job and start its runner."""
    active = [j for j in project.jobs if j.status in ("queued", "running")]
    if active:
        raise ConflictError("a job is already running for this project")
    job = PipelineJob(project_id=project.id, kind=kind, status="queued",
                      runner=runner, steps=_fresh_steps())
    db.add(job)
    project.status = Project.STATUS_GENERATING
    project.error = None
    db.commit()
    db.refresh(job)
    _start(job.id, resume=resume)
    log_event(db, "INFO", f"Job #{job.id} queued for project '{project.topic}' ({runner} runner)",
              project_id=project.id)
    return job


def enqueue_partial(db: Session, project: Project, *, target: str,
                    scene_index: int | None = None) -> PipelineJob:
    """Targeted regeneration from the Preview page."""
    step_map = {
        "scene": ["images", "video", "captions", "editing", "preview"],
        "thumbnail": ["thumbnails", "preview"],
        "voice": ["voice", "captions", "editing", "preview"],
        "music": ["music", "editing", "preview"],
    }
    if target == "video":  # full regeneration
        return enqueue_pipeline(db, project, kind="regenerate", resume=False)
    steps = step_map.get(target)
    if not steps:
        raise AppError(f"unknown regeneration target '{target}'")
    active = [j for j in project.jobs if j.status in ("queued", "running")]
    if active:
        raise ConflictError("a job is already running for this project")
    job = PipelineJob(project_id=project.id, kind=f"regen_{target}", status="queued",
                      runner="local", steps=_fresh_steps())
    db.add(job)
    project.status = Project.STATUS_GENERATING
    db.commit()
    db.refresh(job)
    _start(job.id, steps=steps, only_scene=scene_index, resume=True)
    log_event(db, "INFO", f"Partial regeneration '{target}' queued (job #{job.id})",
              project_id=project.id, context={"scene_index": scene_index})
    return job


# ---------------------------------------------------------------------------
# local runner thread
# ---------------------------------------------------------------------------

def _start(job_id: int, *, steps: list[str] | None = None, only_scene: int | None = None,
           resume: bool = True) -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        job = db.get(PipelineJob, job_id)
        runner = job.runner if job else "local"
    finally:
        db.close()

    if runner == "github":
        _dispatch_github(job_id, settings)
        return

    thread = threading.Thread(
        target=_run_local, args=(job_id, steps, only_scene, resume),
        name=f"pipeline-job-{job_id}", daemon=True,
    )
    _THREADS[job_id] = thread
    thread.start()


def _run_local(job_id: int, steps: list[str] | None, only_scene: int | None,
               resume: bool) -> None:
    with _SEMAPHORE:
        db = SessionLocal()
        try:
            job = db.get(PipelineJob, job_id)
            if not job:
                return
            project = db.get(Project, job.project_id)
            job.status = "running"
            job.started_at = utcnow()
            db.commit()

            def progress(step: str, status: str, message: str = "") -> None:
                _record_step(db, job, project, step, status, message)

            def cancelled() -> bool:
                db.refresh(job)
                return bool(job.cancel_requested)

            work_dir = _project_dir(project.id)
            ctx = EngineContext(
                work_dir=work_dir,
                params=project.params or {},
                providers=build_providers_for_user(db, project.user_id),
                project_id=project.id,
                progress=progress,
                should_cancel=cancelled,
            )
            engine = PipelineEngine(ctx)
            state = engine.run(steps=steps, only_scene=only_scene, resume=resume)

            _persist_result(db, project, job, state)
            job.status = "succeeded"
            job.finished_at = utcnow()
            job.current_step = None
            project.status = Project.STATUS_REVIEW
            db.commit()
            log_event(db, "INFO", f"Job #{job.id} finished — preview is ready for approval",
                      project_id=project.id)
        except CancelledError:
            job = db.get(PipelineJob, job_id)
            if job:
                job.status = "cancelled"
                job.finished_at = utcnow()
                db.commit()
            log_event(db, "WARNING", f"Job #{job_id} cancelled by user",
                      project_id=job.project_id if job else None)
        except Exception as exc:
            logger.exception("job %s failed", job_id)
            job = db.get(PipelineJob, job_id)
            if job:
                job.status = "failed"
                job.error = str(exc)[:2000]
                job.finished_at = utcnow()
                project = db.get(Project, job.project_id)
                if project:
                    project.status = Project.STATUS_FAILED
                    project.error = str(exc)[:1000]
                db.commit()
                log_event(db, "ERROR", f"Job #{job.id} failed: {exc}",
                          project_id=job.project_id)
        finally:
            db.close()
            _THREADS.pop(job_id, None)


def _record_step(db: Session, job: PipelineJob, project: Project, step: str,
                 status: str, message: str) -> None:
    db.refresh(job)
    steps = list(job.steps or [])
    for entry in steps:
        if entry["name"] == step:
            if status == "running" and entry["status"] != "running":
                entry["started_at"] = utcnow().isoformat()
            entry["status"] = status
            entry["message"] = message
            if status in ("done", "failed", "skipped"):
                entry["finished_at"] = utcnow().isoformat()
    job.steps = steps
    job.current_step = step if status == "running" else job.current_step
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(job, "steps")
    db.commit()
    # milestone persistence for the project detail page
    try:
        state_file = _project_dir(project.id) / "state.json"
        if state_file.exists() and status == "done":
            import json
            state = json.loads(state_file.read_text())
            _persist_milestones(db, project, state)
    except Exception:
        pass


def _persist_milestones(db: Session, project: Project, state: dict) -> None:
    changed = False
    for field_name, state_key in (("knowledge", "knowledge"), ("script", "script"),
                                  ("storyboard", "storyboard"), ("prompts", "prompts"),
                                  ("video_metadata", "metadata")):
        if state.get(state_key):
            setattr(project, field_name, state[state_key])
            changed = True
    if state.get("script", {}).get("title") and not project.title:
        project.title = state["script"]["title"]
        changed = True
    if changed:
        db.commit()


def _persist_result(db: Session, project: Project, job: PipelineJob, state: dict) -> None:
    _persist_milestones(db, project, state)
    kind_map = {
        "images": ("image", lambda i: f"scene_{int(i):02d}.png"),
        "clips": ("video_clip", lambda i: f"clip_{int(i):02d}.mp4"),
        "voice": ("voice", lambda i: f"voice_{int(i):02d}.wav"),
    }
    for state_key, (kind, namer) in kind_map.items():
        for sidx in state.get(state_key, {}):
            rel = f"projects/{project.id}/{namer(sidx)}"
            _replace_asset(db, project.id, kind, int(sidx), rel,
                           duration=(state[state_key][sidx].get("duration")))
    if state.get("music"):
        _replace_asset(db, project.id, "music", None, f"projects/{project.id}/music.wav",
                       duration=state["music"].get("duration"))
    if _project_dir(project.id).joinpath("captions.srt").exists():
        _replace_asset(db, project.id, "captions", None, f"projects/{project.id}/captions.srt")
        _replace_asset(db, project.id, "captions", 9999, f"projects/{project.id}/captions.ass")
    for i, rel_thumb in enumerate(state.get("thumbnails", [])):
        _replace_asset(db, project.id, "thumbnail", i, f"projects/{project.id}/{rel_thumb}")
    if state.get("final"):
        _replace_asset(db, project.id, "final_video", None,
                       f"projects/{project.id}/final.mp4", duration=state["final"].get("duration"))
        project.final_video_path = f"projects/{project.id}/final.mp4"
    if state.get("thumbnails"):
        project.thumbnail_path = f"projects/{project.id}/{state['thumbnails'][0]}"
    db.commit()


def _replace_asset(db: Session, project_id: int, kind: str, scene_index: int | None,
                   rel_key: str, duration: float | None = None) -> None:
    (db.query(Asset)
       .filter_by(project_id=project_id, kind=kind, scene_index=scene_index)
       .delete())
    key = rel_key
    db.add(Asset(project_id=project_id, kind=kind, scene_index=scene_index,
                 path=key, duration=duration, meta={}))
    db.commit()


def _project_dir(project_id: int) -> Path:
    return Path(get_settings().MEDIA_ROOT) / "projects" / str(project_id)


# ---------------------------------------------------------------------------
# GitHub Actions runner
# ---------------------------------------------------------------------------

def _dispatch_github(job_id: int, settings) -> None:
    """Trigger generate.yml; progress/artifacts arrive via callback endpoints."""
    import httpx

    db = SessionLocal()
    try:
        job = db.get(PipelineJob, job_id)
        project = db.get(Project, job.project_id)
        if not settings.GITHUB_DISPATCH_TOKEN or not settings.GITHUB_REPOSITORY:
            logger.warning("GitHub runner not configured — falling back to local run")
            job.runner = "local"
            db.commit()
            _start(job_id)
            return
        payload = {
            "ref": "main",
            "inputs": {
                "job_id": str(job_id),
                "topic": project.topic,
                "params": __import__("json").dumps(project.params or {}),
                "callback_url": f"{settings.PUBLIC_API_URL}/api/v1/jobs/callback/{job_id}",
            },
        }
        resp = httpx.post(
            f"https://api.github.com/repos/{settings.GITHUB_REPOSITORY}/actions/workflows/generate.yml/dispatches",
            headers={
                "Authorization": f"Bearer {settings.GITHUB_DISPATCH_TOKEN}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json=payload, timeout=30,
        )
        if resp.status_code >= 300:
            raise AppError(f"GitHub dispatch failed: {resp.status_code} {resp.text[:200]}")
        job.status = "running"
        job.started_at = utcnow()
        _record_step(db, job, project, "research", "running",
                     "dispatched to GitHub Actions runner")
        log_event(db, "INFO", f"Job #{job.id} dispatched to GitHub Actions",
                  project_id=project.id)
    except Exception as exc:
        logger.exception("github dispatch failed; running locally instead")
        db2 = SessionLocal()
        try:
            job = db2.get(PipelineJob, job_id)
            job.runner = "local"
            db2.commit()
        finally:
            db2.close()
        log_event(db2 := SessionLocal(), "WARNING",
                  f"GitHub dispatch failed ({exc}); running job #{job_id} locally",
                  project_id=job.project_id)
        db2.close()
        _start(job_id)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# control & recovery
# ---------------------------------------------------------------------------

def request_cancel(db: Session, job: PipelineJob) -> None:
    if job.status not in ("queued", "running"):
        raise ConflictError("job is not running")
    job.cancel_requested = True
    db.commit()


def recover_interrupted_jobs(db: Session) -> int:
    """Mark jobs orphaned by a restart as failed (users can resume them)."""
    stale = db.query(PipelineJob).filter(PipelineJob.status.in_(["queued", "running"]))
    count = 0
    for job in stale:
        job.status = "failed"
        job.error = "interrupted by server restart — press Generate to resume"
        job.finished_at = utcnow()
        count += 1
    if count:
        db.commit()
    return count


def job_position_snapshot(db: Session, job: PipelineJob) -> dict[str, Any]:
    done = sum(1 for s in (job.steps or []) if s.get("status") == "done")
    total = len(job.steps or STEP_NAMES)
    return {
        "done_steps": done, "total_steps": total,
        "percent": round(100 * done / max(1, total - 1), 1),
    }
