#!/usr/bin/env python3
"""
Met a jour le workflow n8n dify-diagnostic (v2) :
- Prompt LLM enrichi : personnalite, CECRL, auto_eval_level, exchange_count
- Parse and Prepare : extrait tous les champs + instrumentation
- SQL Write Profile : ecrit tous les champs, preserve scores_confiance existants
"""

import json
import subprocess

WORKFLOW_ID = "58dd0014770a4c"
VERSION_ID = "99af14ff-9d6a-4011-8530-13609cb5f434"


def read_nodes():
    result = subprocess.run(
        ["docker", "exec", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db",
         "-t", "-c", f"SELECT nodes FROM workflow_entity WHERE id='{WORKFLOW_ID}';"],
        capture_output=True, text=True
    )
    return json.loads(result.stdout.strip())


def read_connections():
    result = subprocess.run(
        ["docker", "exec", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db",
         "-t", "-c", f"SELECT connections FROM workflow_entity WHERE id='{WORKFLOW_ID}';"],
        capture_output=True, text=True
    )
    return json.loads(result.stdout.strip())


NEW_BUILD_PROMPT_CODE = r"""const difyResp = $input.first().json;
const parsed = $('Parse Body').first().json;

const messages = difyResp.data || [];

let transcript = "";
if (messages.length > 0) {
  const exchanges = messages.slice().reverse().map(m => {
    return `Eleve: ${m.query || ""}\nProfesseur: ${(m.answer || "").substring(0, 500)}`;
  });
  transcript = exchanges.join("\n\n");
}

if (!transcript) {
  transcript = "Pas de messages disponibles.";
}

const llmBody = {
  model: "mistral-small",
  messages: [
    {
      role: "system",
      content: `Tu es un expert en evaluation CECRL et en analyse de profils apprenants.

Analyse le transcript ci-dessous d'une conversation entre un professeur d'anglais et un nouvel eleve.
La conversation comporte 2 phases :
- PHASE 1 (debut) : questions de personnalite en francais (prenom, raisons, style de correction, centres d'interet, mode d'apprentissage)
- PHASE 2 (suite) : questions en anglais de difficulte croissante pour evaluer le niveau CECRL

=== TACHE 1 : PERSONNALITE ===
Extrais des premiers echanges (phase 1) :
- prenom : le prenom de l'eleve
- raison : pourquoi il apprend l'anglais (travail/voyage/culture/examen/autre)
- style_correction : comment il veut etre corrige (direct/doux, humour/serieux)
- centres_interet : ses hobbies/passions
- mode_apprentissage : "structure" (veut des examens de validation pour monter de niveau) ou "libre" (progression naturelle sans blocage). Si pas clair → "libre"

=== TACHE 2 : EVALUATION CECRL ===
Pour chaque reponse EN ANGLAIS de l'eleve, evalue :
1. GRAMMAIRE : structures utilisees (correctes et incorrectes)
2. VOCABULAIRE : basique (A1-A2) / intermediaire (B1-B2) / avance (C1-C2)
3. COMPLEXITE : phrases simples / composees / complexes
4. ERREURS : type et frequence

REGLE CRITIQUE pour determiner le niveau :
- Le niveau = le DERNIER palier ou l'eleve est CONFORTABLE (reponses fluides, peu d'erreurs)
- PAS le palier qu'il atteint peniblement avec beaucoup d'erreurs
- En cas de doute, choisir le niveau INFERIEUR
- Ignorer les echanges de personnalite (phase 1), analyser UNIQUEMENT les reponses en anglais (phase 2)

Reponds UNIQUEMENT avec un objet JSON valide :
{
  "personnalite": {
    "prenom": "...",
    "raison": "...",
    "style_correction": "...",
    "centres_interet": "...",
    "mode_apprentissage": "structure|libre"
  },
  "niveau_global": "A1|A2|B1|B2|C1|C2",
  "justification": "Explication en 2-3 phrases",
  "points_forts": "Ce que l'eleve maitrise bien",
  "lacunes": "Les faiblesses identifiees",
  "plan_sessions": "Les 3 priorites pedagogiques",
  "details_par_competence": {
    "grammaire": "A1|A2|B1|B2|C1|C2",
    "vocabulaire": "A1|A2|B1|B2|C1|C2",
    "production": "A1|A2|B1|B2|C1|C2"
  },
  "auto_eval_level": "A1|A2|B1|B2|C1|C2|null",
  "exchange_count": 5
}

=== CHAMP auto_eval_level ===
Si l'eleve a indique son propre niveau en Phase 1 (auto-evaluation, choix parmi des descripteurs), extrais le niveau CECRL correspondant. Si pas d'auto-evaluation explicite, mets null.

=== CHAMP exchange_count ===
Compte le nombre de reponses EN ANGLAIS de l'eleve dans le transcript (phase 2 uniquement). Ne compte PAS les echanges en francais de la phase 1.`
    },
    { role: "user", content: transcript }
  ],
  max_tokens: 1000,
  temperature: 0.1
};

return [{ json: {
  username: parsed.username,
  domaine: parsed.domaine,
  litellm_body: JSON.stringify(llmBody)
} }];"""


NEW_PARSE_CODE = r"""const response = $input.first().json;
const original = $('Parse Body').first().json;

const raw = response.choices[0].message.content.trim();

let parsed = {};
try {
  const match = raw.match(/\{[\s\S]*\}/);
  parsed = JSON.parse(match ? match[0] : raw);
} catch(e) {
  parsed = { niveau_global: "A2", justification: "Erreur de parsing, niveau par defaut", parse_error: e.message };
}

const esc = (v) => String(v || '').replace(/'/g, "''");

// Extraire personnalite
const perso = parsed.personnalite || {};
const personnaliteJson = JSON.stringify({
  prenom: perso.prenom || '',
  raison: perso.raison || '',
  style_correction: perso.style_correction || '',
  centres_interet: perso.centres_interet || ''
}).replace(/'/g, "''");

const mode = (perso.mode_apprentissage === 'structure') ? 'structure' : 'libre';

// Instrumentation
const autoEval = esc(parsed.auto_eval_level || '');
const exchangeCount = parseInt(parsed.exchange_count, 10) || 0;

// details_par_competence as escaped JSON string for SQL
const detailsJson = JSON.stringify(parsed.details_par_competence || {}).replace(/'/g, "''");

return [{
  json: {
    username: original.username,
    domaine: original.domaine,
    niveau_global: esc(parsed.niveau_global || 'A2'),
    justification: esc(parsed.justification || ''),
    points_forts: esc(parsed.points_forts || ''),
    lacunes: esc(parsed.lacunes || ''),
    plan_sessions: esc(parsed.plan_sessions || ''),
    details_json: detailsJson,
    personnalite_json: personnaliteJson,
    mode_apprentissage: mode,
    auto_eval_level: autoEval,
    exchange_count: exchangeCount,
    debug_raw: raw.substring(0, 500)
  }
}];"""


NEW_SQL_QUERY = """WITH resolve_user AS (
    SELECT COALESCE(
      (SELECT el.username FROM users u JOIN eleves el ON u.eleve_id = el.id WHERE u.dify_user_id = '{{ $json.username }}' LIMIT 1),
      '{{ $json.username }}'
    ) AS resolved_username
  )
  INSERT INTO profils_eleves (
    eleve_id, domaine, niveau_global, points_forts, lacunes, plan_sessions,
    scores_confiance, personnalite, mode_apprentissage,
    details_par_competence, diagnostic_justification, onboarding_completed_at,
    auto_eval_level, diagnostic_exchange_count,
    derniere_session, updated_at
  )
  SELECT e.id, '{{ $json.domaine }}',
    '{{ $json.niveau_global }}',
    NULLIF('{{ $json.points_forts }}', ''),
    NULLIF('{{ $json.lacunes }}', ''),
    NULLIF('{{ $json.plan_sessions }}', ''),
    '{}'::jsonb,
    '{{ $json.personnalite_json }}'::jsonb,
    '{{ $json.mode_apprentissage }}',
    '{{ $json.details_json }}'::jsonb,
    NULLIF('{{ $json.justification }}', ''),
    NOW(),
    NULLIF('{{ $json.auto_eval_level }}', ''),
    {{ $json.exchange_count }},
    NOW(), NOW()
  FROM eleves e WHERE e.username = (SELECT resolved_username FROM resolve_user)
  ON CONFLICT (eleve_id, domaine) DO UPDATE SET
    niveau_global              = EXCLUDED.niveau_global,
    points_forts               = COALESCE(NULLIF(EXCLUDED.points_forts,''), profils_eleves.points_forts),
    lacunes                    = COALESCE(NULLIF(EXCLUDED.lacunes,''), profils_eleves.lacunes),
    plan_sessions              = COALESCE(NULLIF(EXCLUDED.plan_sessions,''), profils_eleves.plan_sessions),
    scores_confiance           = COALESCE(profils_eleves.scores_confiance, '{}'::jsonb),
    personnalite               = EXCLUDED.personnalite,
    mode_apprentissage         = EXCLUDED.mode_apprentissage,
    details_par_competence     = EXCLUDED.details_par_competence,
    diagnostic_justification   = EXCLUDED.diagnostic_justification,
    onboarding_completed_at    = COALESCE(profils_eleves.onboarding_completed_at, NOW()),
    auto_eval_level            = EXCLUDED.auto_eval_level,
    diagnostic_exchange_count  = EXCLUDED.diagnostic_exchange_count,
    derniere_session           = NOW(), updated_at = NOW()"""


# ============================================================
# APPLY
# ============================================================
nodes = read_nodes()
connections = read_connections()

for node in nodes:
    if node["name"] == "Build Analysis Prompt":
        node["parameters"]["jsCode"] = NEW_BUILD_PROMPT_CODE
        print("  Fixed: Build Analysis Prompt (personality + mode extraction)")

    if node["name"] == "Parse and Prepare":
        node["parameters"]["jsCode"] = NEW_PARSE_CODE
        print("  Fixed: Parse and Prepare (personality + mode parsing)")

    if node["name"] == "SQL Write Profile":
        node["parameters"]["query"] = NEW_SQL_QUERY
        print("  Fixed: SQL Write Profile (personality + mode columns)")

nodes_json = json.dumps(nodes, ensure_ascii=False)
nodes_sql = nodes_json.replace("'", "''")
connections_json = json.dumps(connections, ensure_ascii=False)
connections_sql = connections_json.replace("'", "''")

for target, vid in [("workflow_entity", WORKFLOW_ID), ("workflow_history", VERSION_ID)]:
    if target == "workflow_entity":
        sql = f"UPDATE workflow_entity SET nodes = '{nodes_sql}'::json, \"updatedAt\" = NOW() WHERE id = '{vid}';"
    else:
        sql = f"UPDATE workflow_history SET nodes = '{nodes_sql}'::json, \"updatedAt\" = NOW() WHERE \"versionId\" = '{vid}';"

    result = subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db"],
        input=sql, capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"  [OK] {target}: {result.stdout.strip()}")
    else:
        print(f"  [ERR] {target}: {result.stderr.strip()}")

print("\nDone. Restart n8n: docker restart n8n-academie")
