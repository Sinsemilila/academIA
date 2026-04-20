#!/usr/bin/env python3
"""Sprint 5 Phase 5 hotfix — revert the <learner_profile> prepend in llm_onboarding.

Fix for : Dify runtime error "Variable #start.learner_profile_summary# not found".
The onboarding branch bypasses code_turn_check AND does not allow {{#start.X#}}
refs in llm_onboarding. Solution : revert that specific prepend, keep every
other patch.

Idempotent.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

DB_CONTAINER = "postgres-academie"
DB_USER = "sinse"
DB_NAME = "academie_db"

APPS = {
    "teacher": "39565197-c9d1-4d5b-b66f-18925de236d9",
    "maestro": "47b0529c-b3a3-4651-8717-759e666172c9",
}

# Exactly matches what 11_update_dify_onboarding_qcm.py prepended.
ONBOARDING_BLOCK_RE = re.compile(
    r"<learner_profile>\s*\{\{\#start\.learner_profile_summary#\}\}\s*</learner_profile>\s*\n\s*"
    r"Si le bloc ci-dessus n'est pas vide.*?\(Phase 2\)\.\s*\n\s*\n\s*",
    re.DOTALL,
)


def psql_q(sql: str) -> str:
    return subprocess.run(
        ["docker", "exec", "-i", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-t", "-A", "-c", sql],
        capture_output=True, text=True, check=True,
    ).stdout.rstrip("\n")


def psql_exec(sql: str) -> None:
    subprocess.run(
        ["docker", "exec", "-i", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-v", "ON_ERROR_STOP=1"],
        input=sql, text=True, check=True,
    )


def patch_graph(graph_str: str) -> tuple[str, bool]:
    graph = json.loads(graph_str)
    changed = False
    for n in graph.get("nodes", []):
        if n.get("id") != "llm_onboarding":
            continue
        for msg in n["data"].get("prompt_template", []):
            if msg.get("role") != "system":
                continue
            original = msg.get("text", "")
            new_text = ONBOARDING_BLOCK_RE.sub("", original, count=1)
            if new_text != original:
                msg["text"] = new_text
                changed = True
        break
    if not changed:
        return graph_str, False
    return json.dumps(graph, ensure_ascii=False), True


def process(slug: str, dry_run: bool) -> None:
    app_id = APPS[slug]
    print(f"\n=== {slug.upper()}  (app_id={app_id}) ===")
    rows = psql_q(f"""
        (SELECT id || '|' || version FROM workflows
         WHERE app_id = '{app_id}' AND version = 'draft' LIMIT 1)
        UNION ALL
        (SELECT id || '|' || version FROM workflows
         WHERE app_id = '{app_id}' AND version != 'draft'
         ORDER BY updated_at DESC LIMIT 1)
    """)
    for line in rows.splitlines():
        if not line:
            continue
        wf_id, version = line.split("|", 1)
        graph = psql_q(f"SELECT graph FROM workflows WHERE id = '{wf_id}'")
        new_graph, changed = patch_graph(graph)
        if not changed:
            print(f"  [NOOP] {version}")
            continue
        print(f"  [REVERT] {version}  ({len(graph)} → {len(new_graph)} chars)")
        if dry_run:
            continue
        esc = new_graph.replace("'", "''")
        psql_exec(f"UPDATE workflows SET graph = '{esc}', updated_at = NOW() WHERE id = '{wf_id}';")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    for s in APPS:
        process(s, dry_run=args.dry_run)
    if not args.dry_run:
        print("\nRestart dify : docker restart dify-api dify-worker")
    return 0


if __name__ == "__main__":
    sys.exit(main())
