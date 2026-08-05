from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class StepState(BaseModel):
    name: str
    status: str  # pending | running | done | failed | skipped
    message: str = ""
    started_at: str | None = None
    finished_at: str | None = None


class JobOut(BaseModel):
    id: int
    project_id: int
    kind: str
    status: str
    runner: str
    current_step: str | None
    steps: list[dict[str, Any]] | None
    error: str | None
    created_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class AssetOut(BaseModel):
    id: int
    project_id: int
    kind: str
    path: str
    url: str
    scene_index: int | None
    duration: float | None
    meta: dict[str, Any] | None
    created_at: datetime | None


class ProjectOut(BaseModel):
    id: int
    topic: str
    title: str
    status: str
    params: dict[str, Any] | None
    error: str | None
    final_video_url: str | None
    thumbnail_url: str | None
    created_at: datetime | None
    updated_at: datetime | None


class ProjectDetailOut(ProjectOut):
    knowledge: dict[str, Any] | None
    script: dict[str, Any] | None
    storyboard: list[dict[str, Any]] | None
    prompts: dict[str, Any] | None
    video_metadata: dict[str, Any] | None
    assets: list[AssetOut] = []
    latest_job: JobOut | None = None


class UploadOut(BaseModel):
    id: int
    project_id: int
    youtube_video_id: str | None
    status: str
    privacy: str
    made_for_kids: bool
    scheduled_at: str | None
    attempts: int
    last_error: str | None
    history: list[dict[str, Any]] | None
    created_at: datetime | None
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class LogOut(BaseModel):
    id: int
    project_id: int | None
    level: str
    message: str
    context: dict[str, Any] | None
    created_at: datetime | None

    model_config = {"from_attributes": True}
