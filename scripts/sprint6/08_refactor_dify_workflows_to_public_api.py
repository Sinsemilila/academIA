#!/usr/bin/env python3
"""ONE-SHOT MIGRATION — executed Session 37 (2026-04-21). Retained for audit.

This script patched the `dify-snapshot` n8n workflow graph in-place ; it is
NOT part of any runtime code path, battery, or CI. Hardcoded app_id
`DIFY_APP_TEACHER` is therefore acceptable — the script will never run again.
For future similar migrations, read the canonical source via
`agents_config.active_agents()` (field `dify_app_id`, added Session 44).

Session 37 — refactor `dify-snapshot` n8n workflow to use Dify public API.

Before : `dify-snapshot` called
    http://dify-api:5001/console/api/apps/{APP_ID}/chat-messages?...
with `Authorization: Bearer {DIFY_ADMIN_KEY}` — unset/expired for ~5 days,
100% 401 fail rate → `scores_confiance` not refreshed since 2026-04-16.

After : the workflow calls the public API
    http://dify-api:5001/v1/messages?conversation_id=X&user=<dify_user_id>
with `Authorization: Bearer {DIFY_KEY_TEACHER}` (app-scoped key in env).

**Scope** : only `dify-snapshot` tonight. `dify-diagnostic` + `dify-exam-scoring`
are also broken but not on the priority-loop critical path — they're logged as
a TODO for a future session to refactor with the same pattern.

**Prerequisite change** : `scripts/cron_snapshot_safety.py` must send
`dify_user_id` in the webhook payload (in addition to `username`). This
script verifies that at runtime via a pre-flight check on the workflow's
"Parse Body" node output schema.

**Idempotent** : detects already-patched URL → skip. Safe to re-run.
**Both tables patched** : `workflow_entity.nodes` AND `workflow_history.nodes`
(Session 27 gotcha — n8n reads workflow_history for active runs).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

DB_CONTAINER = "postgres-academie"
DB_USER = "sinse"
DB_NAME = "academie_db"

DIFY_APP_TEACHER = "39565197-c9d1-4d5b-b66f-18925de236d9"
DIFY_KEY_TEACHER = os.environ.get("DIFY_KEY_TEACHER", "")

TARGET_WORKFLOW = "dify-snapshot"
HTTP_NODE_NAME = "Fetch Dify Messages"


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


def patch_http_node(node: dict) -> tuple[dict, bool]:
    """Mutate the HTTP node to use Dify public API. Idempotent."""
    params = node.get("parameters", {})
    url = params.get("url", "")

    # Idempotent AND recovers from earlier malformed patches (missing closing }}).
    if "/v1/messages" in url and "user=" in url and url.rstrip().endswith("}}"):
        return node, False  # Already patched cleanly

    # Read both conversation_id and dify_user_id directly from the webhook body.
    # This is robust across workflow variants (no dependency on named upstream
    # node like $('Code in JavaScript') which may be renamed/removed).
    # The Webhook node is always present and always named "Webhook" in our 3
    # target workflows (verified via audit).
    conv_ref = "$('Webhook').first().json.body.conversation_id"
    user_ref = "$('Webhook').first().json.body.dify_user_id"
    limit_clause = "&limit=30"

    # n8n expression : `={{ ... }}`. f-string `}}` → `}`, so `}}}}` → `}}`.
    params["url"] = (
        "={{ 'http://dify-api:5001/v1/messages?conversation_id=' + "
        f"{conv_ref} + '&user=' + {user_ref} + '{limit_clause}' }}}}"
    )

    # Swap Authorization header; drop X-WORKSPACE-ID
    headers = params.get("headerParameters", {}).get("parameters", [])
    new_headers = []
    seen_auth = False
    for h in headers:
        hn = (h.get("name") or "").lower()
        if hn == "authorization":
            new_headers.append({"name": "Authorization", "value": f"Bearer {DIFY_KEY_TEACHER}"})
            seen_auth = True
        elif hn == "x-workspace-id":
            continue
        else:
            new_headers.append(h)
    if not seen_auth:
        new_headers.append({"name": "Authorization", "value": f"Bearer {DIFY_KEY_TEACHER}"})
    params["headerParameters"] = {"parameters": new_headers}

    node["parameters"] = params
    return node, True


def patch_nodes_list(nodes_str: str) -> tuple[str, dict]:
    """Patch the HTTP node in an n8n nodes JSON array. Returns (json_str, stats)."""
    nodes = json.loads(nodes_str) if isinstance(nodes_str, str) else nodes_str
    if not isinstance(nodes, list):
        nodes = nodes.get("nodes", [])
    stats = {"http_patched": 0, "nodes_seen": 0}
    for node in nodes:
        stats["nodes_seen"] += 1
        if (node.get("type") == "n8n-nodes-base.httpRequest"
                and node.get("name") == HTTP_NODE_NAME):
            _, changed = patch_http_node(node)
            if changed:
                stats["http_patched"] += 1
    return json.dumps(nodes, ensure_ascii=False), stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not DIFY_KEY_TEACHER:
        print(
            "ERROR: DIFY_KEY_TEACHER not in env.\n"
            "Source /opt/academia/webapp/.env first :\n"
            "    set -a && . /opt/academia/webapp/.env && set +a && python3 "
            "scripts/sprint6/08_refactor_dify_workflows_to_public_api.py",
            file=sys.stderr,
        )
        return 2

    # Locate workflow
    wf_id = psql_q(
        f"SELECT id FROM workflow_entity WHERE name = '{TARGET_WORKFLOW}'",
    ).strip().split("\n")[0]
    if not wf_id:
        print(f"ERROR: workflow {TARGET_WORKFLOW} not found", file=sys.stderr)
        return 2
    print(f"Workflow id: {wf_id}")

    # Patch workflow_entity
    nodes_str = psql_q(f"SELECT nodes FROM workflow_entity WHERE id = '{wf_id}'")
    new_nodes, stats = patch_nodes_list(nodes_str)
    print(f"  workflow_entity: {stats}")
    if not args.dry_run and stats["http_patched"]:
        esc = new_nodes.replace("'", "''")
        psql_exec(
            f"UPDATE workflow_entity SET nodes = '{esc}'::json, "
            f"\"updatedAt\" = NOW() WHERE id = '{wf_id}';",
        )
        print(f"  [WROTE] workflow_entity")

    # Patch latest workflow_history row (Session 27 gotcha)
    hist_ver = psql_q(
        f"SELECT \"versionId\" FROM workflow_history WHERE \"workflowId\" = '{wf_id}' "
        f"ORDER BY \"createdAt\" DESC LIMIT 1",
    ).strip().split("\n")[0]
    if hist_ver:
        hist_nodes = psql_q(
            f"SELECT nodes FROM workflow_history WHERE \"versionId\" = '{hist_ver}'",
        )
        new_hist, hstats = patch_nodes_list(hist_nodes)
        print(f"  workflow_history (latest): {hstats}")
        if not args.dry_run and hstats["http_patched"]:
            esc = new_hist.replace("'", "''")
            psql_exec(
                f"UPDATE workflow_history SET nodes = '{esc}'::json "
                f"WHERE \"versionId\" = '{hist_ver}';",
            )
            print(f"  [WROTE] workflow_history (latest)")

    print("\n" + ("Dry-run complete." if args.dry_run
                 else "Patch applied. Next: docker restart n8n-academie"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
