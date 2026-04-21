#!/usr/bin/env python3
"""Session 37 followup — refactor `dify-diagnostic` + `dify-exam-scoring` to Dify public API.

Same pattern as `08_refactor_dify_workflows_to_public_api.py` (snapshot), but here
both callers are Dify workflows (Teacher + Maestro), not a cron. So instead of
having the caller push `dify_app_key` in the webhook body, we resolve it inside
n8n via a Postgres lookup on the Dify `api_tokens` table (same DB as n8n).

Wiring inserted per target workflow :

    Parse Body → Resolve Dify App Key (new PG node) → Fetch Dify/Exam Messages (public API)

The new PG node dispatches the app_id by `domain` ('es' → Maestro, else Teacher)
and returns `dify_app_key`. The HTTP node reads `conversation_id` + `username`
from Parse Body (the caller already sends `username = {{#sys.user_id#}}`,
which IS the Dify public-API `user=` param) and `dify_app_key` from the
resolve node.

**Idempotent** — detects an already-patched HTTP URL and skips.
**Both tables patched** — `workflow_entity` and latest `workflow_history` row.
"""
from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import uuid

DB_CONTAINER = "postgres-academie"
DB_USER = "sinse"
DB_NAME = "academie_db"

DIFY_APP_TEACHER = "39565197-c9d1-4d5b-b66f-18925de236d9"
DIFY_APP_MAESTRO = "47b0529c-b3a3-4651-8717-759e666172c9"

# Credential ID used by existing Postgres nodes in both workflows.
# Sourced from workflow_entity.nodes on 2026-04-21.
PG_CREDENTIAL = {"id": "NpF5tjOzvAWkHR2n", "name": "Postgres account"}

RESOLVE_NODE_NAME = "Resolve Dify App Key"

RESOLVE_QUERY = (
    "SELECT token AS dify_app_key "
    "FROM api_tokens "
    "WHERE app_id = (CASE "
    f"WHEN '{{{{ $('Parse Body').first().json.domain }}}}' = 'es' THEN '{DIFY_APP_MAESTRO}' "
    f"ELSE '{DIFY_APP_TEACHER}' "
    "END)::uuid "
    "AND type = 'app' "
    "ORDER BY created_at ASC "
    "LIMIT 1"
)


# Per-target wiring spec
TARGETS = [
    {
        "workflow": "dify-diagnostic",
        "workflow_id": "58dd0014770a4c",
        "http_node": "Fetch Dify Messages",
        "predecessor": "Parse Body",  # what was feeding the HTTP node
        "limit": 30,
    },
    {
        "workflow": "dify-exam-scoring",
        "workflow_id": "y52Fa9sYBmtuwz8y",
        "http_node": "Fetch Exam Messages",
        "predecessor": "Fetch Error Profile",
        "limit": 50,
    },
]


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


def build_resolve_node(reference_pos: list[float]) -> dict:
    """Postgres node that resolves dify_app_key by domain."""
    # Slight offset from the predecessor so layout stays readable in the UI.
    pos = [reference_pos[0] + 200, reference_pos[1] + 150] if reference_pos else [500, 150]
    return {
        "id": str(uuid.uuid4()),
        "name": RESOLVE_NODE_NAME,
        "type": "n8n-nodes-base.postgres",
        "position": pos,
        "parameters": {
            "query": RESOLVE_QUERY,
            "options": {},
            "operation": "executeQuery",
        },
        "credentials": {"postgres": copy.deepcopy(PG_CREDENTIAL)},
        "typeVersion": 2.6,
    }


def patch_http_node(node: dict, limit: int) -> bool:
    """Mutate HTTP node to call Dify public API. Idempotent.

    Returns True if changed.
    """
    params = node.get("parameters", {})
    url = params.get("url", "")

    if "/v1/messages" in url and "user=" in url and url.rstrip().endswith("}}"):
        return False  # Already patched

    # Read conversation_id + username from Parse Body.
    # `username` is set by Dify callers to `{{#sys.user_id#}}`, which IS the
    # Dify public-API `user=` param (end_users.session_id).
    conv_ref = "$('Parse Body').first().json.conversation_id"
    user_ref = "$('Parse Body').first().json.username"

    # n8n expression : `={{ ... }}`. In an f-string, `}}` → `}`, so `}}}}` → `}}`.
    params["url"] = (
        "={{ 'http://dify-api:5001/v1/messages?conversation_id=' + "
        f"{conv_ref} + '&user=' + {user_ref} + '&limit={limit}' }}}}"
    )

    # Swap Authorization header to dynamically fetch from Resolve node; drop X-WORKSPACE-ID.
    headers = params.get("headerParameters", {}).get("parameters", [])
    auth_value = (
        "={{ 'Bearer ' + $('" + RESOLVE_NODE_NAME +
        "').first().json.dify_app_key }}"
    )
    new_headers = []
    seen_auth = False
    for h in headers:
        hn = (h.get("name") or "").lower()
        if hn == "authorization":
            new_headers.append({"name": "Authorization", "value": auth_value})
            seen_auth = True
        elif hn == "x-workspace-id":
            continue
        else:
            new_headers.append(h)
    if not seen_auth:
        new_headers.append({"name": "Authorization", "value": auth_value})
    params["headerParameters"] = {"parameters": new_headers}

    node["parameters"] = params
    return True


def rewire_connections(conns: dict, predecessor: str, http_node: str) -> bool:
    """Rewire: predecessor → Resolve → http_node. Idempotent.

    Returns True if changed.
    """
    pred = conns.get(predecessor)
    if not pred or not pred.get("main"):
        raise RuntimeError(f"Predecessor '{predecessor}' has no main output")

    # First main output slot
    slot0 = pred["main"][0]
    # Already wired through Resolve ?
    if any(edge.get("node") == RESOLVE_NODE_NAME for edge in slot0):
        return False

    # Replace the direct edge to http_node with an edge to Resolve
    new_slot0 = []
    removed_http_edge = False
    for edge in slot0:
        if edge.get("node") == http_node and edge.get("type") == "main":
            removed_http_edge = True
            continue
        new_slot0.append(edge)
    new_slot0.append({"node": RESOLVE_NODE_NAME, "type": "main", "index": 0})
    pred["main"][0] = new_slot0

    if not removed_http_edge:
        # Caller config changed : predecessor didn't directly feed http_node.
        # Safer to abort than silently create a dangling graph.
        raise RuntimeError(
            f"'{predecessor}' did not feed '{http_node}' directly — abort. "
            f"Existing edges: {slot0}"
        )

    # Resolve → http_node
    conns[RESOLVE_NODE_NAME] = {
        "main": [[{"node": http_node, "type": "main", "index": 0}]]
    }
    return True


def patch_workflow_blob(nodes_str: str, conns_str: str, target: dict) -> tuple[str, str, dict]:
    """Patch a (nodes, connections) pair. Returns (nodes_json, conns_json, stats)."""
    nodes = json.loads(nodes_str)
    conns = json.loads(conns_str)
    stats = {"http_patched": 0, "resolve_added": 0, "conns_rewired": 0}

    # Find reference position from predecessor
    pred_pos = None
    for n in nodes:
        if n.get("name") == target["predecessor"]:
            pred_pos = n.get("position")
            break

    # Add Resolve node if missing, or refresh its query if already present.
    resolve_node = next((n for n in nodes if n.get("name") == RESOLVE_NODE_NAME), None)
    if resolve_node is None:
        nodes.append(build_resolve_node(pred_pos or [500, 150]))
        stats["resolve_added"] = 1
    else:
        current_q = resolve_node.get("parameters", {}).get("query", "")
        if current_q != RESOLVE_QUERY:
            resolve_node.setdefault("parameters", {})["query"] = RESOLVE_QUERY
            stats["resolve_query_updated"] = 1

    # Patch HTTP node
    for n in nodes:
        if n.get("type") == "n8n-nodes-base.httpRequest" and n.get("name") == target["http_node"]:
            if patch_http_node(n, target["limit"]):
                stats["http_patched"] = 1
            break

    # Rewire connections
    if rewire_connections(conns, target["predecessor"], target["http_node"]):
        stats["conns_rewired"] = 1

    return json.dumps(nodes, ensure_ascii=False), json.dumps(conns, ensure_ascii=False), stats


def patch_workflow(target: dict, dry_run: bool) -> None:
    wf_id = target["workflow_id"]
    print(f"\n=== {target['workflow']} (id={wf_id}) ===")

    # workflow_entity
    nodes_str = psql_q(f"SELECT nodes FROM workflow_entity WHERE id = '{wf_id}'")
    conns_str = psql_q(f"SELECT connections FROM workflow_entity WHERE id = '{wf_id}'")
    new_nodes, new_conns, stats = patch_workflow_blob(nodes_str, conns_str, target)
    print(f"  workflow_entity: {stats}")
    if not dry_run and any(stats.values()):
        esc_n = new_nodes.replace("'", "''")
        esc_c = new_conns.replace("'", "''")
        psql_exec(
            f"UPDATE workflow_entity SET nodes = '{esc_n}'::json, "
            f"connections = '{esc_c}'::json, \"updatedAt\" = NOW() WHERE id = '{wf_id}';"
        )
        print(f"  [WROTE] workflow_entity")

    # latest workflow_history
    hist_ver = psql_q(
        f"SELECT \"versionId\" FROM workflow_history WHERE \"workflowId\" = '{wf_id}' "
        f"ORDER BY \"createdAt\" DESC LIMIT 1"
    ).strip().split("\n")[0]
    if not hist_ver:
        print("  (no workflow_history row)")
        return

    h_nodes = psql_q(f"SELECT nodes FROM workflow_history WHERE \"versionId\" = '{hist_ver}'")
    h_conns = psql_q(f"SELECT connections FROM workflow_history WHERE \"versionId\" = '{hist_ver}'")
    new_h_nodes, new_h_conns, h_stats = patch_workflow_blob(h_nodes, h_conns, target)
    print(f"  workflow_history (latest, versionId={hist_ver}): {h_stats}")
    if not dry_run and any(h_stats.values()):
        esc_n = new_h_nodes.replace("'", "''")
        esc_c = new_h_conns.replace("'", "''")
        psql_exec(
            f"UPDATE workflow_history SET nodes = '{esc_n}'::json, "
            f"connections = '{esc_c}'::json WHERE \"versionId\" = '{hist_ver}';"
        )
        print(f"  [WROTE] workflow_history")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for target in TARGETS:
        patch_workflow(target, args.dry_run)

    print("\n" + ("Dry-run complete." if args.dry_run
                  else "Patch applied. Next: docker restart n8n-academie"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
