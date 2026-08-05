"""YouTube upload management — always user-initiated (Approve Upload flow)."""

from __future__ import annotations

import threading
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_project
from app.core.errors import AppError, NotFoundError
from app.core.logging import get_logger, log_event
from app.db.session import SessionLocal, get_db
from app.models.project import Project
from app.models.upload import UploadRecord
from app.models.user import User
from app.schemas.common import UploadOut
from app.schemas.generation import UploadRequest
from app.services.storage import get_storage
from app.services.storage.local import LocalStorage
from app.services.youtube import oauth as yt_oauth

logger = get_logger("studio.uploads")

router = APIRouter(prefix="", tags=["uploads"])


def utcnow() -> datetime:
    return datetime.now(UTC)


def _append_history(record: UploadRecord, status_: str, message: str) -> None:
    history = list(record.history or [])
    history.append({"time": utcnow().isoformat(), "status": status_, "message": message})
    record.history = history
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(record, "history")


@router.get("/uploads", response_model=list[UploadOut])
def list_uploads(user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)) -> list[UploadOut]:
    project_ids = [p.id for p in db.query(Project.id).filter(Project.user_id == user.id)]
    records = (db.query(UploadRecord)
               .filter(UploadRecord.project_id.in_(project_ids or [-1]))
               .order_by(UploadRecord.created_at.desc()).limit(200).all())
    return [UploadOut.model_validate(r) for r in records]


@router.post("/projects/{project_id}/uploads", response_model=UploadOut,
             status_code=status.HTTP_202_ACCEPTED)
def create_upload(
    body: UploadRequest,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> UploadOut:
    """Approve & upload. Refuses unless the user explicitly confirmed."""
    if not body.confirm:
        raise AppError("upload requires explicit approval (confirm=true)", 422)
    if not project.final_video_path:
        raise AppError("no final video yet — generate the video first", 422)
    creds = yt_oauth.load_credentials(db, project.user_id)
    if not creds:
        raise AppError(
            "YouTube is not connected. Connect your channel on the Settings page first.", 422)
    metadata = project.video_metadata or {}
    record = UploadRecord(
        project_id=project.id, privacy=body.privacy,
        made_for_kids=body.made_for_kids, scheduled_at=body.scheduled_at,
        title=(body.title or metadata.get("title") or project.title or project.topic)[:100],
        status=UploadRecord.STATUS_UPLOADING, attempts=1,
    )
    db.add(record)
    _append_history(record, record.status, "upload approved by user — starting")
    project.status = Project.STATUS_UPLOADING
    db.commit()
    db.refresh(record)

    thread = threading.Thread(
        target=_run_upload,
        args=(record.id, body.model_dump(), metadata),
        name=f"yt-upload-{record.id}", daemon=True,
    )
    thread.start()
    log_event(db, "INFO", "upload approved and started", project_id=project.id,
              context={"upload_id": record.id, "privacy": body.privacy})
    return UploadOut.model_validate(record)


def _resolve_local_path(project: Project) -> str:
    """Absolute path to the final video (staged from S3 if needed)."""
    storage = get_storage()
    if isinstance(storage, LocalStorage):
        return str(storage.abspath(project.final_video_path))
    import tempfile
    data = storage.read_bytes(project.final_video_path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(data)
        return tmp.name


def _thumb_local_path(project: Project) -> str | None:
    if not project.thumbnail_path:
        return None
    try:
        return _resolve_thumb(project)
    except Exception:
        return None


def _resolve_thumb(project: Project) -> str:
    storage = get_storage()
    if isinstance(storage, LocalStorage):
        return str(storage.abspath(project.thumbnail_path))
    import tempfile
    data = storage.read_bytes(project.thumbnail_path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(data)
        return tmp.name


def _run_upload(record_id: int, options: dict, metadata: dict) -> None:
    db = SessionLocal()
    record = db.get(UploadRecord, record_id)
    if not record:
        db.close()
        return
    project = db.get(Project, record.project_id)
    try:
        creds = yt_oauth.load_credentials(db, project.user_id)
        if not creds:
            raise AppError("YouTube connection lost — reconnect in Settings", 422)
        from app.services.youtube.client import YouTubeClient

        client = YouTubeClient(creds)
        description = options.get("description") or metadata.get("description", "")
        # disclosure for synthetic animated media (YouTube policy)
        disclosure = metadata.get("disclosure")
        if disclosure and disclosure not in description:
            description = (description + "\n\n" + disclosure).strip()
        tags = options.get("tags") or metadata.get("tags") or []
        result = client.upload(
            _resolve_local_path(project),
            title=record.title or project.title or project.topic,
            description=description,
            tags=tags,
            privacy=options.get("privacy", "private"),
            made_for_kids=bool(options.get("made_for_kids", True)),
            scheduled_at=options.get("scheduled_at"),
            thumbnail_path=_thumb_local_path(project),
        )
        record.youtube_video_id = result.get("id")
        if options.get("scheduled_at"):
            record.status = UploadRecord.STATUS_SCHEDULED
        elif options.get("privacy") == "private":
            record.status = UploadRecord.STATUS_DRAFT
        else:
            record.status = UploadRecord.STATUS_PUBLISHED
        project.status = Project.STATUS_PUBLISHED
        _append_history(record, record.status,
                        f"uploaded: https://www.youtube.com/watch?v={record.youtube_video_id}")
        log_event(db, "INFO", f"upload complete: video id {record.youtube_video_id}",
                  project_id=project.id)
    except Exception as exc:
        logger.exception("upload %s failed", record_id)
        record.status = UploadRecord.STATUS_FAILED
        record.last_error = str(exc)[:1500]
        record.attempts += 1
        _append_history(record, "failed", str(exc)[:500])
        project.status = Project.STATUS_REVIEW  # back to review, not lost
        log_event(db, "ERROR", f"upload failed: {exc}", project_id=project.id)
    finally:
        db.commit()
        db.close()


@router.post("/uploads/{upload_id}/retry", response_model=UploadOut, status_code=202)
def retry_upload(upload_id: int, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)) -> UploadOut:
    record = db.get(UploadRecord, upload_id)
    if not record:
        raise NotFoundError("upload")
    project = db.get(Project, record.project_id)
    if not project or (project.user_id != user.id and not user.is_admin):
        raise NotFoundError("upload")
    if record.status not in (UploadRecord.STATUS_FAILED, UploadRecord.STATUS_REQUESTED):
        raise AppError("only failed uploads can be retried", 409)
    record.status = UploadRecord.STATUS_UPLOADING
    record.attempts += 1
    _append_history(record, record.status, "retry requested by user")
    db.commit()
    metadata = project.video_metadata or {}
    thread = threading.Thread(
        target=_run_upload,
        args=(record.id, {"privacy": record.privacy, "made_for_kids": record.made_for_kids,
                          "scheduled_at": record.scheduled_at}, metadata),
        name=f"yt-upload-retry-{record.id}", daemon=True,
    )
    thread.start()
    db.refresh(record)
    return UploadOut.model_validate(record)


@router.post("/uploads/{upload_id}/refresh", response_model=UploadOut)
def refresh_upload_status(upload_id: int, user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)) -> UploadOut:
    """Poll YouTube for processing/publish status of an uploaded video."""
    record = db.get(UploadRecord, upload_id)
    if not record:
        raise NotFoundError("upload")
    project = db.get(Project, record.project_id)
    if not project or (project.user_id != user.id and not user.is_admin):
        raise NotFoundError("upload")
    if record.youtube_video_id:
        creds = yt_oauth.load_credentials(db, project.user_id)
        if creds:
            try:
                from app.services.youtube.client import YouTubeClient
                client = YouTubeClient(creds)
                info = client.video_status(record.youtube_video_id)
                if info.get("found"):
                    _append_history(record, record.status,
                                    f"youtube status: {info.get('upload_status')} / "
                                    f"processing {info.get('processing')}")
                    db.commit()
            except Exception as exc:  # noqa: BLE001
                logger.warning("status refresh failed: %s", exc)
    return UploadOut.model_validate(record)
