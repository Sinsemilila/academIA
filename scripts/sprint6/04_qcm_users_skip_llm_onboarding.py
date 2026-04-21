#!/usr/bin/env python3
"""Sprint 6 (Session 36) — route QCM users directly to llm_session.

Problem : as long as `profils_eleves.niveau_global` is empty (which is the
case for all QCM users until the legacy n8n snapshot runs — often never),
`code_profil_check.profil_present` stays False, which routes every turn to
`llm_onboarding`. That prompt does FASE 2 observational diagnostic + textual
bilan + goodbye loop, conflicting with our Session 36 consolidation
mechanism.

Fix : patch the code_profil_check python function so `profil_present = true`
is ALSO true when `learner_profile_summary` is non-empty (= QCM completed).
QCM users thereafter go through `if_profil` → cas1 → code_turn_check →
llm_session, which emits proper JSON with `observed_level`.

Idempotent via marker `QCM_AS_PROFIL_v1` embedded in the python code body.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

DB_CONTAINER = "postgres-academie"
DB_USER = "sinse"
DB_NAME = "academie_db"

APPS = {
    "teacher": "39565197-c9d1-4d5b-b66f-18925de236d9",
    "maestro": "47b0529c-b3a3-4651-8717-759e666172c9",
}

MARKER = "QCM_AS_PROFIL_v1"

# Original line :  present = bool(text) and text.strip().startswith('[PROFIL ELEVE]')
ORIG = "present = bool(text) and text.strip().startswith('[PROFIL ELEVE]')"
REPLACEMENT = (
    "# QCM_AS_PROFIL_v1 — Session 36 : treat QCM users (non-empty "
    "learner_profile_summary) as having a profile so routing bypasses "
    "llm_onboarding.\n    "
    "_has_legacy = bool(text) and text.strip().startswith('[PROFIL ELEVE]')\n    "
    "_has_qcm = bool((learner_profile_summary or '').strip())\n    "
    "present = _has_legacy or _has_qcm"
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


def patch_graph(graph_str: str) -> tuple[str, int]:
    graph = json.loads(graph_str)
    patched = 0
    for n in graph.get("nodes", []):
        if n.get("id") != "code_profil_check":
            continue
        code = n.get("data", {}).get("code", "")
        if MARKER in code:
            continue
        if ORIG not in code:
            print(f"  [WARN] code_profil_check body does not contain expected line — skip")
            continue
        n["data"]["code"] = code.replace(ORIG, REPLACEMENT)
        patched += 1
        break
    return (json.dumps(graph, ensure_ascii=False), patched) if patched else (graph_str, 0)


def process(slug: str, dry_run: bool) -> None:
    app_id = APPS[slug]
    print(f"\n=== {slug.upper()} ===")
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
        new_graph, n = patch_graph(graph)
        if not n:
            print(f"  [NOOP] {version}")
            continue
        print(f"  [PATCH] {version}")
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
        print("\nRestart : docker restart dify-api dify-worker")
    return 0


if __name__ == "__main__":
    sys.exit(main())
