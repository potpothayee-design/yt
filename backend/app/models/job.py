from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class PipelineJob(Base):
    """One execution of the generation pipeline for a project.

    ``steps`` is a list of dicts: ``{"name", "status", "message",
    "started_at", "finished_at"}`` — one entry per pipeline stage. Persisted
    after every transition so interrupted jobs can resume from the first
    incomplete step.
    """

    __tablename__ = "pipeline_jobs"

    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(40), default="generate")
    status: Mapped[str] = mapped_column(String(20), default=STATUS_QUEUED, index=True)
    current_step: Mapped[str | None] = mapped_column(String(40))
    steps: Mapped[list | None] = mapped_column(JSON, default=list)
    # "local" = in-process worker, "github" = GitHub Actions runner
    runner: Mapped[str] = mapped_column(String(20), default="local")
    error: Mapped[str | None] = mapped_column(Text)
    cancel_requested: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)

    project = relationship("Project", back_populates="jobs")
