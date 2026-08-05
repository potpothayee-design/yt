from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class UploadRecord(Base):
    """History of YouTube upload attempts for a project.

    Uploads are ALWAYS user-initiated. This table keeps an audit trail and
    enough state to retry failed resumable uploads.
    """

    __tablename__ = "upload_records"

    STATUS_REQUESTED = "requested"
    STATUS_UPLOADING = "uploading"
    STATUS_PROCESSING = "processing"
    STATUS_PUBLISHED = "published"
    STATUS_DRAFT = "draft_saved"
    STATUS_SCHEDULED = "scheduled"
    STATUS_FAILED = "failed"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    youtube_video_id: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default=STATUS_REQUESTED)
    privacy: Mapped[str] = mapped_column(String(20), default="private")
    made_for_kids: Mapped[bool] = mapped_column(default=True)
    scheduled_at: Mapped[str | None] = mapped_column(String(40))
    title: Mapped[str | None] = mapped_column(String(200))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    history: Mapped[list | None] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    project = relationship("Project", back_populates="uploads")
