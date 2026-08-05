"""Asset browsing + downloads."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.serializers import asset_out
from app.core.errors import NotFoundError, PermissionDeniedError
from app.db.session import get_db
from app.models.asset import Asset
from app.models.project import Project
from app.models.user import User
from app.schemas.common import AssetOut

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("", response_model=list[AssetOut])
def list_assets(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    project_id: int | None = Query(default=None),
    kind: str | None = Query(default=None),
    limit: int = Query(default=200, le=500),
) -> list[AssetOut]:
    project_ids = [p.id for p in db.query(Project.id).filter(Project.user_id == user.id)]
    query = db.query(Asset).filter(Asset.project_id.in_(project_ids or [-1]))
    if project_id is not None:
        query = query.filter(Asset.project_id == project_id)
    if kind:
        query = query.filter(Asset.kind == kind)
    assets = query.order_by(Asset.created_at.desc()).limit(limit).all()
    return [asset_out(a) for a in assets]


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: int, user: User = Depends(get_current_user),
              db: Session = Depends(get_db)) -> AssetOut:
    asset = db.get(Asset, asset_id)
    if not asset:
        raise NotFoundError("asset")
    project = db.get(Project, asset.project_id)
    if project and project.user_id != user.id and not user.is_admin:
        raise PermissionDeniedError()
    return asset_out(asset)
