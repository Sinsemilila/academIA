"""Session 39 Block 1.2 — LiteLLM custom callback : persist cached_tokens.

Registered in config.yaml via :
    litellm_settings:
      callbacks: ["cache_stats_callback.proxy_handler_instance"]

LiteLLM loads custom callbacks by importing the dotted path, then calling
`log_success_event` (sync) or `async_log_success_event` (async) on the
handler instance with (kwargs, response_obj, start_time, end_time).

We extract `response_obj.usage.prompt_tokens_details.cached_tokens` and
INSERT one row per request into `litellm_cache_stats` in `litellm_db`.
Failures are swallowed to never break the proxy hot path.

Reads DATABASE_URL (or LITELLM_CACHE_STATS_DSN if set) from env — should
be the same DSN LiteLLM already uses. No extra secret to manage.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

from litellm.integrations.custom_logger import CustomLogger

_log = logging.getLogger("litellm.cache_stats")


def _dsn() -> str:
    return (
        os.environ.get("LITELLM_CACHE_STATS_DSN")
        or os.environ.get("DATABASE_URL")
        or ""
    )


def _extract_cached_tokens(response_obj: Any) -> int:
    """Dig `usage.prompt_tokens_details.cached_tokens` out of either a dict
    or a pydantic/openai response object. Returns 0 if absent."""
    if response_obj is None:
        return 0
    usage = getattr(response_obj, "usage", None) or (
        response_obj.get("usage") if isinstance(response_obj, dict) else None
    )
    if usage is None:
        return 0
    details = getattr(usage, "prompt_tokens_details", None) or (
        usage.get("prompt_tokens_details") if isinstance(usage, dict) else None
    )
    if details is None:
        return 0
    val = getattr(details, "cached_tokens", None) or (
        details.get("cached_tokens") if isinstance(details, dict) else 0
    )
    return int(val or 0)


def _extract_prompt_tokens(response_obj: Any) -> int:
    if response_obj is None:
        return 0
    usage = getattr(response_obj, "usage", None) or (
        response_obj.get("usage") if isinstance(response_obj, dict) else None
    )
    if usage is None:
        return 0
    val = getattr(usage, "prompt_tokens", None) or (
        usage.get("prompt_tokens") if isinstance(usage, dict) else 0
    )
    return int(val or 0)


class CacheStatsLogger(CustomLogger):
    """Persist (request_id, cached_tokens, prompt_tokens) to a sidecar
    Postgres table. Designed so any exception path is swallowed and
    logged — never break the proxy hot path over telemetry."""

    def _insert(self, kwargs: dict, response_obj: Any, start_time) -> None:
        try:
            import psycopg  # psycopg3, available in LiteLLM image
        except Exception:
            try:
                import psycopg2 as psycopg  # type: ignore
            except Exception as e:
                _log.warning("no psycopg available: %s", e)
                return
        dsn = _dsn()
        if not dsn:
            _log.warning("no DSN for cache_stats sidecar")
            return

        request_id = kwargs.get("litellm_call_id") or kwargs.get("request_id") or ""
        if not request_id:
            return
        model = kwargs.get("model") or ""
        prompt_tokens = _extract_prompt_tokens(response_obj)
        cached = _extract_cached_tokens(response_obj)
        user_id = (
            (kwargs.get("litellm_params") or {}).get("metadata", {}).get("user_api_key_user_id")
            or kwargs.get("user")
            or ""
        )
        endpoint = kwargs.get("call_type") or ""

        started = start_time if isinstance(start_time, datetime) else datetime.utcnow()

        try:
            with psycopg.connect(dsn) as conn:  # type: ignore
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO litellm_cache_stats
                          (request_id, started_at, model, prompt_tokens,
                           cached_tokens, user_id, endpoint)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (request_id) DO NOTHING
                        """,
                        (request_id, started, model, prompt_tokens, cached,
                         user_id or None, endpoint or None),
                    )
                conn.commit()
        except Exception as e:
            _log.warning("cache_stats insert failed: %s", e)

    # Sync path — LiteLLM calls this on success for non-async routes
    def log_success_event(self, kwargs, response_obj, start_time, end_time):  # noqa: D401
        self._insert(kwargs, response_obj, start_time)

    # Async path — the one that fires for /v1/chat/completions
    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):  # noqa: D401
        self._insert(kwargs, response_obj, start_time)


proxy_handler_instance = CacheStatsLogger()
