"""Sprint Maestro ES Tier 1 Phase 1.B v3 — apply v3 to Teacher EN (cross-langue).

Same 4 fixes as Maestro ES v3 (script 04) — FR phrasing, EN examples.

Strategy : restore from earliest backup (pre-v2 = original since EN had no v1)
+ apply v3 fresh.

Restore source : /tmp/dify_backups/20260501-143858_teacher_en_pre_lyster_v2.json
Backup : /tmp/dify_backups/<TS>_teacher_en_pre_lyster_v3.json

Usage :
  python3 scripts/sprint-maestro-es/05_dify_teacher_en_lyster_v3.py [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import subprocess
import sys

APP_ID = "39565197-c9d1-4d5b-b66f-18925de236d9"
NODE_ID = "llm_session"
RESTORE_BACKUP = pathlib.Path("/tmp/dify_backups/20260501-143858_teacher_en_pre_lyster_v2.json")

DB = ("docker", "exec", "-i", "postgres-academie",
      "psql", "-U", "sinse", "-d", "academie_db")
BACKUP_DIR = pathlib.Path("/tmp/dify_backups")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP_FILE = BACKUP_DIR / f"{TS}_teacher_en_pre_lyster_v3.json"

V3_MARKER = "REGLES LYSTER PAR NIVEAU CECRL (v3)"

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
                     ⚠️ A1-A2 : utiliser partial_recast (avec *forme* en asterisque) — implicit peut passer inaperçu (Lyster Ch 4 §3.1 salience)
  T3 penalized    → ELICITATION ↔ METALINGUISTIC (alterner — diversity rule appliquée par le système)
                     ⚠️ A1-A2 : JAMAIS metalinguistic → partial_recast ou elicitation naturelle
                     ⚠️ B1-B2 + tier T2 (communicatif) : JAMAIS metalinguistic/explicit_correction → recast préféré
  T4 regressive   → PROMPT + REMEDIATION + flag pour spaced retrieval
                     ⚠️ A1-A2 : JAMAIS explicit_correction (❌→✅) → prompt naturel + recast intégré
                     ⚠️ Tier T2 cross-niveau : JAMAIS prompt_plus_remediation (T2 = communicatif, T4 escalation interdite) → partial_recast préféré
Override gravité communicative ≥0.7 : T1 → recast (breakdown communicatif).
Override gravité sociale ≥0.6 : T2 → elicitation (irritation native).
Si dosage saturé, prio T4 > T3 > T2 (linguistic ≥0.5) > T1 silent.
=== FIN MAPPING ==="""

LYSTER_V3 = """=== REGLES LYSTER PAR NIVEAU CECRL (v3) ===
Le mapping ci-dessus a déjà les gates par niveau + tier. Cette section ajoute des EXEMPLES CONCRETS pour éviter (a) "Nice ! But..." en A1-A2 et (b) over-soften en B2-C1 où explicit est valide.

A1-A2 — recast SAILLANT préféré (Lyster Ch 4 §3.1) :

Élève A1 : "Yesterday I go to the cinema"
  ❌ "Nice ! But you should say 'I went' because it's past tense."  (explicit_correction INTERDIT)
  ❌ "Remember : past simple uses '-ed' or irregular forms."         (metalinguistic INTERDIT)
  ❌ "You went to the cinema."                                       (implicit peut passer inaperçu)
  ✅ "Cool ! You *went* to the cinema. What did you watch ?"         (partial_recast asterisque — saillant)

Élève A1 : "I am living in Paris since 5 years"
  ❌ "But you should use 'have been living' for actions continuing now."  (explicit INTERDIT)
  ✅ "Five years in Paris ! You *have been living* there a while. Do you like it ?"  (partial_recast saillant)

Élève A2 : "I have seen him yesterday"
  ❌ "Remember to use past simple with 'yesterday', not present perfect."  (metalinguistic INTERDIT)
  ✅ "Oh, you *saw* him yesterday ! Where did you meet ?"                  (partial_recast + extension)

B1 — recast/elicitation, évite explicit_correction en T2 :

Élève B1/T2 : "I am agree with you"  (calque FR)
  ❌ "Remember : agree is a verb, not adjective. Say 'I agree'."   (metalinguistic INTERDIT en T2)
  ✅ "Ah, you *agree* with me ! Why do you think so ?"             (partial_recast naturel)

B2-C1 — explicit_correction et metalinguistic ACCEPTABLES en T3+ (form-oriented) :

Élève B2/T3 : "If I would have time, I would travel"  (mixed conditional)
  ✅ "Watch out : the if-clause takes past simple, not 'would have'. 'If I had time, I would travel'." (explicit_correction OK B2/T3)
  ✅ "Almost : 'If I *had* time, I would travel'. Where would you go ?" (partial_recast alternative)

Élève C1/T3 : "It's important that he knows the truth"  (subjunctive vs indicative)
  ✅ "Subtle : after 'it's important that' some style guides prefer subjunctive : 'know'. Both are accepted in modern usage. What's your stance ?" (metalinguistic bref OK C1)

REGLE D'OR : niveau + tier > préférence personnelle. A1-A2 → recast saillant. B1/T2 → recast. B1/T3+ → elicit/metaling. B2/T3+ + C1-C2 → tous les moves disponibles.
=== FIN REGLES LYSTER PAR NIVEAU CECRL (v3) ==="""

LEAK_V3 = """=== ANTI-PRIORITY-LEAK ===
CE BLOC S'APPLIQUE SEULEMENT SI : `error_feedback` ci-dessus est VIDE ou ne contient pas d'items avec tier T2+.

SI il y a une erreur genuine (T2+) dans error_feedback : IGNORE ce bloc et suis MAPPING TIER → FEEDBACK TYPE.

SI il n'y a PAS d'erreur (error_feedback vide) :
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

INJECTED = "\n\n" + LYSTER_V3 + "\n\n" + LEAK_V3


def psql_tAc(sql: str) -> str:
    return subprocess.check_output([*DB, "-tAc", sql], text=True).rstrip("\n")


def psql_exec(sql: str) -> None:
    p = subprocess.run([*DB, "-v", "ON_ERROR_STOP=1"],
                       input=sql, text=True, capture_output=True)
    if p.returncode != 0:
        raise SystemExit(f"psql failed: {p.stderr}")


def patch_text(text: str) -> tuple[str, str]:
    if V3_MARKER in text:
        return text, "noop_v3_present"
    if OLD_MAPPING not in text:
        return text, "error_old_mapping_not_found_after_restore"
    text = text.replace(OLD_MAPPING, NEW_MAPPING, 1)
    text = text.replace("=== FIN MAPPING ===", "=== FIN MAPPING ===" + INJECTED, 1)
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

    if not RESTORE_BACKUP.exists():
        print(f"❌ Restore backup not found: {RESTORE_BACKUP}")
        return 1

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    wids = psql_tAc(f"SELECT id FROM workflows WHERE app_id = '{APP_ID}' ORDER BY created_at DESC;").splitlines()
    pre_v3 = {wid: json.loads(psql_tAc(f"SELECT graph FROM workflows WHERE id = '{wid}';")) for wid in wids}
    if not args.dry_run:
        BACKUP_FILE.write_text(json.dumps(pre_v3, ensure_ascii=False, indent=2))
        print(f"✅ Pre-v3 backup → {BACKUP_FILE}")

    with open(RESTORE_BACKUP) as f:
        original = json.load(f)

    # Only patch the latest workflow row (live one).
    latest_wid = wids[0]
    version = psql_tAc(f"SELECT version FROM workflows WHERE id = '{latest_wid}';")
    label = "draft" if "draft" in version else f"published({version[:10]})"
    if latest_wid not in original:
        print(f"  ⚠️ {latest_wid[:8]} not in restore backup")
        return 1
    graph = original[latest_wid]
    patched, status = patch_graph(graph)
    if status == "patched":
        new_graph_json = json.dumps(patched, ensure_ascii=False)
        print(f"  [{label} {latest_wid[:8]}] restored + v3 patched (size: {len(new_graph_json)} chars)")
        if not args.dry_run:
            psql_exec(f"UPDATE workflows SET graph = $${new_graph_json}$$ WHERE id = '{latest_wid}';")
    else:
        print(f"  [{label} {latest_wid[:8]}] {status}")
        if status.startswith("error_"):
            return 2

    if args.dry_run:
        print("\n[dry-run] No DB changes.")
    else:
        print(f"\n✅ Teacher EN v3 applied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
