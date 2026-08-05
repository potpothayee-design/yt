"""Job status endpoints + GitHub Actions callback receivers.

The ``/jobs/callback/{id}`` endpoints are unauthenticated-by-user but
protected by the shared ``JOB_CALLBACK_SECRET`` token — the Actions workflow
posts progress, then uploads the finished artifacts, then marks completion.
"""

from __future__ import annotations

import json
import shutil
from datetime import UTC
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.serializers import job_out
from app.core.config import get_settings
from app.core.errors import NotFoundError
from app.core.logging import log_event
from app.db.session import get_db
from app.models.job import PipelineJob
from app.models.project import Project
from app.models.user import User
from app.schemas.common import JobOut
from app.services.pipeline import orchestrator

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, user: User = Depends(get_current_user),
            db: Session = Depends(get_db)) -> JobOut:
    job = db.get(PipelineJob, job_id)
    if not job:
        raise NotFoundError("job")
    project = db.get(Project, job.project_id)
    if project and project.user_id != user.id and not user.is_admin:
        raise NotFoundError("job")
    return job_out(job, db)


# ---------------------------------------------------------------------------
# GitHub Actions callbacks
# ---------------------------------------------------------------------------

def _check_callback_token(x_job_token: str | None) -> None:
    secret = get_settings().JOB_CALLBACK_SECRET
    if not secret or x_job_token != secret:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid callback token")


@router.post("/callback/{job_id}")
def callback_progress(
    job_id: int,
    body: dict,
    db: Session = Depends(get_db),
    x_job_token: str | None = Header(default=None),
) -> dict:
    """Progress update from the Actions runner: {step, status, message}."""
    _check_callback_token(x_job_token)
    job = db.get(PipelineJob, job_id)
    if not job:
        raise NotFoundError("job")
    project = db.get(Project, job.project_id)
    step = body.get("step", "research")
    status_ = body.get("status", "running")
    message = body.get("message", "")
    orchestrator._record_step(db, job, project, step, status_, message)
    if body.get("state"):
        try:
            state_file = orchestrator._project_dir(project.id) / "state.json"
            state_file.parent.mkdir(parents=True, exist_ok=True)
            state_file.write_text(json.dumps(body["state"]))
            orchestrator._persist_milestones(db, project, body["state"])
        except Exception:
            pass
    return {"ok": True}


@router.post("/callback/{job_id}/artifact")
async def callback_artifact(
    job_id: int,
    file: UploadFile = File(...),
    kind: str = Form(...),
    scene_index: int | None = Form(default=None),
    db: Session = Depends(get_db),
    x_job_token: str | None = Header(default=None),
) -> dict:
    """Receive a finished artifact (final.mp4, thumbnails, captions, state.json)."""
    _check_callback_token(x_job_token)
    job = db.get(PipelineJob, job_id)
    if not job:
        raise NotFoundError("job")
    project = db.get(Project, job.project_id)
    pdir = orchestrator._project_dir(project.id)
    pdir.mkdir(parents=True, exist_ok=True)

    filename = Path(file.filename or "artifact.bin").name
    dest = pdir / filename if kind != "thumbnail" else pdir / "thumbnails" / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)

    if kind == "state":
        try:
            state = json.loads(dest.read_text())
            orchestrator._persist_milestones(db, project, state)
        except Exception:
            pass
        return {"ok": True}

    rel = dest.relative_to(pdir.parent.parent)
    orchestrator._replace_asset(db, project.id, kind, scene_index, str(rel))
    if kind == "final_video":
        project.final_video_path = str(rel)
        db.commit()
    if kind == "thumbnail" and scene_index == 0:
        project.thumbnail_path = str(rel)
        db.commit()
    return {"ok": True, "path": str(dest)}


@router.post("/callback/{job_id}/complete")
def callback_complete(
    job_id: int,
    body: dict,
    db: Session = Depends(get_db),
    x_job_token: str | None = Header(default=None),
) -> dict:
    """Final completion signal from the Actions runner."""
    _check_callback_token(x_job_token)
    job = db.get(PipelineJob, job_id)
    if not job:
        raise NotFoundError("job")
    project = db.get(Project, job.project_id)
    if body.get("status") == "failed":
        job.status = "failed"
        job.error = body.get("error", "actions run failed")[:2000]
        project.status = Project.STATUS_FAILED
        project.error = job.error[:1000]
    else:
        job.status = "succeeded"
        project.status = Project.STATUS_REVIEW
    from datetime import datetime
    job.finished_at = datetime.now(UTC)
    db.commit()
    log_event(db, "INFO", f"GitHub Actions job #{job.id} -> {job.status}",
              project_id=project.id)
    return {"ok": True}
