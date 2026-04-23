"""
Refactor 2026-H2 Phase A1 — Redis opaque session store.

Replaces JWT-in-localStorage with HttpOnly cookies pointing to Redis-stored
opaque tokens. Sliding TTL 7 days, instant revocation, CSRF double-submit.

Schema :
  session:<token>            HASH  user_id, username, ip, user_agent,
                                   csrf_token, created_at, last_active
                             TTL   7 days (sliding, refreshed on each get)

  user_sessions:<user_id>    SET   {token1, token2, ...}  (reverse index)
                             no TTL — manually pruned on session expiry/delete
"""
from __future__ import annotations

import os
import secrets
import time
import hashlib
from typing import Any

import redis.asyncio as redis_asyncio

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis-academie:6379/0")
SESSION_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days
SESSION_KEY_PREFIX = "session:"
USER_INDEX_PREFIX = "user_sessions:"

_pool: redis_asyncio.Redis | None = None


def _client() -> redis_asyncio.Redis:
    global _pool
    if _pool is None:
        _pool = redis_asyncio.from_url(
            REDIS_URL, encoding="utf-8", decode_responses=True
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def short_id(token: str) -> str:
    """16-char SHA1 prefix — exposed to clients in /me/sessions list to allow
    targeted revoke without leaking the actual session token."""
    return hashlib.sha1(token.encode()).hexdigest()[:16]


async def create_session(
    user_id: int, username: str, ip: str, user_agent: str
) -> tuple[str, str]:
    """Create a new session ; return (session_token, csrf_token)."""
    token = secrets.token_urlsafe(48)
    csrf_token = secrets.token_urlsafe(32)
    r = _client()
    key = f"{SESSION_KEY_PREFIX}{token}"
    pipe = r.pipeline()
    pipe.hset(key, mapping={
        "user_id": str(user_id),
        "username": username,
        "ip": ip or "",
        "user_agent": (user_agent or "")[:512],
        "csrf_token": csrf_token,
        "created_at": _now_iso(),
        "last_active": _now_iso(),
    })
    pipe.expire(key, SESSION_TTL_SECONDS)
    pipe.sadd(f"{USER_INDEX_PREFIX}{user_id}", token)
    await pipe.execute()
    return token, csrf_token


async def get_session(token: str) -> dict[str, Any] | None:
    """Lookup session ; refresh TTL (sliding) ; return dict or None."""
    if not token:
        return None
    r = _client()
    key = f"{SESSION_KEY_PREFIX}{token}"
    data = await r.hgetall(key)
    if not data:
        return None
    pipe = r.pipeline()
    pipe.hset(key, "last_active", _now_iso())
    pipe.expire(key, SESSION_TTL_SECONDS)
    await pipe.execute()
    data["user_id"] = int(data["user_id"])
    return data


async def delete_session(token: str) -> None:
    """Delete one session + remove from user reverse index."""
    if not token:
        return
    r = _client()
    key = f"{SESSION_KEY_PREFIX}{token}"
    data = await r.hgetall(key)
    pipe = r.pipeline()
    pipe.delete(key)
    if data and "user_id" in data:
        pipe.srem(f"{USER_INDEX_PREFIX}{data['user_id']}", token)
    await pipe.execute()


async def delete_session_by_short_id(user_id: int, short: str) -> bool:
    """Find token in user's reverse index where short_id matches, delete it.
    Returns True if found+deleted."""
    r = _client()
    tokens = await r.smembers(f"{USER_INDEX_PREFIX}{user_id}")
    for tok in tokens:
        if short_id(tok) == short:
            await delete_session(tok)
            return True
    return False


async def delete_all_sessions_for_user(user_id: int, except_token: str | None = None) -> int:
    """Delete all sessions for a user (optionally keeping one). Returns count deleted."""
    r = _client()
    tokens = await r.smembers(f"{USER_INDEX_PREFIX}{user_id}")
    deleted = 0
    for tok in tokens:
        if except_token and tok == except_token:
            continue
        await delete_session(tok)
        deleted += 1
    if not except_token:
        await r.delete(f"{USER_INDEX_PREFIX}{user_id}")
    return deleted


async def list_sessions_for_user(user_id: int, current_token: str | None = None) -> list[dict[str, Any]]:
    """List sessions for /me/sessions. Returns short_id, ip, ua, created_at,
    last_active, is_current. Prunes stale entries (in set but not in store)."""
    r = _client()
    tokens = await r.smembers(f"{USER_INDEX_PREFIX}{user_id}")
    out = []
    stale = []
    for tok in tokens:
        data = await r.hgetall(f"{SESSION_KEY_PREFIX}{tok}")
        if not data:
            stale.append(tok)
            continue
        out.append({
            "id": short_id(tok),
            "ip": data.get("ip", ""),
            "user_agent": data.get("user_agent", ""),
            "created_at": data.get("created_at"),
            "last_active": data.get("last_active"),
            "is_current": current_token == tok,
        })
    if stale:
        await r.srem(f"{USER_INDEX_PREFIX}{user_id}", *stale)
    out.sort(key=lambda s: s.get("last_active") or "", reverse=True)
    return out
