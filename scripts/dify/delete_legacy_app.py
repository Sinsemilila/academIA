"""Session 39 Block 2b — safe DELETE of a legacy Dify app.

Only call this on apps that are CONFIRMED orphan (not referenced by
webapp/.env, not wired in n8n workflows, not in active scripts).

Flow :
  1. SELECT counts per table touched by the delete (dry-run output).
  2. SELECT a predump of rows (messages + conversations) → /tmp JSON.
  3. If --apply : DELETE inside one transaction.
  4. Verify 0 rows post-delete.

Usage :
  python3 scripts/dify/delete_legacy_app.py <uuid> --dry-run   # default
  python3 scripts/dify/delete_legacy_app.py <uuid> --apply
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dify_db import psql_exec, psql_query

# Tables touched by a Dify app delete. Ordered to respect FK (child → parent).
# Does NOT touch global tables (users, accounts, sites, plugins).
# (table, FK column pointing to apps.id). Most tables use `app_id` but the
# `apps` table itself uses `id` — the bug that let orphans survive delete
# in Session 39 Block 2b. The `sites` table joins via `app_id` in its
# Dify schema variant, confirmed present.
SCOPED_TABLES: list[tuple[str, str]] = [
    ("messages", "app_id"),
    ("conversations", "app_id"),
    ("end_users", "app_id"),
    ("app_model_configs", "app_id"),
    ("app_dataset_joins", "app_id"),
    ("api_tokens", "app_id"),
    ("workflows", "app_id"),
    ("workflow_runs", "app_id"),
    ("workflow_app_logs", "app_id"),
    ("app_annotation_settings", "app_id"),
    ("installed_apps", "app_id"),
    ("sites", "app_id"),
    ("apps", "id"),  # ← bug fix : apps table uses `id` PK, not `app_id`
]


def count(table: str, col: str, app_id: str) -> int | None:
    """Return row count for the given id, or None if table/column doesn't exist."""
    try:
        raw = psql_query(f"SELECT COUNT(*) FROM {table} WHERE {col} = '{app_id}';")
        return int(raw) if raw else 0
    except Exception:
        return None


def predump(app_id: str, ts: str) -> Path:
    """Dump messages + conversations rows to a JSON file for safety."""
    out = Path(f"/tmp/dify_delete_predump_{ts}_{app_id[:8]}.json")
    msgs_raw = psql_query(
        f"SELECT id, query, answer, created_at FROM messages WHERE app_id = '{app_id}';"
    )
    convs_raw = psql_query(
        f"SELECT id, name, created_at FROM conversations WHERE app_id = '{app_id}';"
    )
    out.write_text(json.dumps({
        "app_id": app_id,
        "messages_raw": msgs_raw,
        "conversations_raw": convs_raw,
        "ts": ts,
    }, indent=2))
    return out


def apply_delete(app_id: str) -> None:
    """Single transaction. Reverse FK order (child first, apps last)."""
    sql = ["BEGIN;"]
    for t, col in SCOPED_TABLES:
        if count(t, col, app_id) is None:
            continue
        sql.append(f"DELETE FROM {t} WHERE {col} = '{app_id}';")
    sql.append("COMMIT;")
    psql_exec("\n".join(sql))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("app_id", help="UUID of the Dify app to prune")
    ap.add_argument("--apply", action="store_true",
                    help="Actually DELETE. Without this flag, only counts are shown.")
    args = ap.parse_args()

    print(f"▶ Inspecting app {args.app_id}")
    total = 0
    for t, col in SCOPED_TABLES:
        c = count(t, col, args.app_id)
        if c is None:
            continue
        total += c
        marker = "  " if c == 0 else " *"
        print(f"{marker} {t:<28} ({col:<8}) {c}")
    print(f"  TOTAL rows to remove : {total}")

    if total == 0:
        print("▶ Nothing to do.")
        return 0

    ts = time.strftime("%Y-%m-%d-%H%M%S")
    dump_path = predump(args.app_id, ts)
    print(f"▶ predump → {dump_path}")

    if not args.apply:
        print("▶ DRY-RUN. Re-run with --apply to actually DELETE.")
        return 0

    print("▶ Applying DELETE (single transaction)")
    apply_delete(args.app_id)

    # Verify
    post = sum((count(t, col, args.app_id) or 0) for t, col in SCOPED_TABLES)
    print(f"▶ post-delete total rows referencing app_id : {post}")
    return 0 if post == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
