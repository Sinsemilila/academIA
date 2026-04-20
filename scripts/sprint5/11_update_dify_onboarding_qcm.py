#!/usr/bin/env python3
"""Sprint 5 Phase 5 — Wire QCM onboarding into Dify chatflows (Teacher + Maestro).

Transforms both chatflows to accept QCM profile data from the backend:
  1. Add 2 Start inputs: `learner_profile_json` + `learner_profile_summary`
  2. Wire them through `code_turn_check` (Session 32 pattern : variables[] +
     main() signature + return dict + outputs)
  3. Prepend a <learner_profile> block at the top of `llm_onboarding` system
     prompt that injects {{#start.learner_profile_summary#}} — Start vars are
     always in the Dify VariablePool regardless of graph topology (so works
     even though the onboarding branch bypasses code_turn_check for new users).
  4. Inject {{#code_turn_check.learner_profile_summary#}} at the top of
     llm_session + llm_plan_choice (existing-user flows go through
     code_turn_check).

Idempotent : re-running after success is safe. The <learner_profile> block is
inserted only if not already present.

Preserves `conversation_variables` column untouched (Session 32 gotcha: strip
only happens via Dify admin API publish. SQL UPDATE of `graph` alone is safe).

Usage :
  python3 scripts/sprint5/11_update_dify_onboarding_qcm.py --dry-run   # preview
  python3 scripts/sprint5/11_update_dify_onboarding_qcm.py             # apply
  python3 scripts/sprint5/11_update_dify_onboarding_qcm.py --only teacher
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
    "teacher": {
        "app_id": "39565197-c9d1-4d5b-b66f-18925de236d9",
        "display": "Teacher (EN)",
    },
    "maestro": {
        "app_id": "47b0529c-b3a3-4651-8717-759e666172c9",
        "display": "Maestro (ES)",
    },
}

NEW_START_VARS = [
    {
        "type": "paragraph",
        "variable": "learner_profile_json",
        "label": "learner_profile_json",
        "required": False,
        "max_length": 10000,
        "default": "{}",
    },
    {
        "type": "paragraph",
        "variable": "learner_profile_summary",
        "label": "learner_profile_summary",
        "required": False,
        "max_length": 2000,
        "default": "",
    },
]

VARS_TO_WIRE = ["learner_profile_json", "learner_profile_summary"]

ONBOARDING_PREPEND = (
    "<learner_profile>\n"
    "{{#start.learner_profile_summary#}}\n"
    "</learner_profile>\n\n"
    "Si le bloc ci-dessus n'est pas vide, l'utilisateur a deja complete un QCM "
    "pre-chat : n'essaie PAS de recueillir a nouveau son prenom, ses objectifs "
    "ou son niveau. Utilise ces informations directement et enchaine sur le "
    "diagnostic observationnel en langue cible (Phase 2).\n\n"
)

SESSION_PREPEND = (
    "<learner_profile>\n"
    "{{#code_turn_check.learner_profile_summary#}}\n"
    "</learner_profile>\n\n"
)


# ── psql helpers ─────────────────────────────────────────────────────

def psql_q(sql: str) -> str:
    cmd = ["docker", "exec", "-i", DB_CONTAINER, "psql",
           "-U", DB_USER, "-d", DB_NAME, "-t", "-A", "-c", sql]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.rstrip("\n")


def psql_exec(sql: str) -> None:
    cmd = ["docker", "exec", "-i", DB_CONTAINER, "psql",
           "-U", DB_USER, "-d", DB_NAME, "-v", "ON_ERROR_STOP=1"]
    subprocess.run(cmd, input=sql, text=True, check=True)


# ── patches ──────────────────────────────────────────────────────────

def _ensure_start_vars(nodes: list) -> bool:
    changed = False
    for n in nodes:
        if n.get("data", {}).get("type") == "start":
            existing = {v.get("variable") for v in n["data"].get("variables", [])}
            for nv in NEW_START_VARS:
                if nv["variable"] not in existing:
                    n["data"]["variables"].append(nv)
                    changed = True
            return changed
    raise RuntimeError("Start node not found")


def _wire_code_turn_check(nodes: list) -> bool:
    changed = False
    start_id = next((n["id"] for n in nodes if n.get("data", {}).get("type") == "start"), None)
    if not start_id:
        raise RuntimeError("Start node id not found")

    for n in nodes:
        if n.get("id") != "code_turn_check":
            continue
        data = n["data"]
        existing_vars = {v.get("variable") for v in data.get("variables", [])}
        for vn in VARS_TO_WIRE:
            if vn not in existing_vars:
                data["variables"].append({
                    "variable": vn,
                    "value_selector": [start_id, vn],
                })
                changed = True

        outputs = data.get("outputs", {})
        if isinstance(outputs, dict):
            for vn in VARS_TO_WIRE:
                if vn not in outputs:
                    outputs[vn] = {"type": "string", "children": None}
                    changed = True

        code = data.get("code", "")

        # Inject 2 new params into main() signature
        if "learner_profile_json: str" not in code:
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
                        ",\n         learner_profile_json: str = '{}',"
                        " learner_profile_summary: str = ''"
                    )
                    code = code[:sig_end - 1] + inject + code[sig_end - 1:]
                    changed = True

        # Insert 2 new keys into return dict
        if "'learner_profile_summary':" not in code:
            ret_idx = code.rfind("return {")
            if ret_idx >= 0:
                depth = 0
                i = ret_idx + len("return ")
                while i < len(code):
                    c = code[i]
                    if c == '{':
                        depth += 1
                    elif c == '}':
                        depth -= 1
                        if depth == 0:
                            break
                    i += 1
                addition = (
                    "        # Sprint 5 Phase 5 — QCM learner profile passthrough\n"
                    "        'learner_profile_json': str(learner_profile_json or '{}'),\n"
                    "        'learner_profile_summary': str(learner_profile_summary or ''),\n"
                    "    "
                )
                j = i - 1
                while j > 0 and code[j] in " \t\n":
                    j -= 1
                needs_comma = code[j] != ","
                prefix = "," if needs_comma else ""
                code = code[:i] + prefix + "\n" + addition + code[i:]
                changed = True

        if code != data.get("code", ""):
            data["code"] = code
            changed = True
        return changed
    # Older workflow versions may lack code_turn_check — skip, don't abort.
    return changed


def _prepend_system_prompt(node: dict, marker: str, prepend_text: str) -> bool:
    """Prepend text to the first system message of a node if not already present."""
    pt = node["data"].get("prompt_template", [])
    for msg in pt:
        if msg.get("role") == "system":
            txt = msg.get("text", "")
            if marker in txt:
                return False
            msg["text"] = prepend_text + txt
            return True
    return False


def _patch_llm_onboarding(nodes: list) -> bool:
    for n in nodes:
        if n.get("id") == "llm_onboarding":
            return _prepend_system_prompt(
                n,
                marker="<learner_profile>",
                prepend_text=ONBOARDING_PREPEND,
            )
    return False


def _patch_llm_session_plan(nodes: list) -> bool:
    changed = False
    for n in nodes:
        if n.get("id") in ("llm_session", "llm_plan_choice"):
            if _prepend_system_prompt(
                n,
                marker="<learner_profile>",
                prepend_text=SESSION_PREPEND,
            ):
                changed = True
    return changed


def patch_graph(graph_str: str) -> tuple[str, dict]:
    graph = json.loads(graph_str)
    nodes = graph.get("nodes", [])
    report = {
        "start_vars": _ensure_start_vars(nodes),
        "code_turn_check": _wire_code_turn_check(nodes),
        "llm_onboarding": _patch_llm_onboarding(nodes),
        "llm_session_plan": _patch_llm_session_plan(nodes),
    }
    if not any(report.values()):
        return graph_str, report
    return json.dumps(graph, ensure_ascii=False), report


# ── main ─────────────────────────────────────────────────────────────

def process_app(slug: str, dry_run: bool) -> None:
    app = APPS[slug]
    print(f"\n=== {app['display']}  (app_id={app['app_id']}) ===")

    # 1. Backup
    if not dry_run:
        print("  [1/4] Refreshing backup table...")
        psql_exec(f"""
            CREATE TABLE IF NOT EXISTS dify_workflows_backup_sprint5_phase5 AS
            SELECT id, app_id, version, graph, conversation_variables, updated_at
            FROM workflows WHERE 1=0;
            INSERT INTO dify_workflows_backup_sprint5_phase5
                SELECT id, app_id, version, graph, conversation_variables, updated_at
                FROM workflows
                WHERE app_id = '{app['app_id']}'
                  AND id NOT IN (SELECT id FROM dify_workflows_backup_sprint5_phase5);
        """)
        n = psql_q(
            f"SELECT COUNT(*) FROM dify_workflows_backup_sprint5_phase5 "
            f"WHERE app_id = '{app['app_id']}'"
        )
        print(f"    Backup rows for this app : {n}")

    # 2. Target only draft + the MOST RECENT published version.
    # Older historical versions are preserved untouched in the table.
    rows = psql_q(
        f"""
        (SELECT id || '|' || version FROM workflows
         WHERE app_id = '{app['app_id']}' AND version = 'draft' LIMIT 1)
        UNION ALL
        (SELECT id || '|' || version FROM workflows
         WHERE app_id = '{app['app_id']}' AND version != 'draft'
         ORDER BY updated_at DESC LIMIT 1)
        """
    )
    targets = [line.split("|", 1) for line in rows.splitlines() if line]
    print(f"  [2/4] Versions to patch (draft + latest published) : {len(targets)}")

    # 3. Patch each
    for wf_id, version in targets:
        graph = psql_q(f"SELECT graph FROM workflows WHERE id = '{wf_id}'")
        new_graph, report = patch_graph(graph)
        if new_graph == graph:
            print(f"    [NOOP] {version} (already patched)")
            continue
        print(f"    [DIFF] {version} : {report}  ({len(graph)} → {len(new_graph)} chars)")
        if dry_run:
            continue
        escaped = new_graph.replace("'", "''")
        psql_exec(
            f"UPDATE workflows SET graph = '{escaped}', updated_at = NOW() "
            f"WHERE id = '{wf_id}';"
        )

    print(f"  [3/4] {'DRY RUN' if dry_run else 'APPLIED'}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", choices=list(APPS.keys()))
    args = parser.parse_args()

    slugs = [args.only] if args.only else list(APPS.keys())
    for slug in slugs:
        process_app(slug, dry_run=args.dry_run)

    if not args.dry_run:
        print("\n[4/4] Restart Dify services to reload workflows :")
        print("      docker restart dify-api dify-worker")

    return 0


if __name__ == "__main__":
    sys.exit(main())
