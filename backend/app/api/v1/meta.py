"""Health, catalogs and pipeline metadata (public)."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.settings import ProviderInfo
from app.services.pipeline.engine import STEP_LABELS, STEP_NAMES
from app.services.pipeline.knowledge import TOPIC_KNOWLEDGE
from app.services.providers import provider_catalog
from app.services.rendering.ffmpeg_utils import ffmpeg_version

router = APIRouter(tags=["meta"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "ok": True,
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "ffmpeg": ffmpeg_version(),
        "dev_login": settings.dev_login_enabled,
    }


@router.get("/meta/provider-catalog", response_model=list[ProviderInfo])
def catalog() -> list[ProviderInfo]:
    return [ProviderInfo(**entry) for entry in provider_catalog()]


@router.get("/meta/pipeline-steps")
def pipeline_steps() -> list[dict]:
    return [{"name": n, "label": STEP_LABELS[n]} for n in STEP_NAMES]


@router.get("/meta/topic-ideas")
def topic_ideas() -> list[dict]:
    ideas = [
        {"topic": name.title(), "example_age": "3-6",
         "description": f"{len(v['scene_seeds'])} ready-made visual lessons"}
        for name, v in TOPIC_KNOWLEDGE.items()
    ]
    return sorted(ideas, key=lambda x: x["topic"]) + [
        {"topic": "Any Topic!", "example_age": "3-6",
         "description": "the built-in writer adapts to any subject"}
    ]
