"""Sprint Maestro ES Tier 1 G5.1 — inject Lyster CEFR + anti-priority-leak blocks.

Cause root : Maestro ES (and Teacher EN) `llm_session` system prompt has a
niveau-agnostic Tier→Feedback mapping. No Lyster CEFR ban for A1-A2
(metalinguistic + explicit_correction prohibited per Lyster 2007 Ch 4 §3.1
+ Ellis & Sheen 2006). 5 baseline fails of S55 19/24 are all
explicit_correction A1-A2 — direct symptom of this missing constraint.

Fix : insert two new STATIC blocks in the cacheable prefix of the system
prompt, after `=== FIN MAPPING ===` and before `CONCEPTOS DE SESIÓN` :
  1. `=== REGLAS LYSTER POR NIVEL CEFR ===` — CEFR-aware override of base
     Tier→Feedback mapping.
  2. `=== ANTI-PRIORITY-LEAK ===` — prohibition on recasting correct
     production / verbalizing the active concept (cible scenario
     `risk_priority_leak_b1_es_001`).

Scope : Maestro ES app `47b0529c-b3a3-4651-8717-759e666172c9` ONLY.
Teacher EN equivalent patch = G5.2, separate script.

Dual-patch : draft `69fc4cf7` + published `d3df0ef0` (both rows updated
since Dify draft and published are independent rows in `workflows`).

Idempotent : detects existing block via marker `=== REGLAS LYSTER POR NIVEL CEFR ===`
and skips if present.

Backup : pre-patch graphs dumped to /tmp/dify_backups/<TS>_maestro_es_pre_lyster_cefr.json.

Smoke target : maestro_es 6/6 ≥ 5/6 + 0 explicit_correction A1-A2 detected.

Usage :
  python3 scripts/sprint-maestro-es/01_dify_maestro_es_lyster_cefr_block.py [--dry-run]

Rollback :
  Restore graphs from /tmp/dify_backups/...json via :
  UPDATE workflows SET graph = '<json>' WHERE id = '<wid>';
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import subprocess
import sys

APP_ID = "47b0529c-b3a3-4651-8717-759e666172c9"  # Maestro ES
NODE_ID = "llm_session"
INSERT_AFTER = "=== FIN MAPPING ==="
MARKER_LYSTER = "=== REGLAS LYSTER POR NIVEL CEFR ==="
MARKER_LEAK = "=== ANTI-PRIORITY-LEAK ==="

DB = ("docker", "exec", "-i", "postgres-academie",
      "psql", "-U", "sinse", "-d", "academie_db")

BACKUP_DIR = pathlib.Path("/tmp/dify_backups")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP_FILE = BACKUP_DIR / f"{TS}_maestro_es_pre_lyster_cefr.json"

LYSTER_BLOCK_ES = """=== REGLAS LYSTER POR NIVEL CEFR ===
El MAPPING TIER → FEEDBACK arriba indica el TIPO base. Estas reglas lo MODULAN según el nivel del alumno (campo niveau del perfil) — Lyster 2007 Ch 4 §3.1 + Ellis & Sheen 2006.

A1-A2 (carga cognitiva alta, foco en significado) :
  PROHIBIDO  metalingüístico (regla explícita) → siempre recast/elicitación
  PROHIBIDO  explicit_correction (❌→✅ sin contexto) → demasiado abrupto, bloquea producción
  PREFERIDO  implicit_recast (T1-T2) y partial_recast (T3)
  Si T4 obliga prompt → prompt_plus_remediation natural, sin tablas de reglas
  Excepción : ruptura comunicativa gravedad ≥0.7 → recast explícito 1 línea

B1 (transición form-meaning) :
  PREFERIDO  recast (T2) y elicitación (T3) — el alumno empieza a "notice"
  ACEPTABLE  metalingüístico breve (1 línea) si error recurrente B1+
  EVITAR    explicit_correction salvo error fundamental + alumno ya notó

B2 (form-oriented, noticing-ready) :
  ACEPTABLE  todos los moves Lyster, incluido metalingüístico + explicit_correction (T3+)
  PREFERIDO  prompt + remediación o explicit_correction cuando forma desvía + significado preserved
  Ej : pretérito↔imperfecto, condicional, subjuntivo imperfecto

C1-C2 (form-focused, accuracy-driven) :
  PREFERIDO  explicit_correction + metalingüístico — el alumno espera precisión y justificación
  ACEPTABLE  todos los moves ; recasts implicit pueden pasar desapercibidos
  Discusión metalingüística profunda OK (registro, matiz, colocación)

REGLA DE ORO : nivel del alumno > preferencia personal > tipo de error.
Si dudas en A1-A2 → recast. Si dudas en C1-C2 → explicit + metalingüístico.
=== FIN REGLAS LYSTER POR NIVEL CEFR ==="""

LEAK_BLOCK_ES = """=== ANTI-PRIORITY-LEAK ===
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

INJECTED_TEXT = "\n\n" + LYSTER_BLOCK_ES + "\n\n" + LEAK_BLOCK_ES


def psql_tAc(sql: str) -> str:
    return subprocess.check_output([*DB, "-tAc", sql], text=True).rstrip("\n")


def psql_exec(sql: str) -> None:
    p = subprocess.run([*DB, "-v", "ON_ERROR_STOP=1"],
                       input=sql, text=True, capture_output=True)
    if p.returncode != 0:
        raise SystemExit(f"psql failed: {p.stderr}")


def patch_graph(graph: dict) -> tuple[dict, str]:
    """Returns (patched_graph, status). Status in {'patched', 'noop_already_present', 'error_marker_missing'}."""
    for node in graph.get("nodes", []):
        if node.get("id") != NODE_ID:
            continue
        d = node.get("data", {})
        for tpl in d.get("prompt_template", []):
            if tpl.get("role") != "system":
                continue
            text = tpl.get("text", "")
            if MARKER_LYSTER in text:
                return graph, "noop_already_present"
            if INSERT_AFTER not in text:
                return graph, "error_marker_missing"
            new_text = text.replace(
                INSERT_AFTER,
                INSERT_AFTER + INJECTED_TEXT,
                1,
            )
            tpl["text"] = new_text
            return graph, "patched"
    return graph, "error_marker_missing"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    wids = psql_tAc(
        f"SELECT id FROM workflows WHERE app_id = '{APP_ID}' "
        f"ORDER BY created_at DESC;"
    ).splitlines()
    if not wids:
        print(f"No Maestro ES workflows found for app_id {APP_ID}")
        return 1

    # Pre-patch backup
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backups = {}
    for wid in wids:
        graph_str = psql_tAc(
            f"SELECT graph FROM workflows WHERE id = '{wid}';"
        )
        backups[wid] = json.loads(graph_str)
    if not args.dry_run:
        BACKUP_FILE.write_text(json.dumps(backups, ensure_ascii=False, indent=2))
        print(f"✅ Backup → {BACKUP_FILE}")
    else:
        print(f"[dry-run] would backup → {BACKUP_FILE}")

    # Patch each workflow
    for wid in wids:
        graph = backups[wid]
        patched, status = patch_graph(graph)
        version_label = "draft" if "draft" in str(
            psql_tAc(f"SELECT version FROM workflows WHERE id = '{wid}';")
        ) else "published"
        if status == "noop_already_present":
            print(f"  [{version_label} {wid[:8]}] noop — Lyster block already present")
            continue
        if status == "error_marker_missing":
            print(f"  [{version_label} {wid[:8]}] ❌ ERROR — '{INSERT_AFTER}' not found in llm_session prompt")
            return 2
        # Status == "patched"
        new_graph_json = json.dumps(patched, ensure_ascii=False)
        size = len(new_graph_json)
        print(f"  [{version_label} {wid[:8]}] patched (graph size: {size} chars)")
        if args.dry_run:
            continue
        # Use STDIN to avoid shell-quoting hell with the JSON
        sql = f"UPDATE workflows SET graph = $${new_graph_json}$$ WHERE id = '{wid}';"
        psql_exec(sql)

    if args.dry_run:
        print("\n[dry-run] No DB changes. Re-run without --dry-run to apply.")
    else:
        print(f"\n✅ Maestro ES Lyster CEFR + anti-priority-leak blocks injected.")
        print(f"   Backup: {BACKUP_FILE}")
        print(f"   Next: smoke test maestro_es 6/6 ≥ 5/6 + 0 explicit_correction A1-A2.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
