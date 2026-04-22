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
SCOPED_TABLES = [
    "messages",
    "conversations",
    "end_users",
    "app_model_configs",
    "app_dataset_joins",
    "api_tokens",
    "workflows",
    "workflow_runs",
    "workflow_app_logs",
    "app_annotation_settings",
    "installed_apps",
    "apps",  # only if the app still has a row here
]


def count(table: str, app_id: str) -> int | None:
    """Return row count for the given app_id, or None if the table/column doesn't exist."""
    try:
        raw = psql_query(f"SELECT COUNT(*) FROM {table} WHERE app_id = '{app_id}';")
        return int(raw) if raw else 0
    except Exception:
        # Table doesn't exist in this Dify version, or no app_id column → skip
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
    """Single transaction. Reverse FK order (child first)."""
    sql = ["BEGIN;"]
    for t in SCOPED_TABLES:
        # Only include tables whose app_id column exists — skip silently if not.
        if count(t, app_id) is None:
            continue
        sql.append(f"DELETE FROM {t} WHERE app_id = '{app_id}';")
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
    for t in SCOPED_TABLES:
        c = count(t, args.app_id)
        if c is None:
            continue
        total += c
        marker = "  " if c == 0 else " *"
        print(f"{marker} {t:<28} {c}")
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
    post = sum((count(t, args.app_id) or 0) for t in SCOPED_TABLES)
    print(f"▶ post-delete total rows referencing app_id : {post}")
    return 0 if post == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
