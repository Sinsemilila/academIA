#!/usr/bin/env python3
"""
Fix var_assigner_exam and var_assigner_exam_start:
- operation "set" with input_type "variable" is NOT supported in Dify v2
- Must use operation "over-write" for variable references
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

    for node in nodes:
        nid = node["id"]

        # Fix var_assigner_exam — 3 variables from code_exam_track
        if nid == "var_assigner_exam":
            node["data"] = {
                "type": "assigner",
                "title": "Update Exam Vars",
                "version": "2",
                "items": [
                    {
                        "variable_selector": ["conversation", "exam_mode"],
                        "operation": "over-write",
                        "input_type": "variable",
                        "value": ["code_exam_track", "new_exam_mode"]
                    },
                    {
                        "variable_selector": ["conversation", "exam_question_num"],
                        "operation": "over-write",
                        "input_type": "variable",
                        "value": ["code_exam_track", "new_question_num"]
                    },
                    {
                        "variable_selector": ["conversation", "exam_responses"],
                        "operation": "over-write",
                        "input_type": "variable",
                        "value": ["code_exam_track", "new_responses"]
                    }
                ],
                "selected": False
            }
            print("  Fixed: var_assigner_exam (over-write instead of set)")

        # Fix var_assigner_exam_start — 1 variable from code_exam_detect
        if nid == "var_assigner_exam_start":
            node["data"] = {
                "type": "assigner",
                "title": "Set Exam Start",
                "version": "2",
                "items": [
                    {
                        "variable_selector": ["conversation", "exam_mode"],
                        "operation": "over-write",
                        "input_type": "variable",
                        "value": ["code_exam_detect", "new_exam_mode"]
                    }
                ],
                "selected": False
            }
            print("  Fixed: var_assigner_exam_start (over-write instead of set)")

    return graph


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

print("\nDone. docker restart dify-api dify-worker")
