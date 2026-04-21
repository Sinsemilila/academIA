#!/usr/bin/env python3
"""Sprint 6 (Session 36) — inject OBSERVED_LEVEL_v1 directive in llm_session
and llm_onboarding system prompts, for Teacher + Maestro, draft + published.

The JSON schema in OUTPUT_SCHEMA_BLOCK (teacher_prompt.py) already declares
`observed_level`. This script adds a one-paragraph directive telling the LLM
WHEN and HOW to emit it.

Idempotent via marker `OBSERVED_LEVEL_v1`.
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

MARKER = "OBSERVED_LEVEL_v1"

DIRECTIVE = """

=== OBSERVED_LEVEL_v1 ===
À partir du turn 4, évalue le niveau CEFR apparent de l'apprenant·e (A1, A2, B1,
B2, C1 ou C2) à partir de ses productions récentes (complexité syntaxique,
lexique, précision morphologique, aisance discursive) et renseigne le champ
"observed_level" du JSON de sortie. Laisse-le vide ("") si le turn ne te donne
pas assez de signal pour trancher (réponse trop courte, compréhension seule,
etc.). Cette estimation alimente la consolidation du niveau provisoire
(auto-déclaré) vers un niveau validé — l'apprenant·e ne la voit pas
directement, elle n'a donc pas à être discutée ou justifiée dans le feedback.
=== FIN OBSERVED_LEVEL_v1 ===
"""

TARGET_NODES = {"llm_session", "llm_onboarding", "llm_plan_choice"}


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
        if n.get("id") not in TARGET_NODES:
            continue
        for msg in n.get("data", {}).get("prompt_template", []):
            if msg.get("role") != "system":
                continue
            text = msg.get("text", "")
            if MARKER in text:
                continue
            msg["text"] = text + DIRECTIVE
            patched += 1
            break
    return (json.dumps(graph, ensure_ascii=False), patched) if patched else (graph_str, 0)


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
        new_graph, n = patch_graph(graph)
        if not n:
            print(f"  [NOOP] {version}")
            continue
        print(f"  [PATCH] {version}  — {n} node(s) updated")
        if dry_run:
            continue
        esc = new_graph.replace("'", "''")
        psql_exec(f"UPDATE workflows SET graph = '{esc}', updated_at = NOW() WHERE id = '{wf_id}';")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--only", choices=list(APPS.keys()))
    args = p.parse_args()
    for s in ([args.only] if args.only else list(APPS.keys())):
        process(s, dry_run=args.dry_run)
    if not args.dry_run:
        print("\nRestart dify : docker restart dify-api dify-worker")
    return 0


if __name__ == "__main__":
    sys.exit(main())
