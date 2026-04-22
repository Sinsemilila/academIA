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
