#!/usr/bin/env python3
"""Sprint 6 (Session 37) — replace OBSERVED_LEVEL_v1 directive with v2.

Session 37 finding: 0/10 organic messages emit a concrete CEFR in
`observed_level` field — all come back as "". Root cause: v1 directive told
the LLM "laisse vide si pas assez de signal", which the model picked as the
safe default every turn.

v2 fixes this by:
  - Removing the empty-string easy-out ("" only authorised for turns 1-2
    with zero production).
  - Making emission MANDATORY from turn 3.
  - Adding 5 concrete learner→level few-shots spanning A1 to C1.
  - Reinforcing that the field is pure telemetry (don't discuss in feedback).

Idempotent via marker `OBSERVED_LEVEL_v2`. Detects and REPLACES v1 block
in-place if present; else appends v2.
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

MARKER_V1 = "OBSERVED_LEVEL_v1"
MARKER_V2 = "OBSERVED_LEVEL_v2"

DIRECTIVE_V2 = """

=== OBSERVED_LEVEL_v2 ===
À CHAQUE turn, émets ton estimation CEFR du niveau APPARENT de l'apprenant·e
sur la base de ses productions cumulées. Renseigne le champ `observed_level`
avec une des valeurs : "A1", "A2", "B1", "B2", "C1", "C2".

RÈGLES STRICTES :
1. OBLIGATOIRE à partir du turn 3. Jamais "" passé ce seuil.
2. Si la production du turn est courte, appuie-toi sur l'ensemble des turns
   précédents pour déduire le niveau. Émets ton meilleur pari, pas "".
3. Ne discute JAMAIS ce niveau dans `feedback` — télémétrie interne pure,
   l'apprenant·e ne le voit pas et ne doit pas le savoir.
4. Seul cas autorisé pour "" : turns 1-2 avec zéro production (ex: "ok",
   "yo", "salut") — après turn 2 c'est une valeur concrète obligatoirement.

EXEMPLES (learner production → observed_level) :
• "yo / je débute / je connais pas trop" → "A1"
• "Me llamo Juan, soy francés y tengo treinta años. Vivo en París."
  (présent simple, ser/vivir, zéro subjonctif ni passé) → "A1"
• "Ayer fui al cine y vi una película muy buena. Me gustó mucho la historia."
  (passé simple correct, coordination, vocabulaire courant) → "A2"
• "Creo que el teletrabajo es útil, aunque es importante que las empresas
  organicen encuentros presenciales." (opinion + subjonctif + concessif) → "B1"
• "Si tuviera más tiempo libre, estudiaría más idiomas, pero el trabajo me
  absorbe todo el día." (subj imparfait + condicional) → "B2"
• "A pesar de que las empresas abogan por la flexibilidad, muchas siguen
  exigiendo presencia física, lo cual genera tensiones." (concessif
  complexe + relative + lexique abstrait) → "C1"
=== FIN OBSERVED_LEVEL_v2 ===
"""

TARGET_NODES = {"llm_session", "llm_onboarding", "llm_plan_choice"}

# Regex to match the v1 block (between === markers, inclusive)
V1_BLOCK_RE = re.compile(
    r"\n*=== OBSERVED_LEVEL_v1 ===.*?=== FIN OBSERVED_LEVEL_v1 ===\s*",
    re.DOTALL,
)


def psql_q(sql: str) -> str:
    return subprocess.run(
        ["docker", "exec", "-i", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME,
         "-t", "-A", "-c", sql],
        capture_output=True, text=True, check=True,
    ).stdout.rstrip("\n")


def psql_exec(sql: str) -> None:
    subprocess.run(
        ["docker", "exec", "-i", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME,
         "-v", "ON_ERROR_STOP=1"],
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
            if MARKER_V2 in text:
                # Already v2 — noop
                break
            if MARKER_V1 in text:
                # Strip v1, then append v2
                text = V1_BLOCK_RE.sub("\n", text).rstrip() + DIRECTIVE_V2
            else:
                # No v1 either (edge case: fresh app) — just append v2
                text = text + DIRECTIVE_V2
            msg["text"] = text
            patched += 1
            break
    if not patched:
        return graph_str, 0
    return json.dumps(graph, ensure_ascii=False), patched


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
            print(f"  [NOOP] {version}  — already v2 or no target nodes")
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
