"""AI Kids Video Studio — FastAPI application entrypoint.

Run:  uvicorn app.main:app --host 0.0.0.0 --port 8000
Docs: http://localhost:8000/docs   (OpenAPI UI)
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import RateLimitMiddleware
from app.db.session import SessionLocal, init_db

logger = get_logger("studio.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging()
    init_db()
    if not settings.SECRET_KEY or settings.SECRET_KEY.startswith("dev-"):
        logger.warning(
            "SECRET_KEY is not set — using an ephemeral development key. "
            "Set SECRET_KEY in production!"
        )
    # recover jobs orphaned by a previous crash/restart
    from app.services.pipeline.orchestrator import recover_interrupted_jobs
    db = SessionLocal()
    try:
        recovered = recover_interrupted_jobs(db)
        if recovered:
            logger.info("recovered %d interrupted job(s) — they can be resumed", recovered)
    finally:
        db.close()
    logger.info("%s v%s ready", settings.APP_NAME, settings.APP_VERSION)
    yield


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if request.url.path.startswith("/media"):
            # allow the dashboard to stream media
            response.headers.setdefault("Cache-Control", "public, max-age=3600")
        return response


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Turn a simple topic into a complete, reviewed, kid-safe educational "
            "video — research, script, storyboard, animation, narration, captions, "
            "music, editing and YouTube draft preparation. Uploads only ever happen "
            "after explicit user approval."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    app.include_router(api_router)

    media_root = Path(settings.MEDIA_ROOT)
    media_root.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=media_root), name="media")

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):  # pragma: no cover
        logger.exception("unhandled error on %s: %s", request.url.path, exc)
        return JSONResponse(status_code=500, content={"detail": "internal server error"})

    @app.get("/", include_in_schema=False)
    def root():
        return {"name": settings.APP_NAME, "version": settings.APP_VERSION,
                "docs": "/docs", "health": "/api/v1/health"}

    return app


app = create_app()
