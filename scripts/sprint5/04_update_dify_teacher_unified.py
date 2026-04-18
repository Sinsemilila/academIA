#!/usr/bin/env python3
"""Sprint 5 Phase 3 — Transform Teacher chatflow into language-tutor unified shell.

In-place edit of the published Teacher workflow (app_id 39565197-...):
1. Add 4 Start node inputs: lang_target_name, lang_target_prof,
   concept_hints_json, cefr_diagnostics_block
2. Replace hardcoded `concept_hint_map = {...}` in code_turn_check JS with
   JSON.parse of the start input
3. Replace the 15 lines of EN example questions in llm_onboarding system prompt
   with the {{#code_turn_check.cefr_diagnostics_block#}} placeholder
4. Replace "Teacher, prof d'anglais" in 4 LLM node persona lines with
   "Teacher, prof {{#code_turn_check.lang_target_prof#}}"
5. Replace "Maintenant je vais evaluer ton niveau avec quelques echanges en
   anglais" → in {{#code_turn_check.lang_target_name#}}

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
    # Format MUST match existing Dify Start variables: use `default` (not `default_value`),
    # keep `label` to the variable name, skip optional keys like `options`/`hint`.
    new_vars = [
        {"type": "text-input", "variable": "lang_target_name",
         "label": "lang_target_name", "required": False, "max_length": 40,
         "default": "Anglais"},
        {"type": "text-input", "variable": "lang_target_prof",
         "label": "lang_target_prof", "required": False, "max_length": 40,
         "default": "d'anglais"},
        {"type": "paragraph", "variable": "concept_hints_json",
         "label": "concept_hints_json", "required": False, "max_length": 10000,
         "default": "{}"},
        {"type": "paragraph", "variable": "cefr_diagnostics_block",
         "label": "cefr_diagnostics_block", "required": False, "max_length": 5000,
         "default": ""},
    ]
    for n in nodes:
        if n.get("data", {}).get("type") == "start":
            existing = {v.get("variable") for v in n["data"].get("variables", [])}
            for nv in new_vars:
                if nv["variable"] not in existing:
                    n["data"]["variables"].append(nv)
            break

    # ── 2. code_turn_check: wire 4 new inputs through the node ──
    #    Dify LLM prompts can ONLY reference `{{#<node_id>.<var>#}}` — start vars
    #    are NOT directly accessible via {{#start.X#}}. Pattern used by existing
    #    wiring (rubric_for_level, fewshots_block, etc.):
    #      (1) Declare var in code_turn_check.variables[] mapped to start
    #      (2) Add param to main() signature
    #      (3) Return value in the main() return dict
    #      (4) Declare in node.outputs array
    #    Then LLM prompts can use {{#code_turn_check.<var>#}}.

    NEW_VARS_TO_WIRE = [
        "lang_target_name",
        "lang_target_prof",
        "concept_hints_json",
        "cefr_diagnostics_block",
    ]

    # Find the actual Start node ID (Dify uses UUID-like ids, not the string "start")
    start_node_id = None
    for n in nodes:
        if n.get("data", {}).get("type") == "start":
            start_node_id = n.get("id")
            break
    if not start_node_id:
        raise RuntimeError("Start node not found — aborting patch")

    for n in nodes:
        if n.get("id") == "code_turn_check":
            data = n["data"]

            # 2.1 — Register in variables[] (input wiring from start node by ID)
            existing_vars = {v.get("variable") for v in data.get("variables", [])}
            for var_name in NEW_VARS_TO_WIRE:
                if var_name not in existing_vars:
                    data["variables"].append({
                        "variable": var_name,
                        "value_selector": [start_node_id, var_name],
                    })

            # 2.2 — Register in outputs declaration (Dify stores as dict with type schema)
            outputs = data.get("outputs", {})
            if isinstance(outputs, dict):
                for var_name in NEW_VARS_TO_WIRE:
                    if var_name not in outputs:
                        outputs[var_name] = {"type": "string", "children": None}

            code = data.get("code", "")

            # 2.3 — Inject 4 new params into main() signature
            if "concept_hints_json: str" not in code:
                m = re.search(r"def main\(", code)
                if m:
                    depth = 1
                    i = m.end()
                    while i < len(code) and depth > 0:
                        c = code[i]
                        if c == '(':
                            depth += 1
                        elif c == ')':
                            depth -= 1
                        i += 1
                    if depth == 0:
                        sig_end = i
                        inject = (
                            ",\n         lang_target_name: str = 'Anglais',"
                            " lang_target_prof: str = \"d'anglais\","
                            "\n         concept_hints_json: str = '{}',"
                            " cefr_diagnostics_block: str = ''"
                        )
                        code = code[:sig_end - 1] + inject + code[sig_end - 1:]

            # 2.4 — Replace hardcoded concept_hint_map dict with json.loads call
            pattern = re.compile(
                r"(\n(?P<indent>[ \t]+))concept_hint_map\s*=\s*\{[^{}]{0,50}(?:[^{}]|\{[^{}]*\})*?\}",
                re.DOTALL,
            )

            def _replace(m_):
                ind = m_.group("indent")
                return (
                    f"{m_.group(1)}concept_hint_map = {{}}\n"
                    f"{ind}try:\n"
                    f"{ind}    concept_hint_map = json.loads(concept_hints_json or '{{}}')\n"
                    f"{ind}except Exception:\n"
                    f"{ind}    concept_hint_map = {{}}"
                )

            if "json.loads(concept_hints_json" not in code:
                code, _ = pattern.subn(_replace, code, count=1)

            # 2.5 — Insert the 4 new keys into the return dict
            # Brace-balance approach: find "return {" then scan forward tracking depth
            if "'lang_target_name':" not in code:
                ret_idx = code.rfind("return {")
                if ret_idx >= 0:
                    depth = 0
                    i = ret_idx + len("return ")  # position of {
                    while i < len(code):
                        c = code[i]
                        if c == '{':
                            depth += 1
                        elif c == '}':
                            depth -= 1
                            if depth == 0:
                                break
                        i += 1
                    # i is now at the closing } of the return dict
                    # Typical 8-space indent for return dict entries
                    ind = "        "
                    addition = (
                        f"        # Sprint 5 Phase 3 — language-tutor passthrough\n"
                        f"        'lang_target_name': str(lang_target_name or 'Anglais'),\n"
                        f"        'lang_target_prof': str(lang_target_prof or \"d'anglais\"),\n"
                        f"        'concept_hints_json': str(concept_hints_json or '{{}}'),\n"
                        f"        'cefr_diagnostics_block': str(cefr_diagnostics_block or ''),\n"
                        f"    "
                    )
                    # Ensure there's a trailing comma on the last existing entry (look back from i)
                    # Check last non-whitespace before i
                    j = i - 1
                    while j > 0 and code[j] in " \t\n":
                        j -= 1
                    needs_comma = code[j] != ","
                    prefix = "," if needs_comma else ""
                    code = code[:i] + prefix + "\n" + addition + code[i:]

            data["code"] = code
            break

    # ── 3. llm_onboarding: LEAVE EN prompt AS-IS (critical) ──────────────
    # The onboarding branch runs when if_profil=false (new user, no profile yet).
    # That branch BYPASSES code_turn_check entirely. Therefore we CANNOT use
    # {{#code_turn_check.X#}} refs here — VariablePool won't have those keys.
    # Keep the original EN persona hardcoded for first-time users. Maestro ES /
    # Professore IT / etc. will be SEPARATE Dify apps with their own onboarding
    # prompts (content pack Phase 4).
    # The `for` loop below is intentionally dead-code (empty nodes list) to
    # preserve the script logic for future reference without applying it.
    for n in []:
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
                        "{{#code_turn_check.cefr_diagnostics_block#}}\n\n",
                        txt, count=1,
                    )
                    # Also replace the "REGLE CRITIQUE : PALIER DE DEPART" first-question map
                    patt2 = re.compile(
                        r"La PREMIERE question.{10,100}:\s*\n(- Si.{5,200}\n){4,8}"
                        r"NE COMMENCE JAMAIS.{10,100}\.",
                        re.DOTALL,
                    )
                    txt = patt2.sub(
                        "La PREMIERE question en {{#code_turn_check.lang_target_name#}} "
                        "DOIT correspondre au niveau choisi par l'eleve (voir "
                        "paliers_first_question dans cefr_diagnostics_block ci-dessus).",
                        txt, count=1,
                    )
                    # Param persona
                    txt = txt.replace(
                        "Tu es Teacher, prof d'anglais",
                        "Tu es Teacher, prof {{#code_turn_check.lang_target_prof#}}",
                    )
                    # Param "en anglais" references
                    txt = txt.replace(
                        "tu passes a l'anglais",
                        "tu passes a {{#code_turn_check.lang_target_name#}}",
                    )
                    txt = txt.replace(
                        "questions en anglais",
                        "questions en {{#code_turn_check.lang_target_name#}}",
                    )
                    txt = txt.replace(
                        "question en anglais",
                        "question en {{#code_turn_check.lang_target_name#}}",
                    )
                    txt = txt.replace(
                        "echanges en anglais",
                        "echanges en {{#code_turn_check.lang_target_name#}}",
                    )
                    txt = txt.replace(
                        "en anglais DOIT correspondre",
                        "en {{#code_turn_check.lang_target_name#}} DOIT correspondre",
                    )
                    txt = txt.replace(
                        "en anglais aujourd'hui",
                        "en {{#code_turn_check.lang_target_name#}} aujourd'hui",
                    )
                    txt = txt.replace(
                        "l'anglais ? (travail",
                        "{{#code_turn_check.lang_target_name#}} ? (travail",
                    )
                    # Phase 3 follow-up: remaining narrative references
                    txt = txt.replace(
                        "Tu passes a l'anglais",
                        "Tu passes a {{#code_turn_check.lang_target_name#}}",
                    )
                    txt = txt.replace(
                        "tu evaluerais ton anglais",
                        "tu evaluerais ton {{#code_turn_check.lang_target_name#}}",
                    )
                    txt = txt.replace(
                        "questions EN ANGLAIS",
                        "questions EN {{#code_turn_check.lang_target_name#}}",
                    )
                    txt = txt.replace(
                        "premiere question EN ANGLAIS",
                        "premiere question EN {{#code_turn_check.lang_target_name#}}",
                    )
                    txt = txt.replace(
                        "La question DOIT etre en anglais",
                        "La question DOIT etre en {{#code_turn_check.lang_target_name#}}",
                    )
                    msg["text"] = txt
                    break
            break

    # ── 4. Other LLM nodes: param persona ──
    # IMPORTANT: exclude llm_onboarding — see section 3. Onboarding branch
    # bypasses code_turn_check so {{#code_turn_check.X#}} refs would fail.
    for n in nodes:
        if n.get("id") in ("llm_plan_choice", "llm_session"):
            pt = n["data"].get("prompt_template", [])
            for msg in pt:
                if msg.get("role") == "system":
                    msg["text"] = msg["text"].replace(
                        "Tu es Teacher, prof d'anglais",
                        "Tu es Teacher, prof {{#code_turn_check.lang_target_prof#}}",
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
