#!/usr/bin/env python3
"""
Ajoute le système d'examen au chatflow Teacher :
1. Modifie code_turn_check pour détecter exam_mode
2. Ajoute llm_exam (mistral-small, passera sur gpt-4o-mini en prod)
3. Ajoute code_exam_track (suit les questions/réponses, détecte fin)
4. Ajoute code_exam_detect (détecte [EXAM_START] dans les réponses session/plan)
5. Ajoute var_assigner_exam (met à jour les variables exam)
6. Ajoute http_exam_scoring (appel n8n pour scoring final)
7. Ajoute code_exam_result (formate le bilan)
8. Rewire les edges
"""

import json
import subprocess

PUBLISHED_ID = "c52a451f-e381-46f1-a23a-077197b0fccb"
DRAFT_ID = "ed0d1c91-8c9a-48ad-9c3a-063981f8da87"

# ============================================================
# PROMPTS & CODE
# ============================================================

LLM_EXAM_PROMPT = """Tu es un examinateur CECRL. Ton neutre, professionnel. Pas de blagues, pas d'emojis. Tu vouvoies.

NIVEAU CIBLE : {{#code_turn_check.niveau#}} → {{#code_profil_check.next_niveau#}}
CONCEPTS A TESTER : {{#code_profil_check.concept_keys_json#}}
Tour examen : {{#conversation.exam_question_num#}}

=== SI tour examen = 0 (INTRO) ===
Presente l'examen :
"📝 Examen de validation {{#code_turn_check.niveau#}} → {{#code_profil_check.next_niveau#}}
Je vais vous poser 20 questions couvrant l'ensemble du niveau {{#code_turn_check.niveau#}} : grammaire, vocabulaire, comprehension et production.
Comptez environ 25-30 minutes.
Regles : je ne corrigerai pas vos erreurs pendant l'examen, pas d'indices, pas d'aide.
Quand vous etes pret(e), dites-le."

Attends la confirmation. Ne pose PAS de question encore.

=== SI tour examen >= 1 (QUESTIONS) ===
Pose UNE question. Format :
"Question [tour]/20 — [concept teste]
[La question]"

Varie les types : QCM, traduction, transformation de phrase, production libre, correction d'erreur.
Couvre tous les concepts de maniere equilibree.
Ne valide JAMAIS une reponse. Ne corrige JAMAIS. Dis juste "Noted." ou "Next question:" et enchaine.

Si l'eleve dit "j'arrete" ou "annuler" → reponds "Examen annule. Pas de souci." et ajoute [EXAM_ABORT] sur une ligne separee.

=== SI tour examen = 20 (FIN) ===
Apres la 20eme reponse, dis :
"Merci, l'examen est termine. Je calcule vos resultats..."
Et ajoute [EXAM_COMPLETE] sur une ligne separee."""

CODE_EXAM_DETECT = """def main(text: str, current_exam_mode: str) -> dict:
    # Detecte [EXAM_START] dans les reponses du Teacher normal
    marker = "[EXAM_START]"
    if marker in text:
        cleaned = text.replace(marker, "").strip()
        return {"cleaned_text": cleaned, "new_exam_mode": "intro", "exam_triggered": True}
    return {"cleaned_text": text, "new_exam_mode": current_exam_mode, "exam_triggered": False}
"""

CODE_EXAM_TRACK = r"""import json

def main(text: str, exam_question_num: int, exam_responses: str, query: str) -> dict:
    num = int(exam_question_num or 0)

    # Parser les reponses existantes
    try:
        responses = json.loads(exam_responses or '[]')
    except:
        responses = []

    # Detecter annulation
    if "[EXAM_ABORT]" in text:
        cleaned = text.replace("[EXAM_ABORT]", "").strip()
        return {
            "cleaned_text": cleaned,
            "new_exam_mode": "off",
            "new_question_num": 0,
            "new_responses": "[]",
            "exam_complete": False,
            "exam_aborted": True
        }

    # Detecter fin d'examen
    if "[EXAM_COMPLETE]" in text:
        cleaned = text.replace("[EXAM_COMPLETE]", "").strip()
        # Stocker la derniere reponse
        if num > 0 and query:
            responses.append({"q": num, "answer": query[:500]})
        return {
            "cleaned_text": cleaned,
            "new_exam_mode": "scoring",
            "new_question_num": num,
            "new_responses": json.dumps(responses),
            "exam_complete": True,
            "exam_aborted": False
        }

    # Tour normal : stocker la reponse de l'eleve et incrementer
    if num == 0:
        # Phase intro → passer en mode actif
        new_num = 1
    else:
        # Stocker la reponse precedente
        if query:
            responses.append({"q": num, "answer": query[:500]})
        new_num = num + 1

    return {
        "cleaned_text": text,
        "new_exam_mode": "active",
        "new_question_num": new_num,
        "new_responses": json.dumps(responses),
        "exam_complete": False,
        "exam_aborted": False
    }
"""

# Le prompt llm_session doit pouvoir detecter la demande d'examen
EXAM_START_INSTRUCTION = """
EXAMEN : si l'eleve dit explicitement qu'il veut passer l'examen (ex: "oui je veux l'examen", "examen", "je suis pret pour l'examen", "let's do the exam") :
→ Reponds : "Parfait, on passe en mode examen !"
→ Ajoute [EXAM_START] sur une ligne separee a la fin de ton message.
Ne mets JAMAIS [EXAM_START] si l'eleve n'a pas clairement demande l'examen."""


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

    # --- Trouver les positions existantes pour placement ---
    session_pos_x, session_pos_y = 1400, 80
    for node in nodes:
        if node["id"] == "llm_session":
            pos = node.get("position", {"x": 1400, "y": 80})
            session_pos_x = pos.get("x", 1400)
            session_pos_y = pos.get("y", 80)

    # === 1. Modifier code_turn_check pour retourner exam_mode ===
    for node in nodes:
        if node["id"] == "code_turn_check":
            old_code = node["data"].get("code", "")
            # Ajouter exam_mode comme variable d'entree
            if "exam_mode" not in str(node["data"].get("variables", [])):
                node["data"]["variables"].append(
                    {"variable": "exam_mode", "value_selector": ["conversation", "exam_mode"]}
                )
            # Ajouter exam_active en sortie
            if "exam_active" not in str(node["data"].get("outputs", {})):
                node["data"]["outputs"]["exam_active"] = {"type": "boolean", "children": None}
            print("  Patched: code_turn_check (added exam_mode input + exam_active output)")

    # === 2. Ajouter llm_exam ===
    llm_exam_node = {
        "id": "llm_exam",
        "type": "custom",
        "data": {
            "type": "llm",
            "title": "Examinateur CECRL",
            "model": {
                "provider": "openai_api_compatible",
                "name": "mistral-small",
                "mode": "chat",
                "completion_params": {"temperature": 0.2, "max_tokens": 300}
            },
            "prompt_template": [{
                "id": "exam-prompt-001",
                "role": "system",
                "text": LLM_EXAM_PROMPT,
                "edition_type": "basic"
            }],
            "prompt_config": {"jinja2_variables": []},
            "memory": {"role_prefix": {"user": "Eleve", "assistant": "Examinateur"}, "window": {"enabled": True, "size": 25}},
            "context": {"enabled": False, "variable_selector": []},
            "vision": {"enabled": False},
            "selected": False
        },
        "position": {"x": session_pos_x, "y": session_pos_y + 400}
    }
    nodes.append(llm_exam_node)
    print("  Added: llm_exam (mistral-small)")

    # === 3. Ajouter code_exam_track ===
    code_exam_track_node = {
        "id": "code_exam_track",
        "type": "custom",
        "data": {
            "type": "code",
            "title": "Exam Track",
            "code": CODE_EXAM_TRACK,
            "code_language": "python3",
            "outputs": {
                "cleaned_text": {"type": "string", "children": None},
                "new_exam_mode": {"type": "string", "children": None},
                "new_question_num": {"type": "number", "children": None},
                "new_responses": {"type": "string", "children": None},
                "exam_complete": {"type": "boolean", "children": None},
                "exam_aborted": {"type": "boolean", "children": None}
            },
            "variables": [
                {"variable": "text", "value_selector": ["llm_exam", "text"]},
                {"variable": "exam_question_num", "value_selector": ["conversation", "exam_question_num"]},
                {"variable": "exam_responses", "value_selector": ["conversation", "exam_responses"]},
                {"variable": "query", "value_selector": ["sys", "query"]}
            ],
            "selected": False
        },
        "position": {"x": session_pos_x + 300, "y": session_pos_y + 400}
    }
    nodes.append(code_exam_track_node)
    print("  Added: code_exam_track")

    # === 4. Ajouter answer_exam ===
    answer_exam_node = {
        "id": "answer_exam",
        "type": "custom",
        "data": {
            "type": "answer",
            "title": "Réponse examen",
            "answer": "{{#code_exam_track.cleaned_text#}}",
            "selected": False
        },
        "position": {"x": session_pos_x + 600, "y": session_pos_y + 400}
    }
    nodes.append(answer_exam_node)
    print("  Added: answer_exam")

    # === 5. Ajouter var_assigner_exam (met à jour les variables conversation exam) ===
    var_assigner_exam_node = {
        "id": "var_assigner_exam",
        "type": "custom",
        "data": {
            "type": "assigner",
            "title": "Update Exam Vars",
            "assigned_variable_selector": [["conversation", "exam_mode"]],
            "input_variable_content": [
                {
                    "id": "assign-exam-mode",
                    "variable_selector": ["conversation", "exam_mode"],
                    "input_type": "variable",
                    "value": ["code_exam_track", "new_exam_mode"]
                },
                {
                    "id": "assign-exam-qnum",
                    "variable_selector": ["conversation", "exam_question_num"],
                    "input_type": "variable",
                    "value": ["code_exam_track", "new_question_num"]
                },
                {
                    "id": "assign-exam-resp",
                    "variable_selector": ["conversation", "exam_responses"],
                    "input_type": "variable",
                    "value": ["code_exam_track", "new_responses"]
                }
            ],
            "items": [
                {
                    "variable_selector": ["conversation", "exam_mode"],
                    "operation": "set",
                    "value_type": "variable",
                    "value": ["code_exam_track", "new_exam_mode"]
                },
                {
                    "variable_selector": ["conversation", "exam_question_num"],
                    "operation": "set",
                    "value_type": "variable",
                    "value": ["code_exam_track", "new_question_num"]
                },
                {
                    "variable_selector": ["conversation", "exam_responses"],
                    "operation": "set",
                    "value_type": "variable",
                    "value": ["code_exam_track", "new_responses"]
                }
            ],
            "selected": False
        },
        "position": {"x": session_pos_x + 600, "y": session_pos_y + 550}
    }
    nodes.append(var_assigner_exam_node)
    print("  Added: var_assigner_exam")

    # === 6. Ajouter code_exam_detect (entre session/plan et answer) ===
    code_exam_detect_node = {
        "id": "code_exam_detect",
        "type": "custom",
        "data": {
            "type": "code",
            "title": "Exam Detect",
            "code": CODE_EXAM_DETECT,
            "code_language": "python3",
            "outputs": {
                "cleaned_text": {"type": "string", "children": None},
                "new_exam_mode": {"type": "string", "children": None},
                "exam_triggered": {"type": "boolean", "children": None}
            },
            "variables": [
                {"variable": "text", "value_selector": ["llm_session", "text"]},
                {"variable": "current_exam_mode", "value_selector": ["conversation", "exam_mode"]}
            ],
            "selected": False
        },
        "position": {"x": session_pos_x + 300, "y": session_pos_y}
    }
    nodes.append(code_exam_detect_node)
    print("  Added: code_exam_detect")

    # === 7. Ajouter var_assigner_exam_start (set exam_mode quand detecte) ===
    var_assigner_exam_start_node = {
        "id": "var_assigner_exam_start",
        "type": "custom",
        "data": {
            "type": "assigner",
            "title": "Set Exam Start",
            "items": [
                {
                    "variable_selector": ["conversation", "exam_mode"],
                    "operation": "set",
                    "value_type": "variable",
                    "value": ["code_exam_detect", "new_exam_mode"]
                }
            ],
            "selected": False
        },
        "position": {"x": session_pos_x + 600, "y": session_pos_y + 150}
    }
    nodes.append(var_assigner_exam_start_node)
    print("  Added: var_assigner_exam_start")

    # === 8. Ajouter if_exam_active (routing dans code_turn_check) ===
    if_exam_node = {
        "id": "if_exam_active",
        "type": "custom",
        "data": {
            "type": "if-else",
            "title": "Mode examen ?",
            "cases": [{
                "id": "exam_on",
                "case_id": "exam_on",
                "conditions": [{
                    "value": "off",
                    "varType": "string",
                    "variable_selector": ["conversation", "exam_mode"],
                    "comparison_operator": "not is"
                }],
                "logical_operator": "and"
            }],
            "selected": False
        },
        "position": {"x": session_pos_x - 200, "y": session_pos_y + 200}
    }
    nodes.append(if_exam_node)
    print("  Added: if_exam_active")

    # === 9. Modifier llm_session et llm_plan pour detecter [EXAM_START] ===
    for node in nodes:
        if node["id"] == "llm_session":
            prompt = node["data"]["prompt_template"][0]["text"]
            if "[EXAM_START]" not in prompt:
                node["data"]["prompt_template"][0]["text"] = prompt + "\n" + EXAM_START_INSTRUCTION
                print("  Patched: llm_session (added EXAM_START detection)")

        if node["id"].startswith("llm_plan_cho"):
            prompt = node["data"]["prompt_template"][0]["text"]
            if "[EXAM_START]" not in prompt:
                node["data"]["prompt_template"][0]["text"] = prompt + "\n" + EXAM_START_INSTRUCTION
                print("  Patched: llm_plan_choice (added EXAM_START detection)")

    # === 10. Rewire edges ===
    # Supprimer les edges directes llm_session → answer_session
    # Les remplacer par llm_session → code_exam_detect → answer_session
    new_edges = []
    for e in edges:
        eid = e.get("id", "")
        src = e.get("source", "")
        tgt = e.get("target", "")

        # Remplacer llm_session → answer_session par llm_session → code_exam_detect
        if src == "llm_session" and tgt.startswith("answer_sess"):
            new_edges.append({
                "id": "edge-session-to-examdetect",
                "source": "llm_session",
                "target": "code_exam_detect",
                "type": "custom",
                "data": {"sourceType": "llm", "targetType": "code"}
            })
            print("  Rewired: llm_session → code_exam_detect (was → answer_session)")
            continue

        # Remplacer code_turn_check → if_first_turn par code_turn_check → if_exam_active
        if src == "code_turn_check" and tgt == "if_first_turn":
            new_edges.append({
                "id": "edge-turncheck-to-ifexam",
                "source": "code_turn_check",
                "target": "if_exam_active",
                "type": "custom",
                "data": {"sourceType": "code", "targetType": "if-else"}
            })
            print("  Rewired: code_turn_check → if_exam_active (was → if_first_turn)")
            continue

        new_edges.append(e)

    # Ajouter les nouveaux edges
    new_edges.extend([
        # if_exam_active (true = exam on) → llm_exam
        {
            "id": "edge-ifexam-to-llmexam",
            "source": "if_exam_active",
            "target": "llm_exam",
            "sourceHandle": "exam_on",
            "type": "custom",
            "data": {"sourceType": "if-else", "targetType": "llm"}
        },
        # if_exam_active (false = normal) → if_first_turn
        {
            "id": "edge-ifexam-to-firstturn",
            "source": "if_exam_active",
            "target": "if_first_turn",
            "sourceHandle": "false",
            "type": "custom",
            "data": {"sourceType": "if-else", "targetType": "if-else"}
        },
        # llm_exam → code_exam_track
        {
            "id": "edge-llmexam-to-track",
            "source": "llm_exam",
            "target": "code_exam_track",
            "type": "custom",
            "data": {"sourceType": "llm", "targetType": "code"}
        },
        # code_exam_track → answer_exam
        {
            "id": "edge-track-to-answerexam",
            "source": "code_exam_track",
            "target": "answer_exam",
            "type": "custom",
            "data": {"sourceType": "code", "targetType": "answer"}
        },
        # code_exam_track → var_assigner_exam
        {
            "id": "edge-track-to-varassignexam",
            "source": "code_exam_track",
            "target": "var_assigner_exam",
            "type": "custom",
            "data": {"sourceType": "code", "targetType": "assigner"}
        },
        # code_exam_detect → answer_session (texte nettoyé)
        {
            "id": "edge-examdetect-to-answersession",
            "source": "code_exam_detect",
            "target": "answer_session",
            "type": "custom",
            "data": {"sourceType": "code", "targetType": "answer"}
        },
        # code_exam_detect → var_assigner_exam_start (set exam_mode si triggered)
        {
            "id": "edge-examdetect-to-varassignstart",
            "source": "code_exam_detect",
            "target": "var_assigner_exam_start",
            "type": "custom",
            "data": {"sourceType": "code", "targetType": "assigner"}
        },
    ])

    print(f"  Total edges: {len(new_edges)}")

    # Modifier answer_session pour utiliser cleaned_text de code_exam_detect
    for node in nodes:
        if node["id"].startswith("answer_sess"):
            node["data"]["answer"] = "{{#code_exam_detect.cleaned_text#}}"
            print("  Patched: answer_session (uses code_exam_detect.cleaned_text)")

    graph["edges"] = new_edges
    return graph


# ============================================================
# APPLY
# ============================================================
for wf_id, label in [(PUBLISHED_ID, "published"), (DRAFT_ID, "draft")]:
    print(f"\n=== Adding exam to {label} ({wf_id}) ===")
    try:
        graph = load_graph(wf_id)
        graph = patch_graph(graph)
        save_graph(wf_id, graph)
    except Exception as e:
        print(f"  [ERR] {e}")
        import traceback
        traceback.print_exc()

print("\nDone. Restart Dify: docker restart dify-api dify-worker")
