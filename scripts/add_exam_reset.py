#!/usr/bin/env python3
"""
Add var_assigner_exam_reset after exam bilan to reset exam_mode to "off".
Also add edge from code_exam_bilan -> var_assigner_exam_reset.
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

    # Check if already exists
    if any(n["id"] == "var_assigner_exam_reset" for n in nodes):
        print("  Already exists: var_assigner_exam_reset — skipping")
        return graph

    # Find position
    bilan_x, bilan_y = 2550, 300
    for n in nodes:
        if n["id"] == "code_exam_bilan":
            pos = n.get("position", {})
            bilan_x = pos.get("x", 2550)
            bilan_y = pos.get("y", 300)

    # Add reset assigner
    reset_node = {
        "id": "var_assigner_exam_reset",
        "data": {
            "type": "assigner",
            "title": "Reset Exam",
            "version": "2",
            "items": [
                {
                    "variable_selector": ["conversation", "exam_mode"],
                    "operation": "over-write",
                    "input_type": "constant",
                    "value": "off"
                },
                {
                    "variable_selector": ["conversation", "exam_question_num"],
                    "operation": "over-write",
                    "input_type": "constant",
                    "value": 0
                },
                {
                    "variable_selector": ["conversation", "exam_responses"],
                    "operation": "over-write",
                    "input_type": "constant",
                    "value": "[]"
                }
            ],
            "selected": False
        },
        "position": {"x": bilan_x + 250, "y": bilan_y + 100}
    }
    nodes.append(reset_node)
    print("  Added: var_assigner_exam_reset")

    # Add edge
    edges.append({
        "id": "edge-bilan-to-resetexam",
        "source": "code_exam_bilan",
        "target": "var_assigner_exam_reset",
        "type": "custom",
        "data": {"sourceType": "code", "targetType": "assigner"}
    })
    print("  Added edge: code_exam_bilan -> var_assigner_exam_reset")

    return graph


for wf_id, label in [(PUBLISHED_ID, "published"), (DRAFT_ID, "draft")]:
    print(f"\n=== Adding exam reset to {label} ({wf_id}) ===")
    try:
        graph = load_graph(wf_id)
        graph = patch_graph(graph)
        save_graph(wf_id, graph)
    except Exception as e:
        print(f"  [ERR] {e}")
        import traceback
        traceback.print_exc()

print("\nDone. docker restart dify-api dify-worker")
