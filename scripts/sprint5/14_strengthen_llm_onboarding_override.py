#!/usr/bin/env python3
"""Sprint 5 Phase 5 hotfix #2 — strengthen llm_onboarding QCM override.

Symptom : même avec `<learner_profile>` block au top et directive de skip
FASE 1, le LLM suit quand même les instructions détaillées FASE 1 (trois
questions FR ultra-spécifiques). Le block + directive brève sont "noyés"
par la richesse descriptive de FASE 1.

Fix : append un override FORT à la FIN du system prompt (dernière
instruction → priorité LLM). Liste explicite des steps à faire si le profil
est présent. Cumulable avec la directive du top (ceinture + bretelles).

Idempotent.
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

# End marker — idempotence check + insertion anchor.
MARKER = "=== QCM_OVERRIDE_v1 ==="

OVERRIDE_BLOCK_FR = """

=== QCM_OVERRIDE_v1 ===
Si le bloc <learner_profile> au DEBUT de ce prompt contient un resume non vide
(il commence par 'Profil apprenant'), tu DOIS :

1. IGNORER COMPLETEMENT toute la section "FASE 1 — ACOGIDA" ci-dessus (ne pose
   AUCUNE des 3 questions FR : prenom, niveau, interets).
2. Saluer tres brievement dans la langue cible (1 phrase max, amical, tutoyer).
3. Annoncer en 1 phrase dans la langue cible que tu vas poser quelques questions
   pour calibrer.
4. Poser IMMEDIATEMENT la PREMIERE question du diagnostic DANS LA LANGUE CIBLE,
   au palier CEFR extrait de 'niveau placement' dans le profil (A1/A2/B1/B2/C1).
5. Utiliser l'Objectif (champ "Objectif") et la Motivation (champ "Motivation
   dominante") du profil pour choisir un theme personnalise la premiere question
   (ex. motivation 'daily_communication' + objectif qui parle de voyage ->
   question sur un voyage recent).
6. Ne PAS repeter les infos du profil au user (il les connait, il vient de
   remplir le QCM). Sois naturel.

Si le bloc <learner_profile> est vide, suis la FASE 1 ci-dessus normalement.

Cette regle ecrase les instructions de FASE 1 ci-dessus en cas de profil present.
=== FIN QCM_OVERRIDE_v1 ===
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
            if MARKER in msg.get("text", ""):
                return graph_str, False
            msg["text"] = msg.get("text", "") + OVERRIDE_BLOCK_FR
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
        print(f"  [PATCH] {version}  ({len(graph)} → {len(new_graph)} chars)")
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
