from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class ProviderSetting(Base):
    """Per-user provider selection + encrypted API key for one capability.

    ``capability`` is one of: text | image | video | voice | music | youtube.
    """

    __tablename__ = "provider_settings"
    __table_args__ = (
        UniqueConstraint("user_id", "capability", name="uq_user_capability"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    capability: Mapped[str] = mapped_column(String(20))
    provider: Mapped[str] = mapped_column(String(40), default="local")
    api_key_encrypted: Mapped[str] = mapped_column(String(2000), default="")
    options: Mapped[dict | None] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    user = relationship("User", back_populates="settings")
