#!/usr/bin/env python3
"""
Fix http_exam_scoring node to use correct Dify HTTP request format.
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
        if node["id"] == "http_exam_scoring":
            node["data"] = {
                "type": "http-request",
                "title": "Score Exam (n8n)",
                "url": "http://n8n-academie:5678/webhook/dify-exam-scoring",
                "method": "post",
                "body": {
                    "type": "json",
                    "data": [
                        {
                            "key": "",
                            "type": "text",
                            "value": '{"username": "{{#sys.user_id#}}", "domaine": "anglais", "conversation_id": "{{#sys.conversation_id#}}", "niveau": "{{#code_turn_check.niveau#}}", "concept_keys": "{{#code_profil_check.concept_keys_json#}}"}'
                        }
                    ]
                },
                "headers": "",
                "params": "",
                "timeout": {
                    "max_read_timeout": 90,
                    "max_write_timeout": 0,
                    "max_connect_timeout": 0
                },
                "authorization": {
                    "type": "no-auth",
                    "config": None
                },
                "selected": False,
                "retry_config": {
                    "max_retries": 2,
                    "retry_enabled": True,
                    "retry_interval": 500
                }
            }
            print("  Fixed: http_exam_scoring (correct Dify format)")

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
