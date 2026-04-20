#!/usr/bin/env python3
"""Sprint 5 Phase 5 hotfix follow-up — wire learner_profile through code_profil_check.

Root cause : `llm_onboarding` is downstream of `code_profil_check` (via if_profil
→ false branch), NOT of `code_turn_check`. Dify's VariablePool only exposes
variables from nodes on the execution path. So `{{#code_turn_check.X#}}` and
`{{#start.X#}}` both fail in llm_onboarding.

Fix : add 2 new input variables to `code_profil_check` (wired from start), add
them to main() signature, return them in outputs. Then llm_onboarding can
reference `{{#code_profil_check.learner_profile_summary#}}`.

Idempotent.
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

VARS = ["learner_profile_json", "learner_profile_summary"]

ONBOARDING_PREPEND = (
    "<learner_profile>\n"
    "{{#code_profil_check.learner_profile_summary#}}\n"
    "</learner_profile>\n\n"
    "Si le bloc ci-dessus n'est pas vide, l'utilisateur a deja complete un QCM "
    "pre-chat : n'essaie PAS de recueillir a nouveau son prenom, ses objectifs "
    "ou son niveau. Utilise ces informations directement et enchaine sur le "
    "diagnostic observationnel en langue cible (Phase 2).\n\n"
)


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


def _wire_code_profil_check(nodes: list) -> bool:
    changed = False
    start_id = next((n["id"] for n in nodes if n.get("data", {}).get("type") == "start"), None)
    if not start_id:
        raise RuntimeError("start node not found")

    target = next((n for n in nodes if n.get("id") == "code_profil_check"), None)
    if not target:
        return False
    data = target["data"]

    # 1. variables[] — wire from start
    existing_vars = {v.get("variable") for v in data.get("variables", [])}
    for vn in VARS:
        if vn not in existing_vars:
            data["variables"].append({
                "variable": vn,
                "value_selector": [start_id, vn],
            })
            changed = True

    # 2. outputs{} — declare as string
    outputs = data.get("outputs", {})
    if isinstance(outputs, dict):
        for vn in VARS:
            if vn not in outputs:
                outputs[vn] = {"type": "string", "children": None}
                changed = True

    # 3. main() signature — inject 2 new params (idempotent)
    code = data.get("code", "")
    if "learner_profile_json: str" not in code:
        m = re.search(r"def main\(", code)
        if m:
            depth = 1
            i = m.end()
            while i < len(code) and depth > 0:
                if code[i] == '(':
                    depth += 1
                elif code[i] == ')':
                    depth -= 1
                i += 1
            if depth == 0:
                inject = (
                    ", learner_profile_json: str = '{}',"
                    " learner_profile_summary: str = ''"
                )
                code = code[:i - 1] + inject + code[i - 1:]
                changed = True

    # 4. Return dict: insert 2 keys into BOTH branches (the empty-body fallback
    #    AND the normal return). Use a simple text pattern : right before every
    #    `return {` closing `}`, insert the two keys if missing.
    if "'learner_profile_summary':" not in code:
        # Find every `return {` ... `}` block and inject 2 keys before the closer.
        # Approach : track each occurrence of `return {` and scan until matching brace.
        out = []
        i = 0
        while i < len(code):
            idx = code.find("return {", i)
            if idx < 0:
                out.append(code[i:])
                break
            out.append(code[i:idx])
            depth = 0
            j = idx + len("return ")
            while j < len(code):
                if code[j] == '{':
                    depth += 1
                elif code[j] == '}':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            # j is now at the closing brace of the return dict
            k = j - 1
            while k > 0 and code[k] in " \t\n":
                k -= 1
            needs_comma = code[k] != ","
            prefix = "," if needs_comma else ""
            addition = (
                "\n        # Sprint 5 Phase 5 — QCM learner profile passthrough (onboarding branch)\n"
                "        'learner_profile_json': str(learner_profile_json or '{}'),\n"
                "        'learner_profile_summary': str(learner_profile_summary or ''),\n"
                "    "
            )
            out.append(code[idx:j] + prefix + addition)
            i = j  # continue from the closing brace (not consumed)
        code = "".join(out)
        changed = True

    if code != data.get("code", ""):
        data["code"] = code
        changed = True
    return changed


def _prepend_llm_onboarding(nodes: list) -> bool:
    for n in nodes:
        if n.get("id") != "llm_onboarding":
            continue
        for msg in n["data"].get("prompt_template", []):
            if msg.get("role") != "system":
                continue
            txt = msg.get("text", "")
            if "<learner_profile>" in txt:
                return False  # already present (shouldn't be after Phase 12 revert)
            msg["text"] = ONBOARDING_PREPEND + txt
            return True
    return False


def patch_graph(graph_str: str) -> tuple[str, dict]:
    graph = json.loads(graph_str)
    nodes = graph.get("nodes", [])
    report = {
        "code_profil_check_wired": _wire_code_profil_check(nodes),
        "llm_onboarding_prepended": _prepend_llm_onboarding(nodes),
    }
    if not any(report.values()):
        return graph_str, report
    return json.dumps(graph, ensure_ascii=False), report


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
        new_graph, report = patch_graph(graph)
        if new_graph == graph:
            print(f"  [NOOP] {version} {report}")
            continue
        print(f"  [PATCH] {version} {report}  ({len(graph)} → {len(new_graph)} chars)")
        if dry_run:
            continue
        esc = new_graph.replace("'", "''")
        psql_exec(f"UPDATE workflows SET graph = '{esc}', updated_at = NOW() WHERE id = '{wf_id}';")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--only", choices=list(APPS.keys()))
    args = p.parse_args()
    slugs = [args.only] if args.only else list(APPS.keys())
    for s in slugs:
        process(s, dry_run=args.dry_run)
    if not args.dry_run:
        print("\nRestart dify : docker restart dify-api dify-worker")
    return 0


if __name__ == "__main__":
    sys.exit(main())
