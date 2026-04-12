#!/usr/bin/env python3
"""
Corrige le trigger diagnostic dans le chatflow Teacher :
1. if_eval_ready : format 'cases' (comme if_profil/if_first_turn)
2. Edges : ajouter type:'custom' + data:{sourceType,targetType}
3. sourceHandle : utiliser case_id au lieu de 'true'
"""

import json
import subprocess

PUBLISHED_ID = "c52a451f-e381-46f1-a23a-077197b0fccb"
DRAFT_ID = "ed0d1c91-8c9a-48ad-9c3a-063981f8da87"


def load_graph(workflow_id):
    result = subprocess.run(
        ["docker", "exec", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db",
         "-t", "-c", f"SELECT graph FROM workflows WHERE id='{workflow_id}';"],
        capture_output=True, text=True
    )
    return json.loads(result.stdout.strip())


def save_graph(workflow_id, graph):
    graph_json = json.dumps(graph, ensure_ascii=False)
    graph_sql = graph_json.replace("'", "''")
    sql = f"UPDATE workflows SET graph = '{graph_sql}'::json, updated_at = NOW() WHERE id = '{workflow_id}';"
    result = subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db"],
        input=sql, capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"  [OK] {workflow_id}: {result.stdout.strip()}")
    else:
        print(f"  [ERR] {workflow_id}: {result.stderr.strip()}")


def patch_graph(graph):
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    # --- 1. Fix if_eval_ready node: use proper 'cases' format ---
    for node in nodes:
        if node["id"] == "if_eval_ready":
            node["data"] = {
                "type": "if-else",
                "title": "Diagnostic ready?",
                "cases": [{
                    "id": "eval_true",
                    "case_id": "eval_true",
                    "conditions": [{
                        "value": "true",
                        "varType": "boolean",
                        "variable_selector": ["code_eval_check", "eval_ready"],
                        "comparison_operator": "="
                    }],
                    "logical_operator": "and"
                }],
                "selected": False
            }
            print("  Fixed: if_eval_ready → proper cases format")

    # --- 2. Fix edges: add type + data + correct sourceHandle ---
    new_edges = []
    for e in edges:
        eid = e.get("id", "")

        if eid == "edge-onb-to-eval":
            # llm_onboarding → code_eval_check
            new_edges.append({
                "id": "edge-onb-to-eval",
                "source": "llm_onboarding",
                "target": "code_eval_check",
                "type": "custom",
                "data": {"sourceType": "llm", "targetType": "code"}
            })
            print("  Fixed edge: llm_onboarding → code_eval_check")

        elif eid == "edge-eval-to-answer":
            # code_eval_check → answer_onboarding
            new_edges.append({
                "id": "edge-eval-to-answer",
                "source": "code_eval_check",
                "target": "answer_onboarding",
                "type": "custom",
                "data": {"sourceType": "code", "targetType": "answer"}
            })
            print("  Fixed edge: code_eval_check → answer_onboarding")

        elif eid == "edge-eval-to-if":
            # code_eval_check → if_eval_ready
            new_edges.append({
                "id": "edge-eval-to-if",
                "source": "code_eval_check",
                "target": "if_eval_ready",
                "type": "custom",
                "data": {"sourceType": "code", "targetType": "if-else"}
            })
            print("  Fixed edge: code_eval_check → if_eval_ready")

        elif eid == "edge-if-to-diag":
            # if_eval_ready (true) → http_diagnostic — sourceHandle = case_id
            new_edges.append({
                "id": "edge-if-to-diag",
                "source": "if_eval_ready",
                "target": "http_diagnostic",
                "sourceHandle": "eval_true",
                "type": "custom",
                "data": {"sourceType": "if-else", "targetType": "http-request"}
            })
            print("  Fixed edge: if_eval_ready → http_diagnostic (sourceHandle=eval_true)")

        else:
            new_edges.append(e)

    graph["edges"] = new_edges
    print(f"  Total edges: {len(new_edges)}")
    return graph


# ============================================================
# APPLY
# ============================================================
for wf_id, label in [(PUBLISHED_ID, "published"), (DRAFT_ID, "draft")]:
    print(f"\n=== Fixing {label} ({wf_id}) ===")
    try:
        graph = load_graph(wf_id)
        graph = patch_graph(graph)
        save_graph(wf_id, graph)
    except Exception as e:
        print(f"  [ERR] {e}")
        import traceback
        traceback.print_exc()

print("\nDone. Restart Dify: docker restart dify-api dify-worker")
