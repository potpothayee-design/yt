"""Project CRUD + generation control."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_project
from app.api.serializers import job_out, project_detail_out, project_out
from app.core.errors import AppError
from app.core.logging import log_event
from app.db.session import get_db
from app.models.job import PipelineJob
from app.models.project import Project
from app.models.user import User
from app.schemas.common import JobOut, ProjectDetailOut, ProjectOut
from app.schemas.generation import (
    GenerationParams,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    RegenerateRequest,
)
from app.services.pipeline import orchestrator

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
) -> list[ProjectOut]:
    query = db.query(Project).filter(Project.user_id == user.id)
    if status_filter:
        query = query.filter(Project.status == status_filter)
    projects = query.order_by(Project.updated_at.desc()).limit(200).all()
    return [project_out(p) for p in projects]


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    body: ProjectCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectOut:
    params = body.params or GenerationParams(topic=body.topic)
    params.topic = body.topic
    project = Project(
        user_id=user.id, topic=body.topic.strip(), title="",
        status=Project.STATUS_DRAFT,
        params=params.model_dump(),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    log_event(db, "INFO", f"project created: '{body.topic}'", project_id=project.id)
    return project_out(project)


@router.get("/{project_id}", response_model=ProjectDetailOut)
def get_project(project: Project = Depends(get_owned_project),
                db: Session = Depends(get_db)) -> ProjectDetailOut:
    return project_detail_out(project, db)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    body: ProjectUpdateRequest,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> ProjectOut:
    """Update title / script / metadata (Preview page editing)."""
    if body.title is not None:
        project.title = body.title
    if body.script is not None:
        project.script = body.script
        # keep engine state in sync so regeneration uses the edited script
        _sync_state_json(project, "script", body.script)
    if body.video_metadata is not None:
        project.video_metadata = body.video_metadata
    db.commit()
    log_event(db, "INFO", "project updated (manual edit)", project_id=project.id)
    return project_out(project)


def _sync_state_json(project: Project, key: str, value) -> None:
    import json

    from app.core.config import get_settings
    state_file = (get_settings().MEDIA_ROOT and
                  orchestrator._project_dir(project.id) / "state.json")
    try:
        if state_file.exists():
            state = json.loads(state_file.read_text())
            state[key] = value
            # update narration on storyboard scenes too (script edits)
            if key == "script" and state.get("storyboard"):
                narr = {s.get("index"): s.get("narration", "")
                        for s in value.get("scenes", [])}
                for sb in state["storyboard"]:
                    if sb.get("index") in narr and narr[sb["index"]]:
                        sb["narration"] = narr[sb["index"]]
            state_file.write_text(json.dumps(state, indent=2))
    except Exception:
        pass


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> None:
    log_event(db, "INFO", f"project deleted: '{project.topic}'")
    db.delete(project)
    db.commit()


# ---------------------------------------------------------------------------
# generation control
# ---------------------------------------------------------------------------

@router.post("/{project_id}/generate", response_model=JobOut, status_code=202)
def generate(
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
    runner: str = Query(default="local", pattern="^(local|github)$"),
    resume: bool = Query(default=True),
) -> JobOut:
    if project.status in ("generating", "uploading"):
        raise AppError("project already has work in progress", 409)
    job = orchestrator.enqueue_pipeline(db, project, runner=runner, resume=resume)
    return job_out(job, db)


@router.post("/{project_id}/regenerate", response_model=JobOut, status_code=202)
def regenerate(
    body: RegenerateRequest,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> JobOut:
    if project.status not in (Project.STATUS_REVIEW, Project.STATUS_FAILED,
                              Project.STATUS_PUBLISHED):
        raise AppError("regeneration is available once a preview exists", 409)
    if body.target == "video" and body.instruction:
        # user's creative instruction is appended to the params for the rerun
        params = dict(project.params or {})
        params["creative_note"] = body.instruction
        project.params = params
        db.commit()
    job = orchestrator.enqueue_partial(db, project, target=body.target,
                                       scene_index=body.scene_index)
    return job_out(job, db)


@router.get("/{project_id}/jobs", response_model=list[JobOut])
def project_jobs(project: Project = Depends(get_owned_project),
                 db: Session = Depends(get_db)) -> list[JobOut]:
    return [job_out(j, db) for j in project.jobs[:10]]


@router.post("/{project_id}/jobs/{job_id}/cancel", response_model=JobOut)
def cancel_job(
    job_id: int,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> JobOut:
    job = db.get(PipelineJob, job_id)
    if not job or job.project_id != project.id:
        raise AppError("job not found", 404)
    orchestrator.request_cancel(db, job)
    return job_out(job, db)
