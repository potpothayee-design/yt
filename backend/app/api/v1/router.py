"""Aggregate API v1 router."""

from fastapi import APIRouter

from app.api.v1 import (
    assets,
    auth,
    jobs,
    logs,
    meta,
    projects,
    settings,
    uploads,
    youtube,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(jobs.router)
api_router.include_router(assets.router)
api_router.include_router(uploads.router)
api_router.include_router(settings.router)
api_router.include_router(logs.router)
api_router.include_router(youtube.router)
api_router.include_router(meta.router)
