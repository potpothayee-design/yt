"""Shared FastAPI dependencies: current user, project ownership."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.project import Project
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "authentication required")
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired token")
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")
    return user


def get_owned_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = db.get(Project, project_id)
    if not project or (project.user_id != user.id and not user.is_admin):
        raise NotFoundError("project")
    return project
