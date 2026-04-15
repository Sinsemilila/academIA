"""Reconcile token tracking against OpenAI's own Usage API.

Hits GET https://api.openai.com/v1/organization/usage/completions for the
current UTC day and returns input+output tokens. Used as the third leg of
the triple safety net (local tiktoken + LiteLLM SpendLogs + OpenAI authoritative).

Returns None on any failure (no admin key, network error, parse error, etc.)
so the caller can fall back to LiteLLM/local without crashing.
"""
from __future__ import annotations

import logging
import os
from datetime import date, datetime, time, timezone

import httpx

logger = logging.getLogger("academie-api.openai_reconcile")

ADMIN_KEY_PATH = os.environ.get(
    "OPENAI_ADMIN_KEY_PATH",
    "/run/academie-secrets/openai-admin-key",
)
USAGE_URL = "https://api.openai.com/v1/organization/usage/completions"
TIMEOUT_S = 10.0


def _read_admin_key() -> str | None:
    """Return the admin key contents (stripped) or None if file missing/empty."""
    if not os.path.exists(ADMIN_KEY_PATH):
        return None
    try:
        with open(ADMIN_KEY_PATH) as f:
            key = f.read().strip()
        return key or None
    except OSError:
        return None


async def reconcile_openai_usage(target_day: date | None = None) -> int | None:
    """Total input+output tokens for the given UTC day per OpenAI's Usage API.

    target_day: defaults to today UTC. The API is bucketed; we sum across the
                single 1d bucket's results.
    Returns: int total tokens, or None on any error.
    """
    key = _read_admin_key()
    if key is None:
        return None
    day = target_day or datetime.now(timezone.utc).date()
    start_ts = int(datetime.combine(day, time.min, tzinfo=timezone.utc).timestamp())
    params = {"start_time": start_ts, "bucket_width": "1d"}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
            r = await client.get(
                USAGE_URL,
                headers={"Authorization": f"Bearer {key}"},
                params=params,
            )
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.warning("openai_reconcile failed: %s", e)
        return None

    total = 0
    for bucket in data.get("data", []):
        for result in bucket.get("results", []):
            total += int(result.get("input_tokens", 0)) + int(result.get("output_tokens", 0))
    return total
