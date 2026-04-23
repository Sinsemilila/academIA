"""Internal-only endpoints — not user-facing, no JWT guard.

Exposed on the docker-internal network only (academie-net-bridge). The
FastAPI app is not routable from outside the stack so any caller that
can reach these routes already has container-level access.

Currently :
  - POST /internal/cache-stats : relay from LiteLLM custom callback
    (litellm-proxy ships no Python PG driver, so it POSTs here and we
    write to the litellm_db sidecar with asyncpg).
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .. import database  # module-level pool at database.pool

router = APIRouter(prefix="/internal", tags=["internal"])
_log = logging.getLogger("internal.cache_stats")


class CacheStatsPayload(BaseModel):
    request_id: str = Field(..., max_length=200)
    started_at: str
    model: str = Field(..., max_length=200)
    prompt_tokens: int = 0
    cached_tokens: int = 0
    user_id: Optional[str] = Field(None, max_length=200)
    endpoint: Optional[str] = Field(None, max_length=80)


@router.post("/cache-stats", status_code=202)
async def ingest_cache_stats(payload: CacheStatsPayload):
    """Persist cached_tokens telemetry to academie_db.litellm_cache_stats.
    Swallows errors to keep LiteLLM's hot path free."""
    try:
        started = datetime.fromisoformat(payload.started_at.replace("Z", "+00:00"))
    except Exception:
        started = datetime.utcnow()
    try:
        async with database.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO litellm_cache_stats
                  (request_id, started_at, model, prompt_tokens,
                   cached_tokens, user_id, endpoint)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (request_id) DO NOTHING
                """,
                payload.request_id, started, payload.model,
                payload.prompt_tokens, payload.cached_tokens,
                payload.user_id, payload.endpoint,
            )
    except Exception as e:
        _log.warning("cache-stats insert failed: %s", e)
    return {"ok": True}


# ── Session 44 B — model usage relay (groq tier tracker) ─────────────

class ModelUsagePayload(BaseModel):
    model: str = Field(..., max_length=200)
    input_tokens: int = 0
    output_tokens: int = 0
    # Phase A5 — opaque user identifier from LiteLLM callback. Resolved
    # backend-side to an integer users.id (NULL = system / non-attributable).
    user: Optional[str] = Field(None, max_length=200)


async def _resolve_user_id(raw_user: str | None) -> int | None:
    """Resolve a Dify-style user string to an academie users.id.

    Accepted forms (in priority order) :
      * "user_42"             → 42
      * "<int>"               → int
      * <dify uuid string>    → SELECT id FROM users WHERE dify_user_id = $1

    Returns None for unknown strings (logged as system-attributable).
    """
    if not raw_user:
        return None
    s = str(raw_user).strip()
    if s.startswith("user_"):
        try:
            return int(s[5:])
        except (TypeError, ValueError):
            pass
    if s.isdigit():
        return int(s)
    try:
        async with database.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM users WHERE dify_user_id = $1", s,
            )
            return row["id"] if row else None
    except Exception:
        return None


@router.post("/model-usage", status_code=202)
async def ingest_model_usage(payload: ModelUsagePayload):
    """UPSERT today's token counts for a (model, user) pair. Called by the
    LiteLLM callback for every successful completion. Swallow errors to
    keep the proxy hot path free."""
    if payload.input_tokens <= 0 and payload.output_tokens <= 0:
        return {"ok": True}
    user_id = await _resolve_user_id(payload.user)
    try:
        async with database.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO model_usage_daily
                  (usage_date, model, user_id, input_tokens, output_tokens, updated_at)
                VALUES (CURRENT_DATE, $1, $2, $3, $4, NOW())
                ON CONFLICT (usage_date, model, user_id) DO UPDATE SET
                  input_tokens  = model_usage_daily.input_tokens  + EXCLUDED.input_tokens,
                  output_tokens = model_usage_daily.output_tokens + EXCLUDED.output_tokens,
                  updated_at    = NOW()
                """,
                payload.model, user_id, payload.input_tokens, payload.output_tokens,
            )
    except Exception as e:
        _log.warning("model-usage insert failed: %s", e)
    return {"ok": True}


# ── Session 44 V2 — rate-limit snapshot from response headers ─────────

class RateLimitSnapshot(BaseModel):
    model: str = Field(..., max_length=200)
    limit_requests:     Optional[int] = None
    remaining_requests: Optional[int] = None
    reset_requests_sec: Optional[int] = None
    limit_tokens:       Optional[int] = None
    remaining_tokens:   Optional[int] = None
    reset_tokens_sec:   Optional[int] = None


@router.post("/rate-limit-snapshot", status_code=202)
async def ingest_rate_limit_snapshot(payload: RateLimitSnapshot):
    """UPSERT the latest x-ratelimit-* state for a model (last-write-wins).
    Called by the LiteLLM callback after every successful completion ;
    the admin endpoint reads this to display authoritative
    provider-attested counters (no 15-min reconcile lag, no estimation)."""
    if all(getattr(payload, f) is None for f in (
        "limit_requests", "remaining_requests", "reset_requests_sec",
        "limit_tokens", "remaining_tokens", "reset_tokens_sec",
    )):
        return {"ok": True}
    try:
        async with database.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO model_rate_snapshot
                  (model, limit_requests, remaining_requests, reset_requests_sec,
                   limit_tokens, remaining_tokens, reset_tokens_sec, observed_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                ON CONFLICT (model) DO UPDATE SET
                  limit_requests     = COALESCE(EXCLUDED.limit_requests,     model_rate_snapshot.limit_requests),
                  remaining_requests = COALESCE(EXCLUDED.remaining_requests, model_rate_snapshot.remaining_requests),
                  reset_requests_sec = COALESCE(EXCLUDED.reset_requests_sec, model_rate_snapshot.reset_requests_sec),
                  limit_tokens       = COALESCE(EXCLUDED.limit_tokens,       model_rate_snapshot.limit_tokens),
                  remaining_tokens   = COALESCE(EXCLUDED.remaining_tokens,   model_rate_snapshot.remaining_tokens),
                  reset_tokens_sec   = COALESCE(EXCLUDED.reset_tokens_sec,   model_rate_snapshot.reset_tokens_sec),
                  observed_at        = NOW()
                """,
                payload.model,
                payload.limit_requests, payload.remaining_requests, payload.reset_requests_sec,
                payload.limit_tokens, payload.remaining_tokens, payload.reset_tokens_sec,
            )
    except Exception as e:
        _log.warning("rate-limit-snapshot insert failed: %s", e)
    return {"ok": True}
