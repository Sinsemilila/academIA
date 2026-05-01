"""Sprint Maestro ES Tier 1 G5.2 — apply Lyster CEFR v2 to Teacher EN.

Cross-langue consistency : Maestro ES received the patch in G5.1 (script 02).
Apply identical structural change to Teacher EN to prevent EN regression
during ES iteration (Lyster taxonomy is cross-L2 per Lyster & Saito 2010).

Same blocks as Maestro ES v2 :
  1. Inline caveat in MAPPING TIER → FEEDBACK TYPE (FR phrasing).
  2. Lyster CEFR v2 block with ❌/✅ EN examples (past simple, present perfect, false friends).
  3. ANTI-PRIORITY-LEAK block.

Single workflow row for Teacher EN (no separate draft — published only).

Idempotent : detects v2 marker `=== REGLES LYSTER PAR NIVEAU CECRL (v2) ===`.

Backup : /tmp/dify_backups/<TS>_teacher_en_pre_lyster_v2.json

Usage :
  python3 scripts/sprint-maestro-es/03_dify_teacher_en_lyster_cefr_v2.py [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import subprocess
import sys

APP_ID = "39565197-c9d1-4d5b-b66f-18925de236d9"  # Teacher EN
NODE_ID = "llm_session"

DB = ("docker", "exec", "-i", "postgres-academie",
      "psql", "-U", "sinse", "-d", "academie_db")
BACKUP_DIR = pathlib.Path("/tmp/dify_backups")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP_FILE = BACKUP_DIR / f"{TS}_teacher_en_pre_lyster_v2.json"

V2_MARKER = "REGLES LYSTER PAR NIVEAU CECRL (v2)"

OLD_MAPPING = """=== MAPPING TIER → FEEDBACK TYPE ===
Pour chaque erreur (voir tier summary ci-dessus) :
  T1 ignored      → SILENT (log only, ne mentionne jamais)
  T2 noted        → IMPLICIT_RECAST (reformule inline, pas de pause)
  T3 penalized    → ELICITATION ↔ METALINGUISTIC (alterner — diversity rule appliquée par le système)
  T4 regressive   → PROMPT + REMEDIATION + flag pour spaced retrieval
Override gravité communicative ≥0.7 : T1 → recast (breakdown communicatif).
Override gravité sociale ≥0.6 : T2 → elicitation (irritation native).
Si dosage saturé, prio T4 > T3 > T2 (linguistic ≥0.5) > T1 silent.
=== FIN MAPPING ==="""

NEW_MAPPING = """=== MAPPING TIER → FEEDBACK TYPE ===
Pour chaque erreur (voir tier summary ci-dessus) :
  T1 ignored      → SILENT (log only, ne mentionne jamais)
  T2 noted        → IMPLICIT_RECAST (reformule inline, pas de pause)
  T3 penalized    → ELICITATION ↔ METALINGUISTIC (alterner — diversity rule appliquée par le système)
                     ⚠️ SI niveau A1 ou A2 : JAMAIS metalinguistic → utiliser partial_recast à la place
  T4 regressive   → PROMPT + REMEDIATION + flag pour spaced retrieval
                     ⚠️ SI niveau A1 ou A2 : JAMAIS explicit_correction (❌→✅) → prompt naturel + recast intégré
Override gravité communicative ≥0.7 : T1 → recast (breakdown communicatif).
Override gravité sociale ≥0.6 : T2 → elicitation (irritation native).
Si dosage saturé, prio T4 > T3 > T2 (linguistic ≥0.5) > T1 silent.
=== FIN MAPPING ==="""

LYSTER_V2 = """=== REGLES LYSTER PAR NIVEAU CECRL (v2) ===
Le mapping ci-dessus a déjà les gates A1-A2. Cette section ajoute des EXEMPLES CONCRETS pour éviter le pattern "Nice ! But you should..." qui est explicit_correction INTERDIT en A1-A2.

A1-A2 — EXEMPLES (Lyster 2007 Ch 4 §3.1) :

Élève A1 : "Yesterday I go to the cinema"
  ❌ "Nice ! But you should say 'I went' because it's past tense."  (explicit_correction INTERDIT)
  ❌ "Remember : past simple uses '-ed' or irregular forms."         (metalinguistic INTERDIT)
  ✅ "Cool ! You went to the cinema. What did you watch ?"           (recast naturel)

Élève A1 : "I am living in Paris since 5 years"
  ❌ "But you should use 'have been living' for actions continuing now."  (explicit INTERDIT)
  ✅ "Five years in Paris ! You've been living there a while. Do you like it ?"  (recast natural + extension)

Élève A2 : "I have seen him yesterday"
  ❌ "Remember to use past simple with 'yesterday', not present perfect."  (metalinguistic INTERDIT)
  ✅ "Oh, you saw him yesterday ! Where did you meet ?"                    (partial_recast + extension)

Pattern anti-A1-A2 : NE JAMAIS commencer "Nice ! But..." suivi d'une règle ou forme corrigée. TOUJOURS intégrer la correction DANS ta propre phrase naturelle.

B1 (transition) — recast (T2) et elicitation (T3) préférés. Metalinguistic bref OK si récurrent.
B2 (form-oriented) — tous les moves Lyster acceptables, incluant explicit_correction T3+.
C1-C2 (form-focused) — explicit + metalinguistic préférés (l'élève l'attend).
=== FIN REGLES LYSTER PAR NIVEAU CECRL (v2) ==="""

LEAK_BLOCK = """=== ANTI-PRIORITY-LEAK ===
Si la production de l'élève NE contient PAS d'erreur (error_feedback vide ou sans items T2+) :
  INTERDIT   reformuler (recast) une phrase correcte — over-correction détruit la confiance
  INTERDIT   mentionner le CONCEPT ACTIF verbalement ("On va travailler le past simple...")
  INTERDIT   injecter un hint correctif préventif ("Attention à present perfect vs past simple...")
  FAIRE      accuse naturel ("Nice !" / "OK.") + question ou extension qui CONTEXTUALISE
             le concept actif SANS le nommer (challenge implicite via contexte)

Le concept actif se travaille par SELECTION DE CONTEXTE, pas par annonce verbale.
Ex concept = "past simple vs present perfect" + élève produit une phrase correcte au présent :
  ❌ "Nice. Now let's practice the past simple. Tell me what you did yesterday."
  ✅ "OK. And yesterday ? Tell me something about your weekend." (contexte force past simple sans annonce)

Exception : tour 2 de session (annonce TTT du concept) — seul moment où mentionner le concept actif est OBLIGATOIRE. Ensuite : implicite toujours.
=== FIN ANTI-PRIORITY-LEAK ==="""

INJECTED_AFTER_MAPPING = "\n\n" + LYSTER_V2 + "\n\n" + LEAK_BLOCK


def psql_tAc(sql: str) -> str:
    return subprocess.check_output([*DB, "-tAc", sql], text=True).rstrip("\n")


def psql_exec(sql: str) -> None:
    p = subprocess.run([*DB, "-v", "ON_ERROR_STOP=1"],
                       input=sql, text=True, capture_output=True)
    if p.returncode != 0:
        raise SystemExit(f"psql failed: {p.stderr}")


def patch_text(text: str) -> tuple[str, str]:
    if V2_MARKER in text:
        return text, "noop_v2_present"
    if OLD_MAPPING in text:
        text = text.replace(OLD_MAPPING, NEW_MAPPING, 1)
    elif "=== MAPPING TIER → FEEDBACK TYPE ===" not in text:
        return text, "error_mapping_missing"
    else:
        return text, "error_mapping_variant"
    if "=== FIN MAPPING ===" not in text:
        return text, "error_fin_mapping_missing"
    text = text.replace(
        "=== FIN MAPPING ===",
        "=== FIN MAPPING ===" + INJECTED_AFTER_MAPPING,
        1,
    )
    return text, "patched"


def patch_graph(graph: dict) -> tuple[dict, str]:
    for node in graph.get("nodes", []):
        if node.get("id") != NODE_ID:
            continue
        d = node.get("data", {})
        for tpl in d.get("prompt_template", []):
            if tpl.get("role") != "system":
                continue
            new_text, status = patch_text(tpl.get("text", ""))
            if status == "patched":
                tpl["text"] = new_text
            return graph, status
    return graph, "error_node_not_found"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    wids = psql_tAc(
        f"SELECT id FROM workflows WHERE app_id = '{APP_ID}' "
        f"ORDER BY created_at DESC;"
    ).splitlines()
    if not wids:
        print(f"No Teacher EN workflows found")
        return 1

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backups = {}
    for wid in wids:
        backups[wid] = json.loads(psql_tAc(f"SELECT graph FROM workflows WHERE id = '{wid}';"))
    if not args.dry_run:
        BACKUP_FILE.write_text(json.dumps(backups, ensure_ascii=False, indent=2))
        print(f"✅ Backup → {BACKUP_FILE}")

    # Only patch the latest (most recent) workflow row — Teacher EN has 5 historical
    # versions but Dify reads the most recent published as live.
    latest_wid = wids[0]
    version = psql_tAc(f"SELECT version FROM workflows WHERE id = '{latest_wid}';")
    label = "draft" if "draft" in version else f"published({version[:10]})"
    graph = backups[latest_wid]
    patched, status = patch_graph(graph)
    if status == "patched":
        new_graph_json = json.dumps(patched, ensure_ascii=False)
        print(f"  [{label} {latest_wid[:8]}] patched (graph size: {len(new_graph_json)} chars)")
        if not args.dry_run:
            psql_exec(f"UPDATE workflows SET graph = $${new_graph_json}$$ WHERE id = '{latest_wid}';")
    else:
        print(f"  [{label} {latest_wid[:8]}] {status}")
        if status.startswith("error_"):
            return 2

    if args.dry_run:
        print("\n[dry-run] No DB changes.")
    else:
        print(f"\n✅ Teacher EN Lyster CEFR v2 (inline caveat + examples) injected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
