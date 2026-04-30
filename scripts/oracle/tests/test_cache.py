"""Phase 6 — verdict cache tests."""
from __future__ import annotations

import importlib
import time
from pathlib import Path

import pytest


@pytest.fixture
def fresh_cache(tmp_path, monkeypatch):
    """Use a temp DB for isolation, reset module-level state."""
    import scripts.oracle.cache as cache_mod

    db = tmp_path / "test-verdicts.sqlite"
    monkeypatch.setattr(cache_mod, "CACHE_DB", db)
    yield cache_mod


def test_compute_key_deterministic(fresh_cache):
    """Same input → same key, different input → different key."""
    cache = fresh_cache
    msgs = [{"role": "user", "content": "test"}]
    k1 = cache.compute_key(msgs, "model-a")
    k2 = cache.compute_key(msgs, "model-a")
    k3 = cache.compute_key(msgs, "model-b")
    k4 = cache.compute_key([{"role": "user", "content": "different"}], "model-a")
    assert k1 == k2
    assert k1 != k3
    assert k1 != k4
    assert len(k1) == 64  # sha256 hex


def test_get_returns_none_on_miss(fresh_cache):
    cache = fresh_cache
    assert cache.get("nonexistent-key") is None


def test_put_then_get(fresh_cache):
    cache = fresh_cache
    msgs = [{"role": "user", "content": "test"}]
    key = cache.compute_key(msgs, "judge-a")
    result = {"move": "partial_recast", "confidence": 0.9}
    cache.put(key, "judge-a", result)
    assert cache.get(key) == result


def test_put_none_not_cached(fresh_cache):
    """None results NOT memoized (don't cache failures)."""
    cache = fresh_cache
    key = "test-key"
    cache.put(key, "judge-a", None)
    assert cache.get(key) is None


def test_overwrite_via_replace(fresh_cache):
    cache = fresh_cache
    msgs = [{"role": "user", "content": "x"}]
    key = cache.compute_key(msgs, "judge")
    cache.put(key, "judge", {"v": 1})
    cache.put(key, "judge", {"v": 2})
    assert cache.get(key) == {"v": 2}


def test_purge_older_than(fresh_cache):
    cache = fresh_cache
    import sqlite3
    cache._ensure_db()
    # Insert one fresh + one old entry
    now = int(time.time())
    old = now - 31 * 86400
    with sqlite3.connect(cache.CACHE_DB) as conn:
        conn.execute(
            "INSERT INTO verdicts VALUES (?, ?, ?, ?)",
            ("fresh", "m", '{"x":1}', now),
        )
        conn.execute(
            "INSERT INTO verdicts VALUES (?, ?, ?, ?)",
            ("old", "m", '{"x":2}', old),
        )
    deleted = cache.purge_older_than(days=30)
    assert deleted == 1
    assert cache.get("fresh") == {"x": 1}
    assert cache.get("old") is None


def test_stats(fresh_cache):
    cache = fresh_cache
    cache.put("k1", "m", {"x": 1})
    cache.put("k2", "m", {"x": 2})
    s = cache.stats()
    assert s["count"] == 2
    assert s["size_bytes"] > 0


def test_purge_all(fresh_cache):
    cache = fresh_cache
    cache.put("k1", "m", {"x": 1})
    cache.put("k2", "m", {"x": 2})
    n = cache.purge_all()
    assert n == 2
    assert cache.get("k1") is None
    assert cache.stats()["count"] == 0


def test_unicode_safe(fresh_cache):
    """Cache must handle non-ASCII content (CEFR scenarios in EN/ES/IT/DE/JP/RU)."""
    cache = fresh_cache
    msgs = [{"role": "user", "content": "Café résumé 日本語 русский"}]
    key = cache.compute_key(msgs, "judge")
    cache.put(key, "judge", {"reasoning": "Café équivalent 大学"})
    got = cache.get(key)
    assert got == {"reasoning": "Café équivalent 大学"}


def test_message_order_sensitive(fresh_cache):
    """Message order matters for cache key."""
    cache = fresh_cache
    msgs1 = [{"role": "system", "content": "a"}, {"role": "user", "content": "b"}]
    msgs2 = [{"role": "user", "content": "b"}, {"role": "system", "content": "a"}]
    k1 = cache.compute_key(msgs1, "judge")
    k2 = cache.compute_key(msgs2, "judge")
    # sort_keys=True sorts dict keys, NOT the list order — order matters
    # (we want this since prompt order changes meaning)
    assert k1 != k2
