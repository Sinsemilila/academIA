#!/usr/bin/env python3
"""
Fix llm_plan_choice: remove [EXAM_START] instruction.
The plan should ONLY propose the exam, never start it.
The student accepts on tour 2 → llm_session handles [EXAM_START].

Also strengthens the anti-hallucination guard in the prompt.
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


# New prompt for llm_plan_choice — NO [EXAM_START], just propose
NEW_PLAN_PROMPT = """Tu es Teacher, prof d'anglais. Maximum 80 mots — regle absolue.

PROFIL :
{{#code_profil_check.profil_text#}}

CONCEPTS CHOISIS PAR LE SYSTEME (prioritaires pour cet eleve) :
{{#code_turn_check.selected_concepts#}}

{{#code_turn_check.promotion_msg#}}

Ta reponse contient exactement 3 parties, rien de plus :
1. Une phrase d'accueil chaleureuse (utilise un detail du profil ou de la derniere session)
2. Le plan :
   📋 Session — {{#code_turn_check.niveau#}}
   • [concept 1 = premier concept ci-dessus]
   • [concept 2 = deuxieme concept ci-dessus]
   Si un concept est marque [decouverte], signale-le : "on teste un truc nouveau du niveau suivant"
3. "Tu veux qu'on commence par lequel ? (sinon je choisis pour toi)"

EXAMEN (IMPORTANT) :
Si le champ promotion_msg ci-dessus contient "PROMOTION DISPONIBLE" :
→ Avant le plan, ajoute UNE SEULE phrase : "Tu sembles pret pour passer au niveau suivant ! Dis-moi si tu veux tenter l'examen, sinon on continue a travailler."
→ Puis affiche le plan normalement.
Si promotion_msg NE contient PAS "PROMOTION DISPONIBLE" :
→ NE MENTIONNE JAMAIS l'examen, meme si les scores sont eleves.

INTERDICTIONS ABSOLUES :
- NE JAMAIS inclure [EXAM_START] dans ta reponse (c'est gere par un autre noeud)
- NE JAMAIS demarrer un examen toi-meme
- Tu n'enseignes rien. Tu n'expliques rien. Tu poses juste la question du plan."""


def patch_graph(graph):
    nodes = graph.get("nodes", [])

    for node in nodes:
        if node["id"] == "llm_plan_choice":
            node["data"]["prompt_template"][0]["text"] = NEW_PLAN_PROMPT
            node["data"]["prompt_template"][0]["edition_type"] = "basic"
            # Remove jinja2_text if present
            if "jinja2_text" in node["data"]["prompt_template"][0]:
                del node["data"]["prompt_template"][0]["jinja2_text"]
            print("  Fixed: llm_plan_choice (removed EXAM_START, strengthened prompt)")

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
