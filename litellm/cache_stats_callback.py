"""Session 39 Block 1.2 — LiteLLM custom callback : cached_tokens telemetry.

Registered in config.yaml via :
    litellm_settings:
      callbacks: ["cache_ext.cache_stats_callback.proxy_handler_instance"]

LiteLLM loads custom callbacks by importing the dotted path, then calling
`log_success_event` (sync) or `async_log_success_event` (async) on the
handler instance with (kwargs, response_obj, start_time, end_time).

We extract `response_obj.usage.prompt_tokens_details.cached_tokens` and
POST a small JSON payload to academie-api which persists it to the
`litellm_cache_stats` sidecar in litellm_db.

Why HTTP instead of direct PG write : the LiteLLM container image ships
no Python PG driver (psycopg/asyncpg absent, Prisma is JS-based) and
installing one at runtime is both fragile and sandbox-blocked. academie-api
already talks to Postgres and rebuilds cleanly — the relay keeps the
LiteLLM container image pristine.

All failures are swallowed : telemetry must never break the proxy hot path.
"""
from __future__ import annotations

import json
import logging
import os
import urllib.request
from typing import Any

from litellm.integrations.custom_logger import CustomLogger

_log = logging.getLogger("litellm.cache_stats")

# Relay endpoint on academie-api (same docker network → hostname resolves)
RELAY_URL = os.environ.get(
    "LITELLM_CACHE_STATS_RELAY",
    "http://academie-api:8000/internal/cache-stats",
)
# Session 44 B — model usage relay (per-model daily tokens, tier tracker).
MODEL_USAGE_RELAY_URL = os.environ.get(
    "LITELLM_MODEL_USAGE_RELAY",
    "http://academie-api:8000/internal/model-usage",
)
# Map every form LiteLLM might pass in kwargs["model"] (provider-prefixed,
# raw provider name, or our config alias) → the model_group we track in
# model_usage_daily. Covers the observed variants across versions of
# LiteLLM (tested against LiteLLM_SpendLogs — the "model" column is the
# underlying provider model, not the alias).
_MODEL_GROUP_BY_NAME = {
    "groq-standard": "groq-standard",
    "groq/llama-3.3-70b-versatile": "groq-standard",
    "llama-3.3-70b-versatile": "groq-standard",
    "groq-snapshot": "groq-snapshot",
    "groq/llama-3.1-8b-instant": "groq-snapshot",
    "llama-3.1-8b-instant": "groq-snapshot",
    "groq-qwen": "groq-qwen",
    "groq/qwen/qwen3-32b": "groq-qwen",
    "qwen/qwen3-32b": "groq-qwen",
}
RELAY_TIMEOUT_S = 1.5


def _extract_cached_tokens(response_obj: Any) -> int:
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
    """Relay cached_tokens stats to academie-api via HTTP POST.
    Errors are logged and dropped — never propagate to the proxy."""

    def _payload(self, kwargs: dict, response_obj: Any, start_time) -> dict | None:
        request_id = kwargs.get("litellm_call_id") or kwargs.get("request_id") or ""
        if not request_id:
            return None
        prompt_tokens = _extract_prompt_tokens(response_obj)
        cached = _extract_cached_tokens(response_obj)
        # Only bother relaying if we actually have usage data
        if prompt_tokens == 0 and cached == 0:
            return None

        started_iso = (
            start_time.isoformat()
            if hasattr(start_time, "isoformat") else str(start_time)
        )
        return {
            "request_id": request_id,
            "started_at": started_iso,
            "model": kwargs.get("model") or "",
            "prompt_tokens": prompt_tokens,
            "cached_tokens": cached,
            "user_id": (
                (kwargs.get("litellm_params") or {}).get("metadata", {}).get("user_api_key_user_id")
                or kwargs.get("user") or ""
            ) or None,
            "endpoint": kwargs.get("call_type") or None,
        }

    def _post(self, url: str, payload: dict) -> None:
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, data=data, method="POST",
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=RELAY_TIMEOUT_S).read()
        except Exception as e:
            _log.warning("relay %s failed: %s", url, e)

    def _model_usage_payload(self, kwargs: dict, response_obj: Any) -> dict | None:
        """Return a {model, input_tokens, output_tokens} dict for a tracked
        model_group, or None for everything else (no-op relay). Normalizes
        whatever LiteLLM passes (alias, provider-prefixed, raw provider)
        into our canonical model_group label."""
        raw = kwargs.get("model") or ""
        # Also try response_obj.model as a fallback (some LiteLLM versions
        # populate that and not kwargs when a fallback cascade fires).
        if raw not in _MODEL_GROUP_BY_NAME:
            resp_model = getattr(response_obj, "model", None) or (
                response_obj.get("model") if isinstance(response_obj, dict) else None
            )
            if resp_model and resp_model in _MODEL_GROUP_BY_NAME:
                raw = resp_model
        group = _MODEL_GROUP_BY_NAME.get(raw)
        if not group:
            return None
        usage = getattr(response_obj, "usage", None) or (
            response_obj.get("usage") if isinstance(response_obj, dict) else None
        )
        if usage is None:
            return None
        pt = getattr(usage, "prompt_tokens", None) or (
            usage.get("prompt_tokens") if isinstance(usage, dict) else 0
        )
        ct = getattr(usage, "completion_tokens", None) or (
            usage.get("completion_tokens") if isinstance(usage, dict) else 0
        )
        pt, ct = int(pt or 0), int(ct or 0)
        if pt == 0 and ct == 0:
            return None
        return {"model": group, "input_tokens": pt, "output_tokens": ct}

    def log_success_event(self, kwargs, response_obj, start_time, end_time):  # noqa: D401
        cache_payload = self._payload(kwargs, response_obj, start_time)
        if cache_payload:
            self._post(RELAY_URL, cache_payload)
        model_payload = self._model_usage_payload(kwargs, response_obj)
        if model_payload:
            self._post(MODEL_USAGE_RELAY_URL, model_payload)

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):  # noqa: D401
        cache_payload = self._payload(kwargs, response_obj, start_time)
        if cache_payload:
            self._post(RELAY_URL, cache_payload)
        model_payload = self._model_usage_payload(kwargs, response_obj)
        if model_payload:
            self._post(MODEL_USAGE_RELAY_URL, model_payload)


proxy_handler_instance = CacheStatsLogger()
