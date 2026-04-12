#!/usr/bin/env python3
"""
Corrige code_check pour bloquer le snapshot pendant l'onboarding.
Ajoute profil_present comme variable d'entrée : si False, do_snapshot = False.
"""

import json
import subprocess

PUBLISHED_ID = "c52a451f-e381-46f1-a23a-077197b0fccb"
DRAFT_ID = "ed0d1c91-8c9a-48ad-9c3a-063981f8da87"

NEW_CODE = """def main(nb: int, profil_present: bool) -> dict:
    n = int(nb or 0) + 1
    # Ne pas faire de snapshot pendant l'onboarding (pas de profil = nouvel eleve)
    do_snap = n % 10 == 0 and bool(profil_present)
    return {"new_count": n, "do_snapshot": do_snap}
"""


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
        if node["id"] == "code_check":
            node["data"]["code"] = NEW_CODE
            node["data"]["variables"] = [
                {"variable": "nb", "value_selector": ["conversation", "nb_interactions"]},
                {"variable": "profil_present", "value_selector": ["code_profil_check", "profil_present"]}
            ]
            print("  Patched: code_check — blocks snapshot during onboarding")

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

print("\nDone. Restart Dify: docker restart dify-api dify-worker")
