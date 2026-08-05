"""Simple in-memory sliding-window rate limiter middleware.

For multi-instance deployments replace with a Redis-backed limiter — the
middleware interface is intentionally tiny.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Limit requests per client IP within a time window."""

    def __init__(self, app, max_requests: int = 240, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        # Never rate-limit media streaming / health checks
        if request.url.path.startswith(("/media", "/api/v1/health")):
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        now = time.time()
        q = self._hits[client]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please slow down."},
            )
        q.append(now)
        return await call_next(request)
