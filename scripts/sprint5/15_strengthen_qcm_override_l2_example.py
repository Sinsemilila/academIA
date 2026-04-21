#!/usr/bin/env python3
"""Sprint 5 Phase 5 hotfix #3 — renforcer QCM_OVERRIDE_v1 avec exemples L2.

Symptom : Teacher greeting drift FR->L2. Conv Nico 2026-04-20 : turn 1
reponse "Salut ! Je vais te poser quelques questions..." puis "Tell me
about yourself." -> greeting en FR au lieu de L2 comme demande par
QCM_OVERRIDE_v1 step 2 ("Saluer tres brievement dans la langue cible").
Maestro respecte la regle (greeting ES), Teacher drift FR.

Fix : inserer 2 few-shots L2-explicites AVANT le marker `=== FIN` dans
le block existant. Cible Teacher + Maestro, draft + published. Idempotent
via marker `L2_EXAMPLES_v1`.
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

EXISTING_MARKER = "=== QCM_OVERRIDE_v1 ==="
END_MARKER = "=== FIN QCM_OVERRIDE_v1 ==="
NEW_MARKER = "L2_EXAMPLES_v1"

EXAMPLES_BLOCK = """
L2_EXAMPLES_v1 (exemples concrets, adapte a la langue cible) :
- Teacher (anglais), profil A2, objectif voyage :
  "Hey! I'll ask you a few quick questions to calibrate your level. First question: tell me about a trip you really enjoyed."
- Maestro (espanol), profil B1, motivation authentic_content :
  "¡Hola! Voy a hacerte unas preguntas para calibrar tu nivel. Primera pregunta: háblame de una película o serie que te haya marcado."
Les 3 phrases (salut + annonce + question) DOIVENT etre dans la langue cible. JAMAIS en francais si la langue cible n'est pas le francais.

"""


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
            text = msg.get("text", "")
            if NEW_MARKER in text:
                return graph_str, False
            if EXISTING_MARKER not in text or END_MARKER not in text:
                print(f"  [WARN] QCM_OVERRIDE_v1 block introuvable, skip")
                return graph_str, False
            msg["text"] = text.replace(END_MARKER, EXAMPLES_BLOCK + END_MARKER)
            changed = True
        break
    return (json.dumps(graph, ensure_ascii=False), changed) if changed else (graph_str, False)


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
        print(f"  [PATCH] {version}  ({len(graph)} -> {len(new_graph)} chars)")
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
