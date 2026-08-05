"""Database engine & session management.

SQLite is used for development out of the box; set ``DATABASE_URL`` to a
PostgreSQL DSN in production (the same models work on both — JSON columns use
portable ``sqlalchemy.JSON``).
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    settings = get_settings()
    url = settings.sqlalchemy_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Create tables if they do not exist.

    For schema evolution in production use Alembic; ``create_all`` keeps
    first-run and CI frictionless.
    """
    from app import models  # noqa: F401  (ensures all models are registered)

    Base.metadata.create_all(bind=engine)


def get_db() -> Session:  # FastAPI dependency
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
