#!/usr/bin/env python3
"""Sprint 5 Phase 1.4 — Update n8n workflows for domain ISO migration.

Applies string substitutions to each active workflow's `nodes` JSONB:
- `domaine` → `domain` (SQL columns, JS vars, n8n expressions, JSON keys)
- `"anglais"` → `"en"` (JSON string values)
- `'anglais'` → `'en'` (SQL/JS literals)
- Removes `|| 'anglais'` fallbacks (audit recommendation)

Verified pre-run: "domaine" appears only in technical contexts
(SQL, JS vars, n8n expressions), never in prompt text.
"anglais" as a word appears in French prompts but never with surrounding quotes.

Idempotent: re-running after success is safe (no-op since patterns already replaced).

Backup: creates `workflow_entity_backup_sprint5` table with pre-update nodes.
"""
import os
import json
import sys
import subprocess
from datetime import datetime

DB_USER = "sinse"
DB_NAME = "academie_db"
CONTAINER = "postgres-academie"


def psql(sql: str, fetch: bool = False) -> str:
    cmd = ["docker", "exec", "-i", CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME,
           "-t", "-A", "-q", "-c", sql]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return res.stdout.strip()


def psql_many(sql: str) -> None:
    cmd = ["docker", "exec", "-i", CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME]
    subprocess.run(cmd, input=sql, text=True, check=True)


def update_workflow_nodes(wf_name: str) -> tuple[int, int]:
    """Replace patterns in workflow `nodes` JSONB. Returns (before_size, after_size)."""
    # Fetch current nodes as JSON text
    nodes_text = psql(
        f"SELECT nodes::text FROM workflow_entity WHERE name = '{wf_name}' AND active = true LIMIT 1"
    )
    if not nodes_text:
        print(f"  [SKIP] {wf_name}: not found or inactive")
        return (0, 0)

    before_size = len(nodes_text)
    original = nodes_text

    # Substitutions — order matters
    substitutions = [
        # Remove silent fallbacks `|| 'anglais'` per audit recommendation
        (r"body.domaine || 'anglais'", r"body.domaine"),
        (r"body.domain || 'anglais'", r"body.domain"),
        # Value literals
        ('"anglais"', '"en"'),
        ("'anglais'", "'en'"),
        # Column/field rename (global: SQL columns, JS keys, n8n expressions)
        ("domaine", "domain"),
    ]

    for pattern, replacement in substitutions:
        nodes_text = nodes_text.replace(pattern, replacement)

    after_size = len(nodes_text)

    if nodes_text == original:
        print(f"  [NOOP] {wf_name}: no changes needed (already migrated)")
        return (before_size, after_size)

    # Write back via psql (escape single quotes for SQL literal)
    escaped = nodes_text.replace("'", "''")
    update_sql = (
        f"UPDATE workflow_entity SET nodes = '{escaped}'::jsonb, "
        f"\"updatedAt\" = NOW() "
        f"WHERE name = '{wf_name}' AND active = true;"
    )
    psql_many(update_sql)
    print(f"  [UPDATED] {wf_name}: {before_size} → {after_size} chars")
    return (before_size, after_size)


def backup_workflows() -> None:
    """Create `workflow_entity_backup_sprint5` with pre-migration data."""
    sql = """
    DROP TABLE IF EXISTS workflow_entity_backup_sprint5;
    CREATE TABLE workflow_entity_backup_sprint5 AS
    SELECT id, name, active, nodes, "updatedAt" AS backed_up_at
    FROM workflow_entity
    WHERE active = true;
    """
    psql_many(sql)
    count = psql("SELECT COUNT(*) FROM workflow_entity_backup_sprint5")
    print(f"Backup created: workflow_entity_backup_sprint5 ({count} rows)")


def verify_post_migration() -> None:
    """Check for any remaining 'anglais' (value) or bare 'domaine' (column) in workflows."""
    for pattern, desc in [
        ("'anglais'", "SQL literal 'anglais'"),
        ('"anglais"', "JSON value \"anglais\""),
        ("domaine", "column/var 'domaine'"),
    ]:
        sql = (
            f"SELECT COUNT(*) FROM workflow_entity "
            f"WHERE active = true AND nodes::text LIKE '%{pattern}%'"
        )
        count = psql(sql)
        status = "✓" if count == "0" else "✗"
        print(f"  {status} {desc}: {count} workflows still contain it")


def main() -> int:
    print(f"=== n8n workflow migration — {datetime.now().isoformat()} ===")
    print("\n[1/3] Creating backup...")
    backup_workflows()

    print("\n[2/3] Applying substitutions...")
    workflows = [
        "dify-profil-get",
        "dify-profil-update",
        "dify-snapshot",
        "dify-diagnostic",
        "dify-exam-persist",
        "dify-exam-scoring",
    ]
    for wf in workflows:
        update_workflow_nodes(wf)

    print("\n[3/3] Post-migration verification...")
    verify_post_migration()

    print("\nDone. To rollback: ")
    print("  UPDATE workflow_entity we SET nodes = b.nodes")
    print("  FROM workflow_entity_backup_sprint5 b WHERE we.id = b.id;")
    return 0


if __name__ == "__main__":
    sys.exit(main())
