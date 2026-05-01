"""Hash-indexed verdict cache for oracle judge LLM calls.

Speeds up dev iteration by avoiding repeated identical judge calls.
Content-addressed : the cache key is sha256 of (messages_json, judge_model),
so any change to the prompt, the Teacher response, or the model auto-invalidates
the cached entry. No manual `judge_prompt_version` bump needed.

Storage : SQLite at scripts/oracle/.cache/verdicts.sqlite (gitignored).
TTL : 30 days default (configurable via cli purge tool).

Usage in llm_pairwise._call_judge :
    if cfg.get("cache", {}).get("enabled"):
        key = compute_key(messages, model)
        cached = get(key)
        if cached is not None:
            return cached
    # ... real LLM call ...
    put(key, result)
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path

CACHE_DB = Path(__file__).resolve().parent / ".cache" / "verdicts.sqlite"


def _ensure_db() -> None:
    CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(CACHE_DB) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS verdicts (
                key TEXT PRIMARY KEY,
                model TEXT,
                result_json TEXT,
                created_at INTEGER
            )"""
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_created_at ON verdicts(created_at)"
        )


def compute_key(messages: list[dict], model: str) -> str:
    """Content-addressed key. Stable across runs as long as inputs identical."""
    raw = json.dumps(messages, sort_keys=True, ensure_ascii=False) + "||" + model
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get(key: str) -> dict | None:
    """Return cached LLM result dict or None on miss."""
    _ensure_db()
    with sqlite3.connect(CACHE_DB) as conn:
        row = conn.execute(
            "SELECT result_json FROM verdicts WHERE key = ?", (key,)
        ).fetchone()
        if row:
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return None
    return None


def put(key: str, model: str, result: dict | None) -> None:
    """Cache LLM result. None results NOT cached (don't memoize failures)."""
    if result is None:
        return
    _ensure_db()
    with sqlite3.connect(CACHE_DB) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO verdicts VALUES (?, ?, ?, ?)",
            (key, model, json.dumps(result, ensure_ascii=False), int(time.time())),
        )


def stats() -> dict:
    """Return cache stats : count, oldest_age_days, total_size_bytes."""
    _ensure_db()
    with sqlite3.connect(CACHE_DB) as conn:
        row = conn.execute(
            "SELECT COUNT(*), MIN(created_at) FROM verdicts"
        ).fetchone()
        count = row[0] or 0
        min_ts = row[1]
    age_days = (
        (int(time.time()) - min_ts) / 86400 if min_ts else 0
    )
    size_bytes = CACHE_DB.stat().st_size if CACHE_DB.exists() else 0
    return {
        "count": count,
        "oldest_age_days": round(age_days, 1),
        "size_bytes": size_bytes,
        "db_path": str(CACHE_DB),
    }


def purge_older_than(days: int = 30) -> int:
    """Delete entries older than N days. Returns count deleted."""
    _ensure_db()
    cutoff = int(time.time()) - days * 86400
    with sqlite3.connect(CACHE_DB) as conn:
        cur = conn.execute(
            "DELETE FROM verdicts WHERE created_at < ?", (cutoff,)
        )
        return cur.rowcount


def purge_all() -> int:
    """Wipe the entire cache. Returns count deleted."""
    _ensure_db()
    with sqlite3.connect(CACHE_DB) as conn:
        cur = conn.execute("DELETE FROM verdicts")
        return cur.rowcount


# CLI entry point for cache management
def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Oracle verdict cache management")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stats", help="Show cache stats")
    p_purge = sub.add_parser("purge", help="Purge old entries")
    p_purge.add_argument(
        "--days", type=int, default=30, help="Delete entries older than N days"
    )
    p_purge.add_argument(
        "--all", action="store_true", help="Wipe entire cache"
    )
    args = ap.parse_args()

    if args.cmd == "stats":
        s = stats()
        print(f"Cache : {s['count']} entries, oldest {s['oldest_age_days']}d, "
              f"{s['size_bytes']} bytes at {s['db_path']}")
        return 0
    if args.cmd == "purge":
        if args.all:
            n = purge_all()
            print(f"Wiped {n} entries.")
        else:
            n = purge_older_than(args.days)
            print(f"Purged {n} entries older than {args.days}d.")
        return 0
    return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
