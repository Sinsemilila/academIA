#!/usr/bin/env python3
"""Sprint 5 Phase 3 — Transform Teacher chatflow into language-tutor unified shell.

In-place edit of the published Teacher workflow (app_id 39565197-...):
1. Add 4 Start node inputs: lang_target_name, lang_target_prof,
   concept_hints_json, cefr_diagnostics_block
2. Replace hardcoded `concept_hint_map = {...}` in code_turn_check JS with
   JSON.parse of the start input
3. Replace the 15 lines of EN example questions in llm_onboarding system prompt
   with the {{#start.cefr_diagnostics_block#}} placeholder
4. Replace "Teacher, prof d'anglais" in 4 LLM node persona lines with
   "Teacher, prof {{#start.lang_target_prof#}}"
5. Replace "Maintenant je vais evaluer ton niveau avec quelques echanges en
   anglais" → in {{#start.lang_target_name#}}

Updates both published + draft versions. Backup in dify_workflows_backup_sprint5.
Requires Dify service restart after run.

Idempotent: re-running after success is safe.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys

DB_CONTAINER = "postgres-academie"
DB_USER = "sinse"
DB_NAME = "academie_db"
APP_ID = "39565197-c9d1-4d5b-b66f-18925de236d9"


def psql_query(sql: str) -> str:
    cmd = ["docker", "exec", "-i", DB_CONTAINER, "psql",
           "-U", DB_USER, "-d", DB_NAME, "-t", "-A", "-c", sql]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.rstrip("\n")


def psql_exec_file(sql: str) -> None:
    """Execute a SQL block by piping it into psql via stdin (avoids shell-escape hell)."""
    cmd = ["docker", "exec", "-i", DB_CONTAINER, "psql",
           "-U", DB_USER, "-d", DB_NAME]
    subprocess.run(cmd, input=sql, text=True, check=True)


def patch_graph(graph_str: str) -> str:
    """Apply all Phase 3 transforms to a workflow graph JSON string."""
    graph = json.loads(graph_str)
    nodes = graph.get("nodes", [])

    # ── 1. Start node: add 4 new inputs ──
    new_vars = [
        {"variable": "lang_target_name", "type": "text-input", "required": False,
         "label": "Lang target display name", "max_length": 40, "options": [],
         "default_value": "Anglais", "hint": "e.g., Anglais, Espagnol"},
        {"variable": "lang_target_prof", "type": "text-input", "required": False,
         "label": "Lang target prof-label", "max_length": 40, "options": [],
         "default_value": "d'anglais", "hint": "e.g., d'anglais, d'espagnol"},
        {"variable": "concept_hints_json", "type": "paragraph", "required": False,
         "label": "Concept hints (JSON dict)", "max_length": 10000, "options": [],
         "default_value": "{}"},
        {"variable": "cefr_diagnostics_block", "type": "paragraph", "required": False,
         "label": "CEFR diagnostic examples block", "max_length": 5000, "options": [],
         "default_value": ""},
    ]
    for n in nodes:
        if n.get("data", {}).get("type") == "start":
            existing = {v.get("variable") for v in n["data"].get("variables", [])}
            for nv in new_vars:
                if nv["variable"] not in existing:
                    n["data"]["variables"].append(nv)
            break

    # ── 2. code_turn_check: inject JSON.parse for concept_hint_map ──
    #    Dify code nodes access start vars via the `variables` array (value_selector),
    #    NOT via {{#start.X#}} template syntax. We:
    #      - Add concept_hints_json to the variables array (mapped to start node)
    #      - Replace the hardcoded dict with JSON.parse of the injected variable
    for n in nodes:
        if n.get("id") == "code_turn_check":
            data = n["data"]
            # Register concept_hints_json as an input variable for this code node
            existing = {v.get("variable") for v in data.get("variables", [])}
            if "concept_hints_json" not in existing:
                data["variables"].append({
                    "variable": "concept_hints_json",
                    "value_selector": ["start", "concept_hints_json"],
                })
            code = data.get("code", "")
            new_block = (
                "let concept_hint_map = {};\n"
                "            try { concept_hint_map = JSON.parse(concept_hints_json || '{}'); }\n"
                "            catch(e) { concept_hint_map = {}; }"
            )
            pattern = re.compile(
                r"concept_hint_map\s*=\s*\{[^{}]{0,50}(?:[^{}]|\{[^{}]*\})*?\}",
                re.DOTALL,
            )
            # First check if already patched (JSON.parse present)
            if "JSON.parse(concept_hints_json" not in code:
                code, n_sub = pattern.subn(new_block.strip(), code, count=1)
                if n_sub:
                    data["code"] = code
            break

    # ── 3. llm_onboarding: swap EN example paliers for {{#start.cefr_diagnostics_block#}} ──
    # Find the "=== PHASE 2 — DIAGNOSTIC" section and replace the Palier reference table.
    for n in nodes:
        if n.get("id") == "llm_onboarding":
            pt = n["data"].get("prompt_template", [])
            for msg in pt:
                if msg.get("role") == "system":
                    txt = msg.get("text", "")
                    # Replace the full block from "Paliers de reference" to end of "C1-C2" entry.
                    patt = re.compile(
                        r"Paliers de reference.{10,100}:\s*\n(Palier.{5,200}\n){5,10}",
                        re.DOTALL,
                    )
                    txt = patt.sub(
                        "{{#start.cefr_diagnostics_block#}}\n\n",
                        txt, count=1,
                    )
                    # Also replace the "REGLE CRITIQUE : PALIER DE DEPART" first-question map
                    patt2 = re.compile(
                        r"La PREMIERE question.{10,100}:\s*\n(- Si.{5,200}\n){4,8}"
                        r"NE COMMENCE JAMAIS.{10,100}\.",
                        re.DOTALL,
                    )
                    txt = patt2.sub(
                        "La PREMIERE question en {{#start.lang_target_name#}} "
                        "DOIT correspondre au niveau choisi par l'eleve (voir "
                        "paliers_first_question dans cefr_diagnostics_block ci-dessus).",
                        txt, count=1,
                    )
                    # Param persona
                    txt = txt.replace(
                        "Tu es Teacher, prof d'anglais",
                        "Tu es Teacher, prof {{#start.lang_target_prof#}}",
                    )
                    # Param "en anglais" references
                    txt = txt.replace(
                        "tu passes a l'anglais",
                        "tu passes a {{#start.lang_target_name#}}",
                    )
                    txt = txt.replace(
                        "questions en anglais",
                        "questions en {{#start.lang_target_name#}}",
                    )
                    txt = txt.replace(
                        "question en anglais",
                        "question en {{#start.lang_target_name#}}",
                    )
                    txt = txt.replace(
                        "echanges en anglais",
                        "echanges en {{#start.lang_target_name#}}",
                    )
                    txt = txt.replace(
                        "en anglais DOIT correspondre",
                        "en {{#start.lang_target_name#}} DOIT correspondre",
                    )
                    txt = txt.replace(
                        "en anglais aujourd'hui",
                        "en {{#start.lang_target_name#}} aujourd'hui",
                    )
                    txt = txt.replace(
                        "l'anglais ? (travail",
                        "{{#start.lang_target_name#}} ? (travail",
                    )
                    # Phase 3 follow-up: remaining narrative references
                    txt = txt.replace(
                        "Tu passes a l'anglais",
                        "Tu passes a {{#start.lang_target_name#}}",
                    )
                    txt = txt.replace(
                        "tu evaluerais ton anglais",
                        "tu evaluerais ton {{#start.lang_target_name#}}",
                    )
                    txt = txt.replace(
                        "questions EN ANGLAIS",
                        "questions EN {{#start.lang_target_name#}}",
                    )
                    txt = txt.replace(
                        "premiere question EN ANGLAIS",
                        "premiere question EN {{#start.lang_target_name#}}",
                    )
                    txt = txt.replace(
                        "La question DOIT etre en anglais",
                        "La question DOIT etre en {{#start.lang_target_name#}}",
                    )
                    msg["text"] = txt
                    break
            break

    # ── 4. Other LLM nodes: param persona ──
    for n in nodes:
        if n.get("id") in ("llm_plan_choice", "llm_session", "llm_onboarding"):
            pt = n["data"].get("prompt_template", [])
            for msg in pt:
                if msg.get("role") == "system":
                    msg["text"] = msg["text"].replace(
                        "Tu es Teacher, prof d'anglais",
                        "Tu es Teacher, prof {{#start.lang_target_prof#}}",
                    )

    return json.dumps(graph, ensure_ascii=False)


def main() -> int:
    print(f"=== Sprint 5 Phase 3 — Dify Teacher → language-tutor unified ===")

    # Backup
    print("\n[1/3] Refreshing backup table...")
    psql_exec_file(f"""
        CREATE TABLE IF NOT EXISTS dify_workflows_backup_sprint5_phase3 AS
        SELECT id, version, graph, updated_at FROM workflows
        WHERE app_id = '{APP_ID}' LIMIT 0;
        INSERT INTO dify_workflows_backup_sprint5_phase3
            SELECT id, version, graph, updated_at FROM workflows
            WHERE app_id = '{APP_ID}'
              AND id NOT IN (SELECT id FROM dify_workflows_backup_sprint5_phase3);
    """)
    count = psql_query(f"SELECT COUNT(*) FROM dify_workflows_backup_sprint5_phase3")
    print(f"  Backup has {count} rows")

    # Fetch published + draft
    print("\n[2/3] Fetching versions...")
    rows = psql_query(
        f"SELECT id || '|' || version FROM workflows "
        f"WHERE app_id = '{APP_ID}' "
        f"AND (version = 'draft' OR version = '2026-04-05 14:28:19.306704')"
    )
    targets = [line.split("|", 1) for line in rows.splitlines() if line]
    print(f"  Targets: {len(targets)} versions")

    # Patch + write back
    print("\n[3/3] Patching graphs...")
    for wf_id, version in targets:
        graph = psql_query(
            f"SELECT graph FROM workflows WHERE id = '{wf_id}'"
        )
        new_graph = patch_graph(graph)
        if new_graph == graph:
            print(f"  [NOOP] {version}: already patched")
            continue
        escaped = new_graph.replace("'", "''")
        psql_exec_file(
            f"UPDATE workflows SET graph = '{escaped}', "
            f"updated_at = NOW() WHERE id = '{wf_id}';"
        )
        print(f"  [UPDATED] {version}: {len(graph)} → {len(new_graph)} chars")

    print("\nDone. Restart Dify services:")
    print("  docker restart dify-api dify-worker")
    return 0


if __name__ == "__main__":
    sys.exit(main())
