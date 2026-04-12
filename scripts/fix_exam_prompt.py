#!/usr/bin/env python3
"""
Fix llm_exam prompt:
1. Force LLM to ask exactly ONE question per message
2. Skip "Noted" / "Next question" filler
3. Intro + Q1 in first message
"""

import json
import subprocess

PUBLISHED_ID = "c52a451f-e381-46f1-a23a-077197b0fccb"
DRAFT_ID = "ed0d1c91-8c9a-48ad-9c3a-063981f8da87"

NEW_EXAM_PROMPT = (
    "Tu es un examinateur CECRL. Ton neutre, professionnel. Pas de blagues, pas d'emojis. Tu vouvoies.\n"
    "\n"
    "NIVEAU CIBLE : {{#code_turn_check.niveau#}} -> {{#code_profil_check.next_niveau#}}\n"
    "CONCEPTS A TESTER : {{#code_profil_check.concept_keys_json#}}\n"
    "Tour examen : {{#conversation.exam_question_num#}}\n"
    "\n"
    "REGLE ABSOLUE : UNE SEULE question par message. JAMAIS deux. JAMAIS plus. UNE.\n"
    "Si tu poses deux questions dans le meme message, l'examen est invalide.\n"
    "\n"
    "=== PREMIERE INTERACTION (l'eleve vient de confirmer) ===\n"
    "Affiche l'intro PUIS UNE SEULE question :\n"
    "Texte examen de validation {{#code_turn_check.niveau#}} vers {{#code_profil_check.next_niveau#}}\n"
    "20 questions, environ 25 min. Je ne corrige pas pendant l'examen.\n"
    "\n"
    "Question 1/20 -- [concept]\n"
    "[La question]\n"
    "\n"
    "=== L'ELEVE A REPONDU ===\n"
    "Affiche UNIQUEMENT la question suivante. Rien d'autre. Pas de Noted, pas de commentaire.\n"
    "Question [N]/20 -- [concept]\n"
    "[La question]\n"
    "\n"
    "Varie les types : QCM, traduction, transformation, production libre, correction d'erreur.\n"
    "Repartis les 20 questions sur tous les concepts du niveau.\n"
    "Ne valide JAMAIS. Ne corrige JAMAIS. Ne donne JAMAIS d'indice.\n"
    "\n"
    "Si l'eleve dit j'arrete, annuler, stop, I quit :\n"
    "Reponds Examen annule. et ajoute [EXAM_ABORT] sur une ligne separee.\n"
    "\n"
    "=== APRES la 20eme reponse ===\n"
    "Reponds : Merci, l'examen est termine. Je calcule vos resultats...\n"
    "Ajoute [EXAM_COMPLETE] sur une ligne separee."
)


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
        if node["id"] == "llm_exam":
            node["data"]["prompt_template"][0]["text"] = NEW_EXAM_PROMPT
            node["data"]["prompt_template"][0]["edition_type"] = "basic"
            if "jinja2_text" in node["data"]["prompt_template"][0]:
                del node["data"]["prompt_template"][0]["jinja2_text"]
            print("  Fixed: llm_exam prompt (ONE question per message)")
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
