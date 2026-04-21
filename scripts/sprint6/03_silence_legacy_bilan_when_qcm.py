#!/usr/bin/env python3
"""Sprint 6 (Session 36) — append NO_LEGACY_BILAN_v1 directive to llm_onboarding.

Bug : quand QCM est présent (learner_profile non vide), le prompt llm_onboarding
continue à produire un "bilan de niveau" textuel ("Niveau observé : A2 …") qui
entre en conflit avec notre mécanisme de consolidation Session 36 (mini-exam
structuré + modal bienveillant). Dissonance UX : bot dit "c'est bon" puis
modal pop.

Fix : directive appended à llm_onboarding pour interdire EXPLICITEMENT toute
production de bilan, synthèse de niveau, ou proposition de "voir ton bilan"
quand le bloc <learner_profile> est non vide. Le bot continue à observer et
émettre `observed_level` dans son JSON, mais n'annonce plus rien.

Idempotent via marker `NO_LEGACY_BILAN_v1`.
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

MARKER = "NO_LEGACY_BILAN_v1"

DIRECTIVE = """

=== NO_LEGACY_BILAN_v1 ===
CONTRAINTE ABSOLUE quand le bloc <learner_profile> est non vide (QCM déjà
complété par l'apprenant·e) :

1. Tu ne produis JAMAIS de "bilan de niveau" textuel, ni de synthèse du style
   "Niveau observé : X", "Tu as démontré...", "Tu es au niveau Y", etc.
2. Tu ne demandes JAMAIS à l'apprenant·e "ok pour voir ton bilan" ou de
   répondre "ok/oui" pour déclencher un résumé.
3. Tu ne produis JAMAIS de message "Merci pour tes réponses !" suivi d'une
   synthèse — c'était une étape de l'ancien onboarding conversationnel, elle
   est maintenant caduque.
4. Tu continues la conversation de manière naturelle, tour après tour, comme
   un·e prof attentif·ve : questions ouvertes, reformulation, petites tâches
   ciblées, feedback dosé selon la matrice de tolérance de ton niveau.
5. Le niveau CEFR de l'apprenant·e est déjà connu (via QCM + consolidation en
   arrière-plan). Tu n'as pas à le "déterminer" ou à le "confirmer" par une
   séquence de diagnostic formel. Le système de consolidation s'en charge
   via un mini-test structuré au moment opportun — tu n'as RIEN à annoncer
   à ce sujet.
6. Continue d'émettre "observed_level" dans ton JSON (champ discret, invisible
   à l'apprenant·e) — c'est ça qui alimente la consolidation.

Si <learner_profile> est vide, ignore cette section et suis le comportement
standard (FASE 1 recueil + diagnostic + éventuel bilan).
=== FIN NO_LEGACY_BILAN_v1 ===
"""

TARGET_NODE = "llm_onboarding"


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
        if n.get("id") != TARGET_NODE:
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
        print(f"  [PATCH] {version} ({n} update)")
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
