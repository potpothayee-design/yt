"""Model -> API schema serialization with storage URLs."""

from __future__ import annotations

from app.models.asset import Asset
from app.models.job import PipelineJob
from app.models.project import Project
from app.schemas.common import AssetOut, JobOut, ProjectDetailOut, ProjectOut
from app.services.pipeline.orchestrator import job_position_snapshot
from app.services.storage import get_storage


def asset_out(asset: Asset) -> AssetOut:
    storage = get_storage()
    return AssetOut(
        id=asset.id, project_id=asset.project_id, kind=asset.kind, path=asset.path,
        url=storage.url(asset.path), scene_index=asset.scene_index,
        duration=asset.duration, meta=asset.meta, created_at=asset.created_at,
    )


def job_out(job: PipelineJob, db=None) -> JobOut:
    out = JobOut.model_validate(job)
    if db is not None:
        snap = job_position_snapshot(db, job)
        steps = out.steps or []
        # attach progress snapshot as a pseudo-field consumed by the UI
        for s in steps:
            s.setdefault("percent", snap["percent"])
        out.steps = steps
    return out


def project_out(project: Project) -> ProjectOut:
    storage = get_storage()
    return ProjectOut(
        id=project.id, topic=project.topic, title=project.title,
        status=project.status, params=project.params, error=project.error,
        final_video_url=storage.url(project.final_video_path) if project.final_video_path else None,
        thumbnail_url=storage.url(project.thumbnail_path) if project.thumbnail_path else None,
        created_at=project.created_at, updated_at=project.updated_at,
    )


def project_detail_out(project: Project, db) -> ProjectDetailOut:
    base = project_out(project)
    assets = sorted(project.assets, key=lambda a: (a.kind, a.scene_index or 0))
    latest_job = project.jobs[0] if project.jobs else None
    return ProjectDetailOut(
        **base.model_dump(),
        knowledge=project.knowledge, script=project.script,
        storyboard=project.storyboard, prompts=project.prompts,
        video_metadata=project.video_metadata,
        assets=[asset_out(a) for a in assets],
        latest_job=job_out(latest_job, db) if latest_job else None,
    )
