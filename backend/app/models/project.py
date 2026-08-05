from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class JSONText(TypeDecorator):
    """Store a payload as JSON text. Portable across SQLite & PostgreSQL."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect) -> str | None:
        return json.dumps(value) if value is not None else None

    def process_result_value(self, value: str | None, dialect) -> Any:
        return json.loads(value) if value else None


class Project(Base):
    """A single video production, from topic to published draft."""

    __tablename__ = "projects"

    STATUS_DRAFT = "draft"
    STATUS_GENERATING = "generating"
    STATUS_REVIEW = "ready_for_review"
    STATUS_FAILED = "failed"
    STATUS_UPLOADING = "uploading"
    STATUS_PUBLISHED = "published"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    topic: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(32), default=STATUS_DRAFT, index=True)

    # Generation parameters chosen on the Generator page
    params: Mapped[dict | None] = mapped_column(JSON, default=dict)

    # Pipeline artifacts (structured payloads)
    knowledge: Mapped[dict | None] = mapped_column(JSON)      # research summary
    script: Mapped[dict | None] = mapped_column(JSON)         # generated script
    storyboard: Mapped[list | None] = mapped_column(JSON)     # scene plan
    prompts: Mapped[dict | None] = mapped_column(JSON)        # image/video prompts
    video_metadata: Mapped[dict | None] = mapped_column(JSON)  # SEO metadata

    # Polished outputs
    final_video_path: Mapped[str | None] = mapped_column(String(600))
    thumbnail_path: Mapped[str | None] = mapped_column(String(600))
    error: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    user = relationship("User", back_populates="projects")
    jobs = relationship(
        "PipelineJob", back_populates="project", cascade="all, delete-orphan",
        order_by="desc(PipelineJob.id)",
    )
    assets = relationship(
        "Asset", back_populates="project", cascade="all, delete-orphan"
    )
    uploads = relationship(
        "UploadRecord", back_populates="project", cascade="all, delete-orphan"
    )
