from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Asset(Base):
    """Any file produced by the pipeline (image, clip, audio, captions...)."""

    __tablename__ = "assets"

    KIND_IMAGE = "image"
    KIND_CLIP = "video_clip"
    KIND_VOICE = "voice"
    KIND_MUSIC = "music"
    KIND_CAPTIONS = "captions"
    KIND_THUMBNAIL = "thumbnail"
    KIND_FINAL = "final_video"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(30), index=True)
    path: Mapped[str] = mapped_column(String(600))  # storage-relative path
    scene_index: Mapped[int | None] = mapped_column(Integer)
    duration: Mapped[float | None] = mapped_column()
    meta: Mapped[dict | None] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    project = relationship("Project", back_populates="assets")
