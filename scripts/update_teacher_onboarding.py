#!/usr/bin/env python3
"""
Modifie le chatflow Teacher pour le diagnostic CECRL :
1. Nouveau prompt llm_onboarding avec phases personnalite + diagnostic + marqueur [EVAL_READY]
2. Nouveau noeud code_eval_check entre llm_onboarding et answer_onboarding (strip marqueur)
3. Nouveau noeud if_eval_ready (conditionnel)
4. Nouveau noeud http_diagnostic (appel n8n)
5. Rewire les edges
"""

import json
import subprocess

PUBLISHED_ID = "c52a451f-e381-46f1-a23a-077197b0fccb"
DRAFT_ID = "ed0d1c91-8c9a-48ad-9c3a-063981f8da87"

# ============================================================
# NEW ONBOARDING PROMPT
# ============================================================
NEW_ONBOARDING_PROMPT = """Tu es Teacher, prof d'anglais. Maximum 100 mots. UNE question a la fois. Tu tutoies.

Cet eleve est nouveau, tu ne sais rien de lui. Tu vas faire 2 phases dans l'ordre.

=== PHASE 1 — PERSONNALITE (tours 1 a 3) ===
Pose ces questions naturellement, UNE par message :
- Comment tu t'appelles et pourquoi l'anglais ? (travail / voyage / culture / examen)
- Tu preferes etre corrige immediatement ou doucement ? Humour ou serieux ?
- Centres d'interet ?

Quand tu as les reponses → annonce la phase 2 :
"Maintenant je vais evaluer ton niveau CECRL avec quelques questions en anglais. Reponds naturellement, pas de stress !"

=== PHASE 2 — DIAGNOSTIC (tours 4 a 10+) ===
Pose des questions EN ANGLAIS, de difficulte croissante. UNE par message, attends la reponse.

Palier A1-A2 : "Tell me about yourself" / "What do you like to do?"
Palier A2-B1 : "What did you do last weekend?" / "Describe your best friend"
Palier B1    : "What would you do if you won the lottery?"
Palier B1-B2 : "Tell me about a difficult decision you had to make"
Palier B2    : "What are the pros and cons of remote work?"
Palier B2-C1 : "How would the world be different if internet hadn't been invented?"
Palier C1    : "Some argue that AI will replace teachers. Do you agree?"
Palier C1-C2 : "To what extent does language shape thought?"

REGLES DU DIAGNOSTIC :
- Commence au palier A2-B1
- Si l'eleve repond bien → monte d'un palier
- Si l'eleve galere (erreurs frequentes, phrases courtes, melange francais) → STOP, tu as trouve le plafond
- Ne corrige PAS les erreurs pendant le diagnostic (note-les mentalement)
- Pose au MINIMUM 5 questions de niveaux differents
- Si l'eleve divague ou pose des questions → recadre poliment et repose ta question

QUAND TU AS ASSEZ DE DONNEES (minimum 5 questions posees + plafond identifie) :
Dis : "Merci pour tes reponses ! Je suis en train d'analyser ton niveau, un instant..."
Et ajoute le marqueur [EVAL_READY] A LA FIN de ton message (sur une ligne separee).

NE JAMAIS mettre [EVAL_READY] avant d'avoir pose au moins 5 questions en anglais."""


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

    # --- 1. Modify llm_onboarding prompt ---
    for node in nodes:
        data = node.get("data", {})
        if node["id"].startswith("llm_onboardi"):
            data["prompt_template"] = [{
                "id": "onboarding-diagnostic-prompt",
                "role": "system",
                "text": NEW_ONBOARDING_PROMPT,
                "edition_type": "basic"
            }]
            data["prompt_config"] = {"jinja2_variables": []}
            print("  Patched: llm_onboarding prompt")

    # --- 2. Add code_eval_check node ---
    # Find llm_onboarding position for placement
    onb_pos = [0, 0]
    for node in nodes:
        if node["id"].startswith("llm_onboardi"):
            onb_pos = node.get("position", {"x": 0, "y": 0})
            if isinstance(onb_pos, dict):
                onb_pos_x = onb_pos.get("x", 0)
                onb_pos_y = onb_pos.get("y", 0)
            else:
                onb_pos_x, onb_pos_y = 0, 0

    code_eval_node = {
        "id": "code_eval_check",
        "type": "custom",
        "data": {
            "type": "code",
            "title": "Eval Check",
            "code": """def main(text: str) -> dict:
    marker = "[EVAL_READY]"
    eval_ready = marker in text
    cleaned = text.replace(marker, "").strip()
    return {"cleaned_text": cleaned, "eval_ready": eval_ready}
""",
            "code_language": "python3",
            "outputs": {
                "cleaned_text": {"type": "string", "children": None},
                "eval_ready": {"type": "boolean", "children": None}
            },
            "variables": [
                {"variable": "text", "value_selector": ["llm_onboarding", "text"]}
            ],
            "selected": False
        },
        "position": {"x": onb_pos_x + 300, "y": onb_pos_y}
    }
    nodes.append(code_eval_node)
    print("  Added: code_eval_check")

    # --- 3. Add if_eval_ready node ---
    if_eval_node = {
        "id": "if_eval_ready",
        "type": "custom",
        "data": {
            "type": "if-else",
            "title": "Diagnostic ready?",
            "conditions": [{
                "id": "eval-cond-1",
                "comparison_operator": "is",
                "variable_selector": ["code_eval_check", "eval_ready"],
                "value": "true"
            }],
            "selected": False
        },
        "position": {"x": onb_pos_x + 600, "y": onb_pos_y}
    }
    nodes.append(if_eval_node)
    print("  Added: if_eval_ready")

    # --- 4. Add http_diagnostic node ---
    http_diag_node = {
        "id": "http_diagnostic",
        "type": "custom",
        "data": {
            "type": "http-request",
            "title": "Diagnostic CECRL",
            "url": "http://n8n-academie:5678/webhook/dify-diagnostic",
            "method": "post",
            "body": {
                "type": "json",
                "data": [{
                    "key": "",
                    "type": "text",
                    "value": "{\"username\": \"{{#sys.user_id#}}\", \"domaine\": \"anglais\", \"conversation_id\": \"{{#sys.conversation_id#}}\"}"
                }]
            },
            "headers": "",
            "params": "",
            "timeout": {"max_read_timeout": 30, "max_write_timeout": 0, "max_connect_timeout": 0},
            "authorization": {"type": "no-auth", "config": None},
            "selected": False,
            "retry_config": {"max_retries": 2, "retry_enabled": True, "retry_interval": 500}
        },
        "position": {"x": onb_pos_x + 900, "y": onb_pos_y}
    }
    nodes.append(http_diag_node)
    print("  Added: http_diagnostic")

    # --- 5. Modify answer_onboarding to use cleaned_text ---
    for node in nodes:
        data = node.get("data", {})
        if node["id"].startswith("answer_onboa"):
            data["answer"] = "{{#code_eval_check.cleaned_text#}}"
            print("  Patched: answer_onboarding → uses cleaned_text")

    # --- 6. Rewire edges ---
    # Remove old edges from llm_onboarding
    new_edges = []
    for e in edges:
        src = e.get("source", "")
        tgt = e.get("target", "")
        # Keep all edges EXCEPT: llm_onboarding → answer_onboarding
        if src.startswith("llm_onboardi") and tgt.startswith("answer_onboa"):
            continue  # Will rewire through code_eval_check
        new_edges.append(e)

    # Add new edges
    # llm_onboarding → code_eval_check
    new_edges.append({
        "id": "edge-onb-to-eval",
        "source": "llm_onboarding",
        "target": "code_eval_check",
        "sourceHandle": "source"
    })
    # code_eval_check → answer_onboarding
    new_edges.append({
        "id": "edge-eval-to-answer",
        "source": "code_eval_check",
        "target": "answer_onboarding",
        "sourceHandle": "source"
    })
    # code_eval_check → if_eval_ready
    new_edges.append({
        "id": "edge-eval-to-if",
        "source": "code_eval_check",
        "target": "if_eval_ready",
        "sourceHandle": "source"
    })
    # if_eval_ready (true) → http_diagnostic
    new_edges.append({
        "id": "edge-if-to-diag",
        "source": "if_eval_ready",
        "target": "http_diagnostic",
        "sourceHandle": "true"
    })

    graph["edges"] = new_edges
    print(f"  Rewired edges: {len(new_edges)} total")

    return graph


# ============================================================
# APPLY
# ============================================================
for wf_id, label in [(PUBLISHED_ID, "published"), (DRAFT_ID, "draft")]:
    print(f"\n=== Updating {label} ({wf_id}) ===")
    try:
        graph = load_graph(wf_id)
        graph = patch_graph(graph)
        save_graph(wf_id, graph)
    except Exception as e:
        print(f"  [ERR] {e}")
        import traceback
        traceback.print_exc()

print("\nDone. Restart Dify: docker restart dify-api dify-worker")
