"""
Simple in-memory rate limiter for FastAPI.
No external dependency needed — works with asyncio.

Refactor 2026-H2 Phase A5 — added `scope="user"` mode that derives the bucket
key from the authenticated session cookie (falls back to IP if no session).
Single-worker assumption holds today (uvicorn 1 worker). For multi-worker, see
A5 followup roadmap : migrate to slowapi + Redis backend.
"""

import asyncio
import time
from collections import defaultdict
from typing import Literal

from fastapi import HTTPException, Request, status

Scope = Literal["ip", "user"]


class RateLimiter:
    """Token-bucket-style rate limiter, key by IP or by authenticated user_id."""

    def __init__(self):
        # {key: [(timestamp, ...),]}  — key is "ip:<addr>" or "user:<uid>"
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._cleanup_task: asyncio.Task | None = None

    def start_cleanup(self):
        """Start background cleanup task (call once at startup)."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def _periodic_cleanup(self):
        """Remove expired entries every 60s."""
        while True:
            await asyncio.sleep(60)
            now = time.monotonic()
            stale_keys = []
            for key, hits in self._hits.items():
                self._hits[key] = [t for t in hits if now - t < 300]
                if not self._hits[key]:
                    stale_keys.append(key)
            for key in stale_keys:
                del self._hits[key]

    def _get_ip(self, request: Request) -> str:
        """Extract client IP (respects X-Forwarded-For from Cloudflare/nginx)."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def _resolve_user_id(self, request: Request) -> int | None:
        """Look up user_id via the session cookie (no DB call). None if not auth."""
        from . import auth as _auth
        from . import sessions as _sessions

        token = request.cookies.get(_auth.COOKIE_SESSION)
        if not token:
            return None
        sess = await _sessions.get_session(token)
        if not sess:
            return None
        return sess.get("user_id")

    def check(self, request: Request, max_requests: int, window_seconds: int):
        """Per-IP synchronous check (back-compat). Raises 429 if exceeded."""
        self._enforce(f"ip:{self._get_ip(request)}", max_requests, window_seconds)

    async def check_user(self, request: Request, max_requests: int, window_seconds: int):
        """Per-user async check. Falls back to per-IP if no session cookie."""
        user_id = await self._resolve_user_id(request)
        key = f"user:{user_id}" if user_id else f"ip:{self._get_ip(request)}"
        self._enforce(key, max_requests, window_seconds)

    def _enforce(self, key: str, max_requests: int, window_seconds: int) -> None:
        now = time.monotonic()
        self._hits[key] = [t for t in self._hits[key] if now - t < window_seconds]

        if len(self._hits[key]) >= max_requests:
            retry_after = int(window_seconds - (now - self._hits[key][0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Trop de requetes. Reessayez dans {retry_after}s.",
                headers={"Retry-After": str(retry_after)},
            )

        self._hits[key].append(now)


# Singleton — shared across all routes
limiter = RateLimiter()
