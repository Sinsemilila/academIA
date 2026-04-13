#!/usr/bin/env python3
"""
Cree le workflow n8n dify-diagnostic :
Analyse CECRL d'un transcript de conversation pour determiner le niveau d'un nouvel eleve.
Appele depuis Dify quand llm_onboarding signale [EVAL_READY].
"""

import os
import json
from pathlib import Path

def _read_secret(name, fallback=""):
    p = Path(f"/opt/academie-shared/secrets/{name}")
    return p.read_text().strip() if p.exists() else fallback

_DIFY_ADMIN_KEY = os.environ.get("DIFY_ADMIN_KEY") or _read_secret("dify-admin-key")
import subprocess
import uuid

WORKFLOW_NAME = "dify-diagnostic"

nodes = [
    # 1. Webhook
    {
        "id": str(uuid.uuid4()),
        "name": "Webhook",
        "type": "n8n-nodes-base.webhook",
        "position": [0, 0],
        "webhookId": str(uuid.uuid4()),
        "parameters": {
            "path": "dify-diagnostic",
            "options": {},
            "httpMethod": "POST",
            "responseMode": "responseNode"
        },
        "typeVersion": 2.1
    },
    # 2. Parse body
    {
        "id": str(uuid.uuid4()),
        "name": "Parse Body",
        "type": "n8n-nodes-base.code",
        "position": [208, 0],
        "parameters": {
            "jsCode": """const body = $input.first().json.body;
return [{
  json: {
    username: body.username,
    domaine: body.domaine,
    conversation_id: body.conversation_id || ""
  }
}];"""
        },
        "typeVersion": 2
    },
    # 3. Fetch Dify Messages
    {
        "id": str(uuid.uuid4()),
        "name": "Fetch Dify Messages",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.4,
        "position": [416, 0],
        "parameters": {
            "method": "GET",
            "url": "={{ 'http://dify-api:5001/console/api/apps/39565197-c9d1-4d5b-b66f-18925de236d9/chat-messages?conversation_id=' + $json.conversation_id + '&limit=30' }}",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {"name": "Authorization", "value": f"Bearer {_DIFY_ADMIN_KEY}"},
                    {"name": "X-WORKSPACE-ID", "value": "4c3e17be-144c-4e7a-968e-478d6c48fb2f"}
                ]
            },
            "options": {}
        }
    },
    # 4. Build CECRL analysis prompt
    {
        "id": str(uuid.uuid4()),
        "name": "Build Analysis Prompt",
        "type": "n8n-nodes-base.code",
        "position": [624, 0],
        "parameters": {
            "jsCode": r"""const difyResp = $input.first().json;
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
      content: `Tu es un expert en evaluation CECRL (Cadre Europeen Commun de Reference pour les Langues).

Analyse le transcript ci-dessous d'une conversation entre un professeur d'anglais et un nouvel eleve. Le professeur a pose des questions de difficulte croissante pour evaluer le niveau.

Pour chaque reponse de l'eleve, evalue :
1. GRAMMAIRE : structures utilisees (correctes et incorrectes)
2. VOCABULAIRE : basique (A1-A2) / intermediaire (B1-B2) / avance (C1-C2)
3. COMPLEXITE : phrases simples / composees / complexes
4. ERREURS : type et frequence

REGLE CRITIQUE pour determiner le niveau :
- Le niveau = le DERNIER palier ou l'eleve est CONFORTABLE (reponses fluides, peu d'erreurs)
- PAS le palier qu'il atteint peniblement avec beaucoup d'erreurs
- En cas de doute, choisir le niveau INFERIEUR (mieux vaut sous-estimer que surestimer)
- Ignorer les questions de personnalite (debut de conversation), analyser uniquement les reponses en anglais

Reponds UNIQUEMENT avec un objet JSON valide :
{
  "niveau_global": "A1|A2|B1|B2|C1|C2",
  "justification": "Explication en 2-3 phrases de pourquoi ce niveau",
  "points_forts": "Ce que l'eleve maitrise bien",
  "lacunes": "Les faiblesses identifiees",
  "plan_sessions": "Les 3 priorites pedagogiques pour progresser",
  "details_par_competence": {
    "grammaire": "A1|A2|B1|B2|C1|C2",
    "vocabulaire": "A1|A2|B1|B2|C1|C2",
    "production": "A1|A2|B1|B2|C1|C2"
  }
}`
    },
    { role: "user", content: transcript }
  ],
  max_tokens: 800,
  temperature: 0.1
};

return [{ json: {
  username: parsed.username,
  domaine: parsed.domaine,
  litellm_body: JSON.stringify(llmBody)
} }];"""
        },
        "typeVersion": 2
    },
    # 5. HTTP LiteLLM
    {
        "id": str(uuid.uuid4()),
        "name": "HTTP Request",
        "type": "n8n-nodes-base.httpRequest",
        "position": [832, 0],
        "parameters": {
            "url": "http://litellm-proxy:4000/v1/chat/completions",
            "method": "POST",
            "options": {},
            "jsonBody": "={{ $json.litellm_body }}",
            "sendBody": True,
            "sendHeaders": True,
            "specifyBody": "json",
            "headerParameters": {
                "parameters": [
                    {"name": "Content-Type", "value": "application/json"}
                ]
            }
        },
        "typeVersion": 4.4
    },
    # 6. Parse + Write to DB
    {
        "id": str(uuid.uuid4()),
        "name": "Parse and Prepare",
        "type": "n8n-nodes-base.code",
        "position": [1040, 0],
        "parameters": {
            "jsCode": r"""const response = $input.first().json;
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

return [{
  json: {
    username: original.username,
    domaine: original.domaine,
    niveau_global: esc(parsed.niveau_global || 'A2'),
    justification: esc(parsed.justification || ''),
    points_forts: esc(parsed.points_forts || ''),
    lacunes: esc(parsed.lacunes || ''),
    plan_sessions: esc(parsed.plan_sessions || ''),
    details: JSON.stringify(parsed.details_par_competence || {}),
    debug_raw: raw.substring(0, 500)
  }
}];"""
        },
        "typeVersion": 2
    },
    # 7. SQL Write Profile
    {
        "id": str(uuid.uuid4()),
        "name": "SQL Write Profile",
        "type": "n8n-nodes-base.postgres",
        "position": [1248, 0],
        "parameters": {
            "operation": "executeQuery",
            "query": """INSERT INTO profils_eleves (
    eleve_id, domaine, niveau_global, points_forts, lacunes, plan_sessions,
    scores_confiance, derniere_session, updated_at
  )
  SELECT e.id, '{{ $json.domaine }}',
    '{{ $json.niveau_global }}',
    NULLIF('{{ $json.points_forts }}', ''),
    NULLIF('{{ $json.lacunes }}', ''),
    NULLIF('{{ $json.plan_sessions }}', ''),
    '{}'::jsonb,
    NOW(), NOW()
  FROM eleves e WHERE e.username = '{{ $json.username }}'
  ON CONFLICT (eleve_id, domaine) DO UPDATE SET
    niveau_global    = EXCLUDED.niveau_global,
    points_forts     = COALESCE(NULLIF(EXCLUDED.points_forts,''), profils_eleves.points_forts),
    lacunes          = COALESCE(NULLIF(EXCLUDED.lacunes,''), profils_eleves.lacunes),
    plan_sessions    = COALESCE(NULLIF(EXCLUDED.plan_sessions,''), profils_eleves.plan_sessions),
    scores_confiance = '{}'::jsonb,
    derniere_session = NOW(), updated_at = NOW()""",
            "options": {}
        },
        "credentials": {
            "postgres": {
                "id": "NpF5tjOzvAWkHR2n",
                "name": "Postgres account"
            }
        },
        "typeVersion": 2.6
    },
    # 8. Respond
    {
        "id": str(uuid.uuid4()),
        "name": "Respond to Webhook",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.1,
        "position": [1456, 0],
        "parameters": {
            "respondWith": "allIncomingItems"
        }
    }
]

connections = {
    "Webhook": {"main": [[{"node": "Parse Body", "type": "main", "index": 0}]]},
    "Parse Body": {"main": [[{"node": "Fetch Dify Messages", "type": "main", "index": 0}]]},
    "Fetch Dify Messages": {"main": [[{"node": "Build Analysis Prompt", "type": "main", "index": 0}]]},
    "Build Analysis Prompt": {"main": [[{"node": "HTTP Request", "type": "main", "index": 0}]]},
    "HTTP Request": {"main": [[{"node": "Parse and Prepare", "type": "main", "index": 0}]]},
    "Parse and Prepare": {"main": [[
        {"node": "SQL Write Profile", "type": "main", "index": 0},
        {"node": "Respond to Webhook", "type": "main", "index": 0}
    ]]},
    "SQL Write Profile": {"main": [[]]}
}

# ============================================================
# CREATE WORKFLOW IN N8N DB
# ============================================================
workflow_id = str(uuid.uuid4())[:16].replace('-','')
version_id = str(uuid.uuid4())

nodes_json = json.dumps(nodes, ensure_ascii=False)
connections_json = json.dumps(connections, ensure_ascii=False)
nodes_sql = nodes_json.replace("'", "''")
connections_sql = connections_json.replace("'", "''")

# Insert workflow_entity
sql1 = f"""INSERT INTO workflow_entity (id, name, active, nodes, connections, "createdAt", "updatedAt", "versionId", "triggerCount", "isArchived", "versionCounter")
VALUES ('{workflow_id}', '{WORKFLOW_NAME}', true,
  '{nodes_sql}'::json, '{connections_sql}'::json,
  NOW(), NOW(), '{version_id}', 0, false, 1
);"""

# Insert workflow_history
sql2 = f"""INSERT INTO workflow_history ("versionId", "workflowId", authors, "createdAt", "updatedAt", nodes, connections, name)
VALUES ('{version_id}', '{workflow_id}', 'claude',
  NOW(), NOW(), '{nodes_sql}'::json, '{connections_sql}'::json, '{WORKFLOW_NAME}'
);"""

for i, sql in enumerate([sql1, sql2], 1):
    result = subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db"],
        input=sql, capture_output=True, text=True
    )
    table = "workflow_entity" if i == 1 else "workflow_history"
    if result.returncode == 0:
        print(f"[OK] {table}: {result.stdout.strip()}")
    else:
        print(f"[ERR] {table}: {result.stderr.strip()}")

print(f"\nWorkflow ID: {workflow_id}")
print(f"Version ID: {version_id}")
print(f"Webhook: POST http://n8n-academie:5678/webhook/dify-diagnostic")
print("\nRestart n8n: docker restart n8n-academie")
