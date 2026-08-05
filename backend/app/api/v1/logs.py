"""Event log queries for the Logs page."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.log import LogEntry
from app.models.project import Project
from app.models.user import User
from app.schemas.common import LogOut

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("", response_model=list[LogOut])
def list_logs(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    level: str | None = Query(default=None),
    project_id: int | None = Query(default=None),
    limit: int = Query(default=200, le=1000),
) -> list[LogOut]:
    project_ids = [p.id for p in db.query(Project.id).filter(Project.user_id == user.id)]
    query = db.query(LogEntry).filter(
        (LogEntry.project_id.in_(project_ids or [-1])) | (LogEntry.project_id.is_(None))
    )
    if level:
        query = query.filter(LogEntry.level == level.upper())
    if project_id is not None:
        query = query.filter(LogEntry.project_id == project_id)
    entries = query.order_by(LogEntry.created_at.desc()).limit(limit).all()
    return [LogOut.model_validate(e) for e in entries]
