#!/usr/bin/env python3
"""
Creates the n8n dify-exam-scoring workflow.
Flow:
  Webhook → Parse → Get Conversation → Build Scoring Prompt → LLM Score → Parse Results → SQL Update → Respond

Uses same credential patterns as dify-diagnostic (no credential store, headers inline).
"""

import os
import json
import subprocess
import uuid
from datetime import datetime

POSTGRES_CRED_ID = "NpF5tjOzvAWkHR2n"
def _read_secret(name, fallback=""):
    from pathlib import Path
    p = Path(f"/opt/academie-shared/secrets/{name}")
    return p.read_text().strip() if p.exists() else fallback

DIFY_ADMIN_KEY = os.environ.get("DIFY_ADMIN_KEY", _read_secret("dify-admin-key"))
WORKSPACE_ID = "4c3e17be-144c-4e7a-968e-478d6c48fb2f"
TEACHER_APP_ID = "39565197-c9d1-4d5b-b66f-18925de236d9"


def run_sql(sql):
    result = subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db"],
        input=sql, capture_output=True, text=True
    )
    return result


# ============================================================
# NODES
# ============================================================

webhook_id = str(uuid.uuid4())

nodes = [
    {
        "id": str(uuid.uuid4()),
        "name": "Webhook",
        "type": "n8n-nodes-base.webhook",
        "typeVersion": 2,
        "position": [0, 0],
        "webhookId": webhook_id,
        "parameters": {
            "path": "dify-exam-scoring",
            "httpMethod": "POST",
            "responseMode": "responseNode",
            "options": {}
        }
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Parse Body",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [250, 0],
        "parameters": {
            "jsCode": """const body = $input.first().json.body || $input.first().json;
const username = body.username || '';
const domaine = body.domaine || 'anglais';
const conversation_id = body.conversation_id || '';
const exam_responses = body.exam_responses || '[]';
const niveau = body.niveau || 'B1';
const concept_keys = body.concept_keys || '[]';
const module_index = body.module_index || 0;
const module_total = body.module_total || 1;
const module_name = body.module_name || '';
const module_concepts = body.module_concepts || '';

return [{
  json: {
    username,
    domaine,
    conversation_id,
    exam_responses,
    niveau,
    concept_keys,
    module_index,
    module_total,
    module_name,
    module_concepts
  }
}];"""
        }
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Fetch Exam Messages",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [500, 0],
        "parameters": {
            "method": "GET",
            "url": f"={{{{ 'http://dify-api:5001/console/api/apps/{TEACHER_APP_ID}/chat-messages?conversation_id=' + $json.conversation_id + '&limit=50' }}}}",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {"name": "Authorization", "value": f"Bearer {DIFY_ADMIN_KEY}"},
                    {"name": "X-WORKSPACE-ID", "value": WORKSPACE_ID}
                ]
            },
            "options": {"timeout": 15000}
        }
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Build Scoring Prompt",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [750, 0],
        "parameters": {
            "jsCode": r"""const parsed = $('Parse Body').first().json;
const difyResp = $input.first().json;
const messages = difyResp.data || [];

// Build transcript with exam questions and student answers
// Messages are returned by Dify in CHRONOLOGICAL order (oldest first) — do NOT reverse
let examTranscript = "";
let inExam = false;
const exchanges = messages.slice();

for (const m of exchanges) {
  const answer = m.answer || "";
  const query = m.query || "";

  // Detect start of exam module (intro message or Question 1)
  if (answer.includes("Examen de validation") || answer.includes("Question 1/") ||
      answer.includes("DEBUT DE L'EXAMEN") || answer.includes("Module :")) {
    inExam = true;
  }

  if (inExam) {
    if (query) examTranscript += `ELEVE: ${query}\n`;
    if (answer) examTranscript += `EXAMINATEUR: ${answer}\n\n`;
  }
}

if (!examTranscript) {
  examTranscript = "Transcript examen non disponible. Reponses brutes :\n" + parsed.exam_responses;
}

const moduleName = parsed.module_name || 'Examen';
const moduleConcepts = parsed.module_concepts || '';

const llmBody = {
  model: "mistral-small",
  messages: [
    {
      role: "system",
      content: `Tu es un correcteur CECRL professionnel et juste.

Niveau examine : ${parsed.niveau}
Module : ${moduleName}
Concepts et poids du module : ${moduleConcepts}

Analyse le transcript d'examen ci-dessous. Pour chaque question posee par l'examinateur :
1. Identifie le concept teste (utilise la cle EXACTE du concept, ex: present_perfect_simple)
2. Evalue la reponse de l'eleve (correcte/partielle/incorrecte)
3. Pour les questions situationnelles testant 2-3 concepts, attribue un score a chaque concept teste

NOTATION :
- Correct = 1 point
- Partiellement correct (bonne idee, erreur mineure) = 0.5 point
- Incorrect = 0 point
- REGLE : sois juste mais strict. Une erreur sur le point grammatical teste = 0.
- Ignore les messages hors-sujet (I'm ready, Next please, etc.)

Pour chaque concept, compte le total de questions qui le testaient (y compris les questions croisees).

Reponds UNIQUEMENT avec ce JSON :
{
  "total_score": 75,
  "passed": true,
  "concept_scores": {
    "present_perfect_simple": {"correct": 3, "total": 5, "score": 60},
    "passive_voice": {"correct": 2, "total": 4, "score": 50}
  },
  "commentaire": "Bref commentaire en francais (points forts + lacunes identifiees)"
}

REGLES JSON :
- total_score = moyenne ponderee des scores par concept (0-100)
- passed = true si total_score >= 70
- concept_scores.X.score = (correct / total) * 100 arrondi
- Pas de texte avant ni apres le JSON.`
    },
    {
      role: "user",
      content: `TRANSCRIPT EXAMEN :\n\n${examTranscript}`
    }
  ],
  temperature: 0.1,
  max_tokens: 2000
};

return [{ json: { llmBody, username: parsed.username, domaine: parsed.domaine, niveau: parsed.niveau, concept_keys: parsed.concept_keys } }];"""
        }
    },
    {
        "id": str(uuid.uuid4()),
        "name": "LLM Score",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [1000, 0],
        "parameters": {
            "method": "POST",
            "url": "http://litellm-proxy:4000/v1/chat/completions",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {"name": "Content-Type", "value": "application/json"}
                ]
            },
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify($json.llmBody) }}",
            "options": {"timeout": 60000}
        }
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Parse Results",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1250, 0],
        "parameters": {
            "jsCode": r"""const prev = $('Build Scoring Prompt').first().json;
const llmResp = $input.first().json;

let rawText = "";
try {
  rawText = llmResp.choices[0].message.content || "";
} catch (e) {
  rawText = "";
}

// Extract JSON from response
let jsonStr = rawText.trim();
const jsonMatch = rawText.match(/```(?:json)?\s*([\s\S]*?)```/);
if (jsonMatch) jsonStr = jsonMatch[1].trim();

// Also handle case where there's text before/after JSON
const braceMatch = jsonStr.match(/\{[\s\S]*\}/);
if (braceMatch) jsonStr = braceMatch[0];

let result;
try {
  result = JSON.parse(jsonStr);
} catch (e) {
  result = {
    total_score: 0, passed: false,
    concept_scores: {},
    commentaire: "Erreur analyse: " + e.message
  };
}

return [{
  json: {
    username: prev.username,
    domaine: prev.domaine,
    niveau: prev.niveau,
    concept_keys: prev.concept_keys,
    module_index: prev.module_index || 0,
    module_total: prev.module_total || 1,
    total_score: result.total_score || 0,
    passed: result.passed === true,
    concept_scores: result.concept_scores || {},
    commentaire: result.commentaire || "",
    scored_at: new Date().toISOString()
  }
}];"""
        }
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Build SQL",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1500, 0],
        "parameters": {
            "jsCode": r"""const r = $input.first().json;

// Escape for SQL
const esc = (s) => (s || '').replace(/'/g, "''");

const isLastModule = (r.module_index + 1) >= r.module_total;
const shouldPromote = r.passed && isLastModule;

// Concept scores + to_review (weak concepts to consolidate next session)
const conceptScores = r.concept_scores || {};
const examKeys = Object.keys(conceptScores);

// Concepts with exam score < 60 — used in dernier_examen for next-session guidance (#5)
const toReview = examKeys.filter(k => {
  const cs = conceptScores[k];
  const s = typeof cs === 'object' ? (cs.score || 0) : cs;
  return s < 60;
});

// dernier_examen JSON (only update on last module or failed)
const dernierExamen = JSON.stringify({
  date: r.scored_at,
  niveau: r.niveau,
  score: r.total_score,
  passed: shouldPromote,
  module_results: r.concept_scores,
  to_review: toReview,
  commentaire: r.commentaire
});

// Merge exam concept scores into scores_confiance (30% old + 70% exam)
let mergeClause = '';
if (examKeys.length > 0 && !shouldPromote) {
  // Build CASE for each scored concept — use concept_scores.X.score
  const cases = examKeys.map(k => {
    const cs = conceptScores[k];
    const v = typeof cs === 'object' ? (cs.score || 0) : cs;
    return `WHEN key = '${esc(k)}' THEN ROUND(((COALESCE((scores_confiance->>key)::numeric, 50) * 0.3) + (${v} * 0.7)))::int`;
  }).join('\n        ');

  mergeClause = `scores_confiance = (
    SELECT jsonb_object_agg(key,
      CASE
        ${cases}
        ELSE (scores_confiance->>key)::numeric::int
      END
    )
    FROM jsonb_each_text(scores_confiance)
  ),`;
}

// Level up ONLY if ALL modules passed (this is the last module + passed)
let levelUpClause = '';
// SAFEGUARD: anchor current niveau on failure (prevents any drift/regression)
const safeNiveauClause = `niveau_global = '${r.niveau}',`;

if (shouldPromote) {
  const nextLevel = {
    'A1': 'A2', 'A2': 'B1', 'B1': 'B2', 'B2': 'C1', 'C1': 'C2'
  }[r.niveau] || r.niveau;
  levelUpClause = `niveau_global = '${nextLevel}',
  scores_confiance = '{}'::jsonb,
  nb_examens_niveau = 0,`;
  mergeClause = ''; // Reset scores on promotion
} else {
  // Not promoting: keep niveau anchored at current level (no regression possible)
  levelUpClause = safeNiveauClause;
}

const sql = `
UPDATE profils_eleves
SET
  dernier_examen = '${esc(dernierExamen)}'::jsonb,
  ${(!r.passed && isLastModule) ? 'nb_examens_niveau = nb_examens_niveau + 1,' : ''}
  ${mergeClause}
  ${levelUpClause}
  examen_en_cours = NULL,
  derniere_session = NOW()
WHERE eleve_id = (SELECT id FROM eleves WHERE username = '${esc(r.username)}')
  AND domaine = '${esc(r.domaine)}';
`;

return [{ json: { sql, passed: r.passed, totalScore: r.total_score, niveau: r.niveau, username: r.username, domaine: r.domaine, commentaire: r.commentaire, concept_scores: r.concept_scores, shouldPromote } }];"""
        }
    },
    {
        "id": str(uuid.uuid4()),
        "name": "SQL Update Exam",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2.5,
        "position": [1750, 0],
        "parameters": {
            "operation": "executeQuery",
            "query": "={{ $json.sql }}",
            "options": {}
        },
        "credentials": {
            "postgres": {
                "id": POSTGRES_CRED_ID,
                "name": "Postgres account"
            }
        }
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Respond",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.1,
        "position": [2000, 0],
        "parameters": {
            "respondWith": "json",
            "responseBody": """={{ JSON.stringify({
  status: "ok",
  passed: $('Build SQL').first().json.passed,
  total_score: $('Build SQL').first().json.totalScore,
  niveau: $('Build SQL').first().json.niveau,
  commentaire: $('Build SQL').first().json.commentaire,
  concept_scores: $('Build SQL').first().json.concept_scores,
  shouldPromote: $('Build SQL').first().json.shouldPromote
}) }}"""
        }
    }
]

# Connections
connections = {}
for i in range(len(nodes) - 1):
    connections[nodes[i]["name"]] = {
        "main": [[{"node": nodes[i+1]["name"], "type": "main", "index": 0}]]
    }

# ============================================================
# CREATE WORKFLOW
# ============================================================

workflow_id = str(uuid.uuid4())[:16]
version_id = str(uuid.uuid4())

nodes_json = json.dumps(nodes, ensure_ascii=False).replace("'", "''")
connections_json = json.dumps(connections, ensure_ascii=False).replace("'", "''")
now = datetime.now().isoformat()

# Check if workflow already exists
check = subprocess.run(
    ["docker", "exec", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db",
     "-t", "-c", "SELECT id FROM workflow_entity WHERE name='dify-exam-scoring';"],
    capture_output=True, text=True
)
existing_id = check.stdout.strip()

if existing_id:
    workflow_id = existing_id
    print(f"Updating existing workflow: {workflow_id}")
    sql = f"""
    UPDATE workflow_entity SET
      nodes = '{nodes_json}'::json,
      connections = '{connections_json}'::json,
      "updatedAt" = '{now}',
      active = true
    WHERE id = '{workflow_id}';
    """
else:
    print(f"Creating new workflow: {workflow_id}")
    sql = f"""
    INSERT INTO workflow_entity (id, name, active, nodes, connections, settings, "staticData", "createdAt", "updatedAt")
    VALUES (
      '{workflow_id}',
      'dify-exam-scoring',
      true,
      '{nodes_json}'::json,
      '{connections_json}'::json,
      '{{}}'::json,
      NULL,
      '{now}',
      '{now}'
    );
    """

result = run_sql(sql)
if result.returncode == 0:
    print(f"[OK] Workflow entity: {result.stdout.strip()}")
else:
    print(f"[ERR] {result.stderr}")

# Version history
sql_ver = f"""
INSERT INTO workflow_history (
  "versionId", "workflowId", authors, nodes, connections, "createdAt", "updatedAt"
) VALUES (
  '{version_id}',
  '{workflow_id}',
  'Claude',
  '{nodes_json}'::json,
  '{connections_json}'::json,
  '{now}',
  '{now}'
);

UPDATE workflow_entity SET "activeVersionId" = '{version_id}' WHERE id = '{workflow_id}';
"""

result = run_sql(sql_ver)
if result.returncode == 0:
    print(f"[OK] Version: {version_id}")
else:
    print(f"[ERR] {result.stderr}")

print(f"\nWorkflow ID: {workflow_id}")
print(f"Active Version: {version_id}")
print(f"Webhook: POST http://n8n-academie:5678/webhook/dify-exam-scoring")
print("\nRestart: docker restart n8n-academie")
