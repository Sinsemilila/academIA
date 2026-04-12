"""
Simple in-memory rate limiter for FastAPI.
No external dependency needed — works with asyncio.
Limits are per-IP, auto-cleanup every 60s.
"""

import time
import asyncio
from collections import defaultdict
from fastapi import Request, HTTPException, status


class RateLimiter:
    """Token-bucket-style rate limiter per IP."""

    def __init__(self):
        # {ip: [(timestamp, ...),]}
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
            stale_ips = []
            for ip, hits in self._hits.items():
                self._hits[ip] = [t for t in hits if now - t < 300]
                if not self._hits[ip]:
                    stale_ips.append(ip)
            for ip in stale_ips:
                del self._hits[ip]

    def _get_ip(self, request: Request) -> str:
        """Extract client IP (respects X-Forwarded-For from Cloudflare/nginx)."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def check(self, request: Request, max_requests: int, window_seconds: int):
        """
        Check rate limit. Raises 429 if exceeded.
        Call this at the start of route handlers.
        """
        ip = self._get_ip(request)
        now = time.monotonic()

        # Prune old hits outside window
        self._hits[ip] = [t for t in self._hits[ip] if now - t < window_seconds]

        if len(self._hits[ip]) >= max_requests:
            retry_after = int(window_seconds - (now - self._hits[ip][0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Trop de requetes. Reessayez dans {retry_after}s.",
                headers={"Retry-After": str(retry_after)},
            )

        self._hits[ip].append(now)


# Singleton — shared across all routes
limiter = RateLimiter()
