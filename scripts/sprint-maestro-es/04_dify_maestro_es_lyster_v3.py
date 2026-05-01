"""Sprint Maestro ES Tier 1 Phase 1.B v3 — refined Lyster CEFR + smarter anti-leak.

v2 (script 02) shipped with smoke 6/6 ✅ but full battery 16/24 ❌ vs baseline 19/24.
Postmortem `2026-05-01-maestro-es-tier1-battery-postmortem.md` identified 4 patterns.

v3 fixes :
  Pattern 1 : A1 prefer partial_recast over implicit_recast (Lyster Ch 4 §3.1
              salience nuance — implicit may go unnoticed at A1).
  Pattern 2 : ANTI-PRIORITY-LEAK conditional on `error_feedback` empty —
              don't silent when error genuine.
  Pattern 3 : Extend caveat to T2 cross-niveau ban explicit_correction +
              T2 ban prompt_plus_remediation (T4 escalation not for
              communicative tier).
  Pattern 4 : Add 2 B2/C1 ✅ examples (explicit_correction acceptable at
              advanced) to balance A1-A2 over-soften priming.

Strategy : restore from earliest backup (pre-v1) for clean state, apply v3
fresh. Avoids strip-v2 complexity.

Idempotent : detects v3 marker `=== REGLAS LYSTER POR NIVEL CEFR (v3) ===`.

Backup : /tmp/dify_backups/<TS>_maestro_es_pre_lyster_v3.json
Restore source : /tmp/dify_backups/20260501-142725_maestro_es_pre_lyster_cefr.json (pre-v1 = truly original)

Usage :
  python3 scripts/sprint-maestro-es/04_dify_maestro_es_lyster_v3.py [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import subprocess
import sys

APP_ID = "47b0529c-b3a3-4651-8717-759e666172c9"
NODE_ID = "llm_session"
RESTORE_BACKUP = pathlib.Path("/tmp/dify_backups/20260501-142725_maestro_es_pre_lyster_cefr.json")

DB = ("docker", "exec", "-i", "postgres-academie",
      "psql", "-U", "sinse", "-d", "academie_db")
BACKUP_DIR = pathlib.Path("/tmp/dify_backups")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP_FILE = BACKUP_DIR / f"{TS}_maestro_es_pre_lyster_v3.json"

V3_MARKER = "REGLAS LYSTER POR NIVEL CEFR (v3)"

OLD_MAPPING = """=== MAPPING TIER → TIPO DE FEEDBACK ===
Para cada error (ver tier summary más arriba) :
  T1 ignorado      → SILENCIOSO (log only, no lo mencionas nunca)
  T2 notado        → RECAST IMPLÍCITO (reformulas inline, sin pausa)
  T3 penalizado    → ELICITACIÓN ↔ METALINGÜÍSTICO (alternar — diversity rule la aplica el sistema)
  T4 regresivo     → PROMPT + REMEDIACIÓN + flag para recuperación espaciada
Override gravedad comunicativa ≥0.7 : T1 → recast (ruptura comunicativa).
Override gravedad social ≥0.6 : T2 → elicitación (irritación nativa).
Si la dosificación está saturada, prioridad T4 > T3 > T2 (linguistic ≥0.5) > T1 silencioso.
=== FIN MAPPING ==="""

# v3 mapping with refined caveats per Pattern 1 + 3.
NEW_MAPPING = """=== MAPPING TIER → TIPO DE FEEDBACK ===
Para cada error (ver tier summary más arriba) :
  T1 ignorado      → SILENCIOSO (log only, no lo mencionas nunca)
  T2 notado        → RECAST IMPLÍCITO (reformulas inline, sin pausa)
                     ⚠️ A1-A2 : usa partial_recast (con asterisco *forma*) — implicit puede pasar inadvertido (Lyster Ch 4 §3.1 salience)
  T3 penalizado    → ELICITACIÓN ↔ METALINGÜÍSTICO (alternar — diversity rule la aplica el sistema)
                     ⚠️ A1-A2 : NUNCA metalingüístico → partial_recast o elicitación natural
                     ⚠️ B1-B2 + tier T2 (comunicativo) : NUNCA metalingüístico/explicit_correction → recast preferido
  T4 regresivo     → PROMPT + REMEDIACIÓN + flag para recuperación espaciada
                     ⚠️ A1-A2 : NUNCA explicit_correction (❌→✅) → prompt natural + recast embebido
                     ⚠️ Tier T2 cross-niveau : NUNCA prompt_plus_remediation (T2 = comunicativo, T4 escalation prohibida) → partial_recast preferido
Override gravedad comunicativa ≥0.7 : T1 → recast (ruptura comunicativa).
Override gravedad social ≥0.6 : T2 → elicitación (irritación nativa).
Si la dosificación está saturada, prioridad T4 > T3 > T2 (linguistic ≥0.5) > T1 silencioso.
=== FIN MAPPING ==="""

# v3 Lyster block — adds Pattern 4 (B2/C1 examples for register balance).
LYSTER_V3 = """=== REGLAS LYSTER POR NIVEL CEFR (v3) ===
El mapping arriba ya tiene los gates por nivel + tier. Esta sección añade EJEMPLOS CONCRETOS para evitar (a) "¡Bien! Pero deberías..." en A1-A2 y (b) over-soften en B2-C1 donde explicit es válido.

A1-A2 — recast SALIENTE preferido (Lyster Ch 4 §3.1) :

Alumno A1 : "Mi casa es en Madrid"
  ❌ "¡Bien! Pero deberías usar 'está' porque hablas de la ubicación."  (explicit_correction PROHIBIDO)
  ❌ "Recuerda : con localización se usa 'estar', no 'ser'."             (metalingüístico PROHIBIDO)
  ❌ "Tu casa está en Madrid."                                            (implicit puede pasar inadvertido)
  ✅ "¡Vale! Tu casa *está* en Madrid. ¿Cerca del centro?"                (partial_recast con asterisco — saliente)

Alumno A1 : "En mi ciudad tener muchos parques"
  ❌ "Pero hay un pequeño error. Debes decir 'hay'."                       (explicit_correction PROHIBIDO)
  ✅ "¡Genial! En tu ciudad *hay* muchos parques. ¿Cuál te gusta más?"    (partial_recast saliente)

Alumno A2 : "Hoy he visto Almudena"
  ❌ "Pero recuerda que debes decir 'veo a Almudena'."                     (explicit_correction PROHIBIDO)
  ✅ "¡Ah, viste *a* Almudena! ¿Dónde os encontrasteis?"                   (partial_recast + extension)

B1 — recast/elicitación, evita explicit_correction en T2 :

Alumno B1/T2 : "Yo gusto la música clásica"  (calque FR)
  ❌ "Recuerda : 'gustar' funciona al revés. La música ME GUSTA."         (metalingüístico PROHIBIDO en T2)
  ✅ "Ah, ¿*te gusta* la música clásica? ¿Qué compositor prefieres?"      (partial_recast natural)

B2-C1 — explicit_correction y metalingüístico ACEPTABLES en T3+ (form-oriented) :

Alumno B2/T3 : "Si tendría más tiempo, viajaría más"  (condicional doble)
  ✅ "Cuidado : el si-clause toma subjuntivo imperfecto, no condicional. 'Si tuviera más tiempo, viajaría'." (explicit_correction acceptable C-T3)
  ✅ "Casi : 'Si tuviera más tiempo, viajaría más'. ¿A dónde te gustaría ir?" (alternativa partial_recast)

Alumno C1/T3 : "Es importante que sabe la verdad"  (subjuntivo presente)
  ✅ "Buen intento. Después de 'es importante que' usamos subjuntivo : 'sepa'. ¿Por qué crees que es importante?" (metalingüístico breve OK C1)

REGLA DE ORO : nivel + tier > preferencia personal. A1-A2 → recast saliente. B1/T2 → recast. B1/T3+ → elicit/metaling. B2/T3+ + C1-C2 → todos los moves disponibles.
=== FIN REGLAS LYSTER POR NIVEL CEFR (v3) ==="""

# v3 ANTI-PRIORITY-LEAK — Pattern 2 fix : conditional on error_feedback.
LEAK_V3 = """=== ANTI-PRIORITY-LEAK ===
ESTE BLOQUE SE APLICA SOLO SI : `error_feedback` arriba está VACÍO o no contiene items con tier T2+.

SI hay error genuino (T2+) en error_feedback : IGNORA este bloque y sigue MAPPING TIER → TIPO DE FEEDBACK.

SI no hay error (error_feedback vacío) :
  PROHIBIDO  reformular (recast) una frase correcta — over-correction destruye confianza
  PROHIBIDO  mencionar el CONCEPTO ACTIVO verbalmente ("Vamos a trabajar el subjuntivo...")
  PROHIBIDO  inyectar pista correctiva preventiva ("Cuidado con ser/estar...")
  HACER      acuse natural ("¡Bien!" / "Vale.") + pregunta o extensión que CONTEXTUALICE
             el concepto activo SIN nombrarlo (challenge implícito vía contexto)

El concepto activo se trabaja por SELECCIÓN DE CONTEXTO, no por anuncio verbal.
Ej concepto = "preterite vs imperfect" + alumno produce frase correcta presente :
  ❌ "Bien. Ahora vamos a practicar el pretérito. Cuéntame qué hiciste ayer."
  ✅ "Vale. ¿Y ayer ? Cuéntame algo de tu fin de semana." (contexto fuerza pretérito sin anuncio)

Excepción : turno 2 de sesión (anuncio TTT del concepto) — único momento donde mencionar el concepto activo es OBLIGATORIO. Después : implícito siempre.
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

    # Backup current state before restore + patch
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    wids = psql_tAc(f"SELECT id FROM workflows WHERE app_id = '{APP_ID}' ORDER BY created_at DESC;").splitlines()
    pre_v3_state = {wid: json.loads(psql_tAc(f"SELECT graph FROM workflows WHERE id = '{wid}';")) for wid in wids}
    if not args.dry_run:
        BACKUP_FILE.write_text(json.dumps(pre_v3_state, ensure_ascii=False, indent=2))
        print(f"✅ Pre-v3 backup → {BACKUP_FILE}")

    # Load original (pre-v1) state for restore
    with open(RESTORE_BACKUP) as f:
        original = json.load(f)

    for wid in wids:
        version = psql_tAc(f"SELECT version FROM workflows WHERE id = '{wid}';")
        version_label = "draft" if "draft" in version else f"published({version[:10]})"
        if wid not in original:
            print(f"  [{version_label} {wid[:8]}] ⚠️ not in restore backup, skip")
            continue
        graph = original[wid]
        patched, status = patch_graph(graph)
        if status == "patched":
            new_graph_json = json.dumps(patched, ensure_ascii=False)
            print(f"  [{version_label} {wid[:8]}] restored + v3 patched (size: {len(new_graph_json)} chars)")
            if not args.dry_run:
                psql_exec(f"UPDATE workflows SET graph = $${new_graph_json}$$ WHERE id = '{wid}';")
        else:
            print(f"  [{version_label} {wid[:8]}] {status}")
            if status.startswith("error_"):
                return 2

    if args.dry_run:
        print("\n[dry-run] No DB changes.")
    else:
        print(f"\n✅ Maestro ES v3 (refined caveats + B2/C1 examples + conditional anti-leak) applied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
