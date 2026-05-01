"""Sprint Maestro ES Tier 1 G5.1 v2 — strengthened Lyster CEFR + anti-leak.

v1 (script 01) inserted abstract "PROHIBIDO metalingüístico" rule.
Smoke 3/6 — gpt-4o-mini bypassed the abstract rule, fell back to existing
Tier→Feedback mapping which is niveau-agnostic ("T3 → ELICITACIÓN ↔
METALINGÜÍSTICO"). 2 fails A1 explicit_correction + 1 A2 semantic.

v2 strategy :
  1. Inline caveat in MAPPING TIER → FEEDBACK (the place LLM actually reads
     for action) — adds A1-A2 niveau gate per Tier line.
  2. Replace abstract Lyster block with EXAMPLE-DRIVEN ❌/✅ block (concrete
     pattern matching "¡Bien! Pero..." → "¡Bien! [recast]").
  3. Keep ANTI-PRIORITY-LEAK block unchanged.

Idempotent : detects v2 marker `=== REGLAS LYSTER POR NIVEL CEFR (v2) ===`.
First restores from v1 patch by removing v1 markers, then applies v2.

Backup : /tmp/dify_backups/<TS>_maestro_es_pre_lyster_v2.json

Usage :
  python3 scripts/sprint-maestro-es/02_dify_maestro_es_lyster_cefr_v2.py [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import subprocess
import sys

APP_ID = "47b0529c-b3a3-4651-8717-759e666172c9"  # Maestro ES
NODE_ID = "llm_session"

DB = ("docker", "exec", "-i", "postgres-academie",
      "psql", "-U", "sinse", "-d", "academie_db")
BACKUP_DIR = pathlib.Path("/tmp/dify_backups")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP_FILE = BACKUP_DIR / f"{TS}_maestro_es_pre_lyster_v2.json"

V2_MARKER = "REGLAS LYSTER POR NIVEL CEFR (v2)"

# (1) Inline caveat — modify MAPPING TIER → FEEDBACK directly.
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

NEW_MAPPING = """=== MAPPING TIER → TIPO DE FEEDBACK ===
Para cada error (ver tier summary más arriba) :
  T1 ignorado      → SILENCIOSO (log only, no lo mencionas nunca)
  T2 notado        → RECAST IMPLÍCITO (reformulas inline, sin pausa)
  T3 penalizado    → ELICITACIÓN ↔ METALINGÜÍSTICO (alternar — diversity rule la aplica el sistema)
                     ⚠️ SI niveau A1 o A2 : NUNCA metalingüístico → usar partial_recast en su lugar
  T4 regresivo     → PROMPT + REMEDIACIÓN + flag para recuperación espaciada
                     ⚠️ SI niveau A1 o A2 : NUNCA explicit_correction (❌→✅) → prompt natural + recast embebido
Override gravedad comunicativa ≥0.7 : T1 → recast (ruptura comunicativa).
Override gravedad social ≥0.6 : T2 → elicitación (irritación nativa).
Si la dosificación está saturada, prioridad T4 > T3 > T2 (linguistic ≥0.5) > T1 silencioso.
=== FIN MAPPING ==="""

# (2) Concise example-driven Lyster block (replaces v1 abstract block).
LYSTER_V2 = """=== REGLAS LYSTER POR NIVEL CEFR (v2) ===
El mapping arriba ya tiene los gates A1-A2. Esta sección añade EJEMPLOS CONCRETOS para evitar el patrón "¡Bien! Pero deberías..." que es explicit_correction PROHIBIDO en A1-A2.

A1-A2 — EJEMPLOS (Lyster 2007 Ch 4 §3.1) :

Alumno A1 : "Mi casa es en Madrid"
  ❌ "¡Bien! Pero deberías usar 'está' porque hablas de la ubicación."  (explicit_correction PROHIBIDO)
  ❌ "Recuerda : con localización se usa 'estar', no 'ser'."             (metalingüístico PROHIBIDO)
  ✅ "¡Vale! Tu casa está en Madrid. ¿Cerca del centro?"                  (recast natural)

Alumno A1 : "En mi ciudad tener muchos parques"
  ❌ "Pero hay un pequeño error. Debes decir 'hay'."                       (explicit_correction PROHIBIDO)
  ✅ "¡Genial! Hay muchos parques. ¿Cuál te gusta más?"                    (recast)

Alumno A2 : "Hoy he visto Almudena"
  ❌ "Pero recuerda que debes decir 'veo a Almudena'."                     (explicit_correction PROHIBIDO)
  ✅ "¡Ah, viste a Almudena! ¿Dónde os encontrasteis?"                     (partial_recast + extension)

Patrón anti-A1-A2 : NUNCA empieces "¡Bien! Pero..." seguido de regla o forma. SIEMPRE incorpora la corrección DENTRO de tu propia frase natural.

B1 (transición) — recast (T2) y elicitación (T3) preferidos. Metalingüístico breve OK si recurrente.
B2 (form-oriented) — todos los moves Lyster aceptables, incluido explicit_correction T3+.
C1-C2 (form-focused) — explicit + metalingüístico preferidos (el alumno lo espera).
=== FIN REGLAS LYSTER POR NIVEL CEFR (v2) ==="""

# (3) Anti-priority-leak block (kept from v1).
LEAK_BLOCK = """=== ANTI-PRIORITY-LEAK ===
Si la producción del alumno NO contiene error (error_feedback vacío o sin items T2+) :
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

INJECTED_AFTER_MAPPING = "\n\n" + LYSTER_V2 + "\n\n" + LEAK_BLOCK


def psql_tAc(sql: str) -> str:
    return subprocess.check_output([*DB, "-tAc", sql], text=True).rstrip("\n")


def psql_exec(sql: str) -> None:
    p = subprocess.run([*DB, "-v", "ON_ERROR_STOP=1"],
                       input=sql, text=True, capture_output=True)
    if p.returncode != 0:
        raise SystemExit(f"psql failed: {p.stderr}")


def strip_v1(text: str) -> str:
    """Remove v1 inserted blocks (between '=== FIN MAPPING ===' and end of '=== FIN ANTI-PRIORITY-LEAK ===').

    v1 inserted: '\\n\\n' + LYSTER_BLOCK_ES + '\\n\\n' + LEAK_BLOCK_ES right after '=== FIN MAPPING ==='.
    """
    # Pattern matches v1 insertion (greedy from FIN MAPPING to FIN ANTI-PRIORITY-LEAK)
    # Only strips if v1 marker is present (no v2 marker).
    if V2_MARKER in text:
        return text  # already v2
    pattern = re.compile(
        r"(=== FIN MAPPING ===)\s*\n\n=== REGLAS LYSTER POR NIVEL CEFR ===.*?=== FIN ANTI-PRIORITY-LEAK ===",
        re.DOTALL,
    )
    return pattern.sub(r"\1", text)


def patch_text(text: str) -> tuple[str, str]:
    """Returns (new_text, status)."""
    if V2_MARKER in text:
        return text, "noop_v2_present"
    # 1. Strip v1 if present
    text = strip_v1(text)
    # 2. Replace mapping with caveat version
    if OLD_MAPPING in text:
        text = text.replace(OLD_MAPPING, NEW_MAPPING, 1)
    elif "=== MAPPING TIER → TIPO DE FEEDBACK ===" not in text:
        return text, "error_mapping_missing"
    else:
        # Mapping present but doesn't match exact OLD_MAPPING (variant) — abort
        return text, "error_mapping_variant"
    # 3. Insert v2 blocks after FIN MAPPING
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
        print(f"No Maestro ES workflows found")
        return 1

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backups = {}
    for wid in wids:
        backups[wid] = json.loads(psql_tAc(f"SELECT graph FROM workflows WHERE id = '{wid}';"))
    if not args.dry_run:
        BACKUP_FILE.write_text(json.dumps(backups, ensure_ascii=False, indent=2))
        print(f"✅ Backup → {BACKUP_FILE}")
    else:
        print(f"[dry-run] would backup → {BACKUP_FILE}")

    for wid in wids:
        version = psql_tAc(f"SELECT version FROM workflows WHERE id = '{wid}';")
        version_label = "draft" if "draft" in version else "published"
        graph = backups[wid]
        patched, status = patch_graph(graph)
        if status == "patched":
            new_graph_json = json.dumps(patched, ensure_ascii=False)
            print(f"  [{version_label} {wid[:8]}] patched (graph size: {len(new_graph_json)} chars)")
            if not args.dry_run:
                psql_exec(f"UPDATE workflows SET graph = $${new_graph_json}$$ WHERE id = '{wid}';")
        else:
            print(f"  [{version_label} {wid[:8]}] {status}")
            if status.startswith("error_"):
                return 2

    if args.dry_run:
        print("\n[dry-run] No DB changes.")
    else:
        print(f"\n✅ Maestro ES Lyster CEFR v2 (inline caveat + examples) injected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
