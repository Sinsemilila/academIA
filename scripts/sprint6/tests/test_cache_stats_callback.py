"""Unit tests for the LiteLLM cache_stats custom callback.

Exercises the pure extraction helpers on both dict-shaped and pydantic-ish
response objects. Skips the DB path (that's integration-tested live via
the dogfood curl in Block 1.2 post-mount).
"""
from __future__ import annotations

import sys
import types
from pathlib import Path
from types import SimpleNamespace

# Callback imports `litellm.integrations.custom_logger.CustomLogger` at the
# top. The `litellm` package is only installed inside the proxy container,
# not on the host where pytest runs. Stub it so the module is importable
# for the pure-function tests below.
_mod = types.ModuleType("litellm")
_mod_int = types.ModuleType("litellm.integrations")
_mod_log = types.ModuleType("litellm.integrations.custom_logger")
class _StubLogger:
    pass
_mod_log.CustomLogger = _StubLogger
sys.modules.setdefault("litellm", _mod)
sys.modules.setdefault("litellm.integrations", _mod_int)
sys.modules.setdefault("litellm.integrations.custom_logger", _mod_log)

# Callback lives in /opt/academie/litellm/ — not on default sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "litellm"))

import cache_stats_callback as cb  # noqa: E402


def test_extract_cached_tokens_from_nested_dict():
    resp = {"usage": {"prompt_tokens": 1200, "prompt_tokens_details": {"cached_tokens": 900}}}
    assert cb._extract_cached_tokens(resp) == 900


def test_extract_cached_tokens_from_nested_objects():
    resp = SimpleNamespace(
        usage=SimpleNamespace(
            prompt_tokens=1200,
            prompt_tokens_details=SimpleNamespace(cached_tokens=512),
        ),
    )
    assert cb._extract_cached_tokens(resp) == 512


def test_extract_cached_tokens_missing_returns_zero():
    assert cb._extract_cached_tokens(None) == 0
    assert cb._extract_cached_tokens({"usage": {}}) == 0
    assert cb._extract_cached_tokens({"usage": {"prompt_tokens_details": None}}) == 0
    assert cb._extract_cached_tokens({"usage": {"prompt_tokens_details": {}}}) == 0


def test_extract_prompt_tokens_dict():
    assert cb._extract_prompt_tokens({"usage": {"prompt_tokens": 1200}}) == 1200
    assert cb._extract_prompt_tokens({}) == 0
    assert cb._extract_prompt_tokens(None) == 0


def test_extract_prompt_tokens_object():
    resp = SimpleNamespace(usage=SimpleNamespace(prompt_tokens=42))
    assert cb._extract_prompt_tokens(resp) == 42
