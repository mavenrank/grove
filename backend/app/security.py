"""API security baseline (handoff §18), implemented as ASGI middleware:

  - Cache-Control: no-store on every personalized response (anything under
    /api/test-sessions, /api/history, /api/insights)
  - restrictive security headers on everything
  - fixed-window rate limiting (global + stricter on session creation)
  - request body size caps for event ingestion
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .config import settings

NO_STORE_PREFIXES = (
    "/api/test-sessions",
    "/api/history",
    "/api/insights",
    "/api/me",
)

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    # Local dev needs inline Vite client scripts; production should tighten to nonces.
    "Content-Security-Policy":
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; connect-src 'self'",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        for k, v in SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)
        if request.url.path.startswith(NO_STORE_PREFIXES):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Tiny in-process fixed-window limiter — right-sized for single-learner."""

    def __init__(self, app, global_per_minute: int, create_per_minute: int):
        super().__init__(app)
        self.global_limit = global_per_minute
        self.create_limit = create_per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()
        global _active_limiter
        _active_limiter = self

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def _check(self, key: str, limit: int, now: float) -> bool:
        window = 60.0
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > window:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api"):
            return await call_next(request)
        now = time.monotonic()
        client = request.client.host if request.client else "anon"
        if not self._check(f"global:{client}", self.global_limit, now):
            return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
        if request.method == "POST" and request.url.path == "/api/test-sessions":
            if not self._check(f"create:{client}", self.create_limit, now):
                return JSONResponse({"detail": "too many test sessions; slow down"},
                                    status_code=429)
        return await call_next(request)


class BodySizeMiddleware(BaseHTTPMiddleware):
    """Reject oversized request bodies early (event batches, ingestion)."""

    def __init__(self, app, max_json_body_bytes: int):
        super().__init__(app)
        self.max = max_json_body_bytes

    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            length = request.headers.get("content-length")
            if length and length.isdigit() and int(length) > self.max:
                return JSONResponse({"detail": "request body too large"}, status_code=413)
        return await call_next(request)


def install_security(app) -> None:
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(BodySizeMiddleware, max_json_body_bytes=settings.max_event_body_bytes)
    app.add_middleware(RateLimitMiddleware,
                       global_per_minute=settings.rate_limit_per_minute,
                       create_per_minute=settings.rate_limit_create_session_per_minute)


_active_limiter: RateLimitMiddleware | None = None


def reset_rate_limits() -> None:
    """Test hook: clear all rate-limit windows."""
    if _active_limiter is not None:
        _active_limiter.reset()
