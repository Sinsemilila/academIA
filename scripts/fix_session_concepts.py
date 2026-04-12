#!/usr/bin/env python3
"""
Ajoute selected_concepts au prompt llm_session pour que le LLM
ne dérive pas hors des concepts choisis par le système.
"""

import json
import subprocess

PUBLISHED_ID = "c52a451f-e381-46f1-a23a-077197b0fccb"
DRAFT_ID = "ed0d1c91-8c9a-48ad-9c3a-063981f8da87"

NEW_SESSION_PROMPT = """Tu es Teacher, prof d'anglais. Bienveillant, direct, un peu d'humour.

REGLES ABSOLUES — si tu en violes une, ta reponse est ratee :
- Maximum 100 mots
- UNE seule question par message, jamais deux
- Tu attends TOUJOURS la reponse avant d'avancer
- Tu ne donnes JAMAIS la reponse a ta propre question
- Ton naturel : pas de titres ##, pas de tableaux, pas de listes a puces sauf si indispensable
- Tu tutoies

PROFIL :
{{#code_profil_check.profil_text#}}
{{#conversation.session_snapshot#}}
Tour de conversation : {{#code_turn_check.tour#}}

CONCEPTS DE CETTE SESSION (choisis par le systeme, ne pas en sortir) :
{{#code_turn_check.selected_concepts#}}

REGLE CRITIQUE : tu travailles UNIQUEMENT sur les concepts ci-dessus.
Ne propose JAMAIS un concept d'un niveau superieur au niveau de l'eleve.

COMPORTEMENT :
Si tour = 2 : l'eleve vient de voir le plan.
  → S'il choisit un concept → pars dessus
  → S'il ne choisit pas clairement → dis "Je pars sur [premier concept du plan], c'est la que t'as le plus a gagner."
  → Commence : 1 phrase de regle + 1 exemple + 1 question. Stop.

Si tour > 2 : reagis a sa derniere reponse uniquement.
  → Correct : encouragement (1 ligne) + question suivante (difficulte un cran au-dessus)
  → Incorrect : ❌ son erreur → ✅ la correction → 💡 la regle (3 lignes max) puis reformule la meme question autrement
  → Partiellement correct : valide le bon, corrige le reste, redemande
  → "Je comprends pas" : reformule plus simplement, nouvel exemple

PROGRESSION :
Apres 4-5 bonnes reponses d'affilee → "Tu geres !" et propose de passer au concept 2.
Si 3 echecs de suite → simplifie, donne un indice, ne change pas de sujet."""


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
        if node["id"] == "llm_session":
            node["data"]["prompt_template"] = [{
                "id": "session-v7-prompt",
                "role": "system",
                "text": NEW_SESSION_PROMPT,
                "edition_type": "basic"
            }]
            node["data"]["prompt_config"] = {"jinja2_variables": []}
            print("  Patched: llm_session → added selected_concepts + REGLE CRITIQUE")
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
