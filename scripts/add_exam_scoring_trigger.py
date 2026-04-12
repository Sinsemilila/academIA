#!/usr/bin/env python3
"""
Wire exam scoring into the chatflow:
1. Add if_exam_complete after code_exam_track
2. Add http_exam_scoring to call n8n webhook
3. Add code_exam_bilan to format results
4. Rewire: code_exam_track -> if_exam_complete -> (complete) http_exam_scoring -> code_exam_bilan -> answer_exam
                                                -> (not complete) answer_exam (normal question)
"""

import json
import subprocess
import uuid

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

    # Check if nodes already exist
    existing_ids = {n["id"] for n in nodes}
    if "if_exam_complete" in existing_ids:
        print("  Already exists: if_exam_complete — skipping")
        return graph

    # Find position of code_exam_track for positioning
    track_x, track_y = 1800, 400
    for n in nodes:
        if n["id"] == "code_exam_track":
            pos = n.get("position", {})
            track_x = pos.get("x", 1800)
            track_y = pos.get("y", 400)

    # === 1. if_exam_complete node ===
    if_exam_complete = {
        "id": "if_exam_complete",
        "data": {
            "type": "if-else",
            "title": "Examen termine ?",
            "cases": [{
                "id": "exam_done",
                "case_id": "exam_done",
                "conditions": [{
                    "value": "true",
                    "varType": "boolean",
                    "variable_selector": ["code_exam_track", "exam_complete"],
                    "comparison_operator": "is"
                }],
                "logical_operator": "and"
            }],
            "selected": False
        },
        "position": {"x": track_x + 250, "y": track_y}
    }
    nodes.append(if_exam_complete)
    print("  Added: if_exam_complete")

    # === 2. http_exam_scoring node ===
    http_exam_scoring = {
        "id": "http_exam_scoring",
        "data": {
            "type": "http-request",
            "title": "Score Exam (n8n)",
            "method": "post",
            "url": "http://n8n-academie:5678/webhook/dify-exam-scoring",
            "headers": "Content-Type: application/json",
            "body": json.dumps({
                "username": "{{#sys.user_id#}}",
                "domaine": "anglais",
                "conversation_id": "{{#sys.conversation_id#}}",
                "niveau": "{{#code_turn_check.niveau#}}",
                "concept_keys": "{{#code_profil_check.concept_keys_json#}}"
            }),
            "timeout": "90",
            "selected": False
        },
        "position": {"x": track_x + 500, "y": track_y - 100}
    }
    nodes.append(http_exam_scoring)
    print("  Added: http_exam_scoring")

    # === 3. code_exam_bilan node ===
    bilan_code = """import json

def main(body: str, exam_text: str) -> dict:
    # Parse scoring response from n8n
    try:
        result = json.loads(body or '{}')
    except:
        result = {}

    passed = result.get('passed', False)
    score = result.get('total_score', 0)
    niveau = result.get('niveau', '?')
    commentaire = result.get('commentaire', '')

    if passed:
        next_level = {'A1':'A2','A2':'B1','B1':'B2','B2':'C1','C1':'C2'}.get(niveau, '?')
        bilan = (
            "\\n\\n--- RESULTATS ---\\n"
            f"Score : {score}/100 - REUSSI !\\n"
            f"Vous passez en {next_level}. Felicitations !\\n"
        )
        if commentaire:
            bilan += f"\\n{commentaire}"
    else:
        bilan = (
            "\\n\\n--- RESULTATS ---\\n"
            f"Score : {score}/100 - Pas encore.\\n"
            f"Il faut minimum 70/100 pour valider.\\n"
        )
        if commentaire:
            bilan += f"\\n{commentaire}"
        bilan += "\\nContinuons a travailler ensemble !"

    # Combine exam completion text + bilan
    full_text = (exam_text or "Examen termine.") + bilan
    return {"bilan_text": full_text}
"""
    code_exam_bilan = {
        "id": "code_exam_bilan",
        "data": {
            "type": "code",
            "title": "Format Bilan",
            "code": bilan_code,
            "code_language": "python3",
            "outputs": {
                "bilan_text": {"type": "string", "children": None}
            },
            "variables": [
                {"variable": "body", "value_selector": ["http_exam_scoring", "body"]},
                {"variable": "exam_text", "value_selector": ["code_exam_track", "cleaned_text"]}
            ],
            "selected": False
        },
        "position": {"x": track_x + 750, "y": track_y - 100}
    }
    nodes.append(code_exam_bilan)
    print("  Added: code_exam_bilan")

    # === 4. answer_exam_bilan node ===
    answer_exam_bilan = {
        "id": "answer_exam_bilan",
        "data": {
            "type": "answer",
            "title": "Bilan examen",
            "answer": "{{#code_exam_bilan.bilan_text#}}",
            "selected": False
        },
        "position": {"x": track_x + 1000, "y": track_y - 100}
    }
    nodes.append(answer_exam_bilan)
    print("  Added: answer_exam_bilan")

    # === 5. Rewire edges ===
    new_edges = []
    for e in edges:
        src = e.get("source", "")
        tgt = e.get("target", "")

        # Remove direct code_exam_track -> answer_exam
        if src == "code_exam_track" and tgt == "answer_exam":
            print(f"  Removed edge: {src} -> {tgt}")
            continue

        new_edges.append(e)

    # Add new edges
    new_edges.extend([
        # code_exam_track -> if_exam_complete
        {
            "id": "edge-track-to-ifcomplete",
            "source": "code_exam_track",
            "target": "if_exam_complete",
            "type": "custom",
            "data": {"sourceType": "code", "targetType": "if-else"}
        },
        # if_exam_complete (true) -> http_exam_scoring
        {
            "id": "edge-ifcomplete-to-scoring",
            "source": "if_exam_complete",
            "target": "http_exam_scoring",
            "sourceHandle": "exam_done",
            "type": "custom",
            "data": {"sourceType": "if-else", "targetType": "http-request"}
        },
        # if_exam_complete (false) -> answer_exam (normal question continues)
        {
            "id": "edge-ifcomplete-to-answer",
            "source": "if_exam_complete",
            "target": "answer_exam",
            "sourceHandle": "false",
            "type": "custom",
            "data": {"sourceType": "if-else", "targetType": "answer"}
        },
        # http_exam_scoring -> code_exam_bilan
        {
            "id": "edge-scoring-to-bilan",
            "source": "http_exam_scoring",
            "target": "code_exam_bilan",
            "type": "custom",
            "data": {"sourceType": "http-request", "targetType": "code"}
        },
        # code_exam_bilan -> answer_exam_bilan
        {
            "id": "edge-bilan-to-answerbilan",
            "source": "code_exam_bilan",
            "target": "answer_exam_bilan",
            "type": "custom",
            "data": {"sourceType": "code", "targetType": "answer"}
        },
    ])

    graph["edges"] = new_edges
    print(f"  Total edges: {len(new_edges)}")

    return graph


for wf_id, label in [(PUBLISHED_ID, "published"), (DRAFT_ID, "draft")]:
    print(f"\n=== Adding exam scoring trigger to {label} ({wf_id}) ===")
    try:
        graph = load_graph(wf_id)
        graph = patch_graph(graph)
        save_graph(wf_id, graph)
    except Exception as e:
        print(f"  [ERR] {e}")
        import traceback
        traceback.print_exc()

print("\nDone. docker restart dify-api dify-worker")
