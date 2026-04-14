#!/usr/bin/env python3
"""
Met a jour le workflow n8n dify-snapshot pour:
1. Ajouter un noeud SQL "Fetch Student Data" (concept_keys + scores existants)
2. Ameliorer le prompt LLM pour scorer les concepts
3. Parser + merger les scores dans Code2
4. Ecrire scores_confiance dans profils_eleves
"""

import os
import json
import subprocess
from pathlib import Path

def _read_secret(name, fallback=""):
    p = Path(f"/opt/academie-shared/secrets/{name}")
    return p.read_text().strip() if p.exists() else fallback

_DIFY_ADMIN_KEY = os.environ.get("DIFY_ADMIN_KEY") or _read_secret("dify-admin-key")

WORKFLOW_ID = "tVfLg92ijYUvBc94"
VERSION_ID = "fb0f3b42-e2f8-4607-929f-d0ef008e5437"

# ============================================================
# NODES
# ============================================================
nodes = [
    # 1. Webhook (inchange)
    {
        "id": "a6e6f20b-20ae-45c8-a8c3-8a9ed8b2e681",
        "name": "Webhook",
        "type": "n8n-nodes-base.webhook",
        "position": [0, 0],
        "webhookId": "001b173a-8825-4513-94a5-e7c598812cfb",
        "parameters": {
            "path": "dify-snapshot",
            "options": {},
            "httpMethod": "POST",
            "responseMode": "responseNode"
        },
        "typeVersion": 2.1
    },
    # 2. Code (parse body — inchange)
    {
        "id": "1df734d2-d2ef-4e3f-98dd-fdc2def09332",
        "name": "Code in JavaScript",
        "type": "n8n-nodes-base.code",
        "position": [208, 0],
        "parameters": {
            "jsCode": """const body = $input.first().json.body;

return [{
  json: {
    username: body.username,
    domaine: body.domaine,
    conversation_id: body.conversation_id || null,
    contenu: body.contenu || ""
  }
}];"""
        },
        "typeVersion": 2
    },
    # 3. NEW — Fetch Student Data (concept_keys + scores existants)
    {
        "id": "aa11bb22-cc33-dd44-ee55-ff6677889900",
        "name": "Fetch Student Data",
        "type": "n8n-nodes-base.postgres",
        "position": [416, 0],
        "parameters": {
            "operation": "executeQuery",
            "query": """WITH resolve_user AS (
  SELECT COALESCE(
    (SELECT el.username FROM users u JOIN eleves el ON u.eleve_id = el.id WHERE u.dify_user_id = '{{ $json.username }}' LIMIT 1),
    '{{ $json.username }}'
  ) AS resolved_username
),
niveau_map AS (
  SELECT unnest(ARRAY['A1','A2','B1','B2','C1','C2']) as niveau,
         unnest(ARRAY['A2','B1','B2','C1','C2','C2']) as next_niveau
)
SELECT
  p.niveau_global,
  p.scores_confiance,
  c.concept_keys,
  cnext.concept_keys as next_concept_keys
FROM eleves e
LEFT JOIN profils_eleves p ON p.eleve_id = e.id AND p.domaine = '{{ $json.domaine }}'
LEFT JOIN curriculums c ON c.domaine = p.domaine AND c.niveau = p.niveau_global
LEFT JOIN niveau_map nm ON nm.niveau = p.niveau_global
LEFT JOIN curriculums cnext ON cnext.domaine = p.domaine AND cnext.niveau = nm.next_niveau
WHERE e.username = (SELECT resolved_username FROM resolve_user)""",
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
    # 4. Fetch Dify Messages (inchange sauf position)
    {
        "id": "b2c3d4e5-f6a7-48b9-c0d1-e2f3a4b5c6d7",
        "name": "Fetch Dify Messages",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.4,
        "position": [624, 0],
        "parameters": {
            "method": "GET",
            "url": "={{ 'http://dify-api:5001/console/api/apps/39565197-c9d1-4d5b-b66f-18925de236d9/chat-messages?conversation_id=' + $('Code in JavaScript').first().json.conversation_id + '&limit=20' }}",
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
    # 5. Code1 — Build LLM prompt (MODIFIE — inclut concept_keys)
    {
        "id": "71420d77-c0cc-4364-a557-ba5e1ccfa407",
        "name": "Code in JavaScript1",
        "type": "n8n-nodes-base.code",
        "position": [832, 0],
        "parameters": {
            "jsCode": r"""const difyResp = $input.first().json;
const parsed = $('Code in JavaScript').first().json;
const studentData = $('Fetch Student Data').first().json;

const username = parsed.username;
const domaine = parsed.domaine;
const messages = difyResp.data || [];

let contenu = "";
if (messages.length > 0) {
  const exchanges = messages.slice().reverse().map(m => {
    return `Eleve: ${m.query || ""}\nProfesseur: ${(m.answer || "").substring(0, 400)}`;
  });
  contenu = exchanges.join("\n\n");
}
if (!contenu) contenu = `Session ${domaine} de ${username}`;

// Concept keys du niveau de l'eleve
let conceptKeys = [];
try {
  const ck = studentData.concept_keys;
  conceptKeys = typeof ck === 'string' ? JSON.parse(ck) : (ck || []);
} catch(e) { conceptKeys = []; }
const conceptKeysStr = conceptKeys.length > 0 ? conceptKeys.join(', ') : 'aucun';

// Concept keys du niveau suivant (pour mode libre N+1 tracking)
let nextConceptKeys = [];
try {
  const nck = studentData.next_concept_keys;
  nextConceptKeys = typeof nck === 'string' ? JSON.parse(nck) : (nck || []);
} catch(e) { nextConceptKeys = []; }
const nextKeysStr = nextConceptKeys.length > 0 ? nextConceptKeys.join(', ') : '';

// Scores existants pour le merge ulterieur
let existingScores = {};
try {
  const sc = studentData.scores_confiance;
  existingScores = typeof sc === 'string' ? JSON.parse(sc || '{}') : (sc || {});
} catch(e) { existingScores = {}; }

const llmBody = {
  model: "groq-snapshot",
  messages: [
    {
      role: "system",
      content: `Tu es un assistant pedagogique expert. Analyse cette session et reponds UNIQUEMENT avec un objet JSON valide, sans texte avant ni apres.

TACHE 1 — Resume : 3-5 phrases (apprentissages, erreurs, points forts, prochaine priorite).

TACHE 2 — Scoring par concept.
REGLE CRITIQUE : inclus UNIQUEMENT les concepts ou l'eleve a recu AU MOINS 1 exercice et a donne AU MOINS 1 reponse. Si un concept n'a pas ete pratique → NE L'INCLUS PAS dans scores_confiance.
Pour chaque concept pratique :
- Compte le nombre d'exercices ou l'eleve a tente une reponse (attempts)
- Compte le nombre de reponses correctes (correct)
- Calcule score = round(correct / attempts * 100)
Cles autorisees (niveau actuel) : ${conceptKeysStr}
${nextKeysStr ? 'Cles niveau suivant (si pratiquees dans la session) : ' + nextKeysStr : ''}
Si un concept du niveau suivant a ete pratique, inclus-le dans scores_confiance.
Si le concept ne correspond a aucune cle autorisee → ignore-le.

TACHE 3 — Profil : estime niveau_global, points_forts, lacunes, plan_sessions.

TACHE 4 — Patterns d'erreurs recurrentes.
Si l'eleve repete la meme erreur 2+ fois sur un meme concept dans cette session :
- Note-la dans "lacunes" avec le pattern exact (ex: "confond present perfect et past simple avec 'yesterday'")
- Sois specifique, pas generique ("erreurs de present perfect" est trop vague)

Format JSON exact :
{
  "resume": "resume pedagogique 3-5 phrases",
  "niveau_global": "A1|A2|B1|B2|C1|C2",
  "points_forts": "description courte",
  "lacunes": "patterns d'erreurs specifiques detectes (ou vide si aucun)",
  "plan_sessions": "prochaine priorite concrete",
  "scores_confiance": {"concept_key": {"attempts": N, "correct": N, "score": N}}
}
Si aucun concept n'a ete pratique, scores_confiance doit etre un objet vide : {}`
    },
    { role: "user", content: contenu }
  ],
  max_tokens: 800,
  temperature: 0.2
};

return [{ json: { username, domaine, litellm_body: JSON.stringify(llmBody), existing_scores: JSON.stringify(existingScores) } }];"""
        },
        "typeVersion": 2
    },
    # 6. HTTP Request LiteLLM (inchange sauf position)
    {
        "id": "245317c8-8f6d-4323-a97b-d1445a392389",
        "name": "HTTP Request",
        "type": "n8n-nodes-base.httpRequest",
        "position": [1040, 0],
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
    # 7. Code2 — Parse + merge scores (MODIFIE)
    {
        "id": "fd784674-7581-4afb-add9-4f3a85a84547",
        "name": "Code in JavaScript2",
        "type": "n8n-nodes-base.code",
        "position": [1248, 0],
        "parameters": {
            "jsCode": r"""const response = $input.first().json;
const original = $('Code in JavaScript').first().json;
const code1Data = $('Code in JavaScript1').first().json;

const raw = response.choices[0].message.content.trim();

let parsed = {};
try {
  const match = raw.match(/\{[\s\S]*\}/);
  parsed = JSON.parse(match ? match[0] : raw);
} catch(e) {
  parsed = { resume: raw, parse_error: e.message };
}

const resume = parsed.resume || raw;

// === MERGE SCORES_CONFIANCE ===
const today = new Date().toISOString().slice(0, 10);

function getExistingScore(v) {
  if (typeof v === 'number') return v;
  if (typeof v === 'object' && v !== null && v.score !== undefined) return Number(v.score);
  return null;
}

let existingScores = {};
try {
  existingScores = JSON.parse(code1Data.existing_scores || '{}');
} catch(e) { existingScores = {}; }

const newScoresRaw = parsed.scores_confiance || {};
const mergedScores = { ...existingScores };

for (const [concept, data] of Object.entries(newScoresRaw)) {
  let newScore;
  let attempts = 0;
  if (typeof data === 'object' && data !== null && data.score !== undefined) {
    newScore = Number(data.score);
    attempts = Number(data.attempts || 0);
  } else if (typeof data === 'number') {
    newScore = data;
    attempts = data > 0 ? 1 : 0;
  } else {
    continue;
  }
  if (attempts <= 0 && newScore === 0 && !(concept in existingScores)) continue;
  if (isNaN(newScore) || newScore < 0 || newScore > 100) continue;

  const existingEntry = mergedScores[concept];
  const existingScore = getExistingScore(existingEntry);
  const merged = existingScore !== null
    ? Math.round(0.3 * existingScore + 0.7 * newScore)
    : Math.round(newScore);
  // Track days_seen : nombre de jours calendaires differents ou le concept a ete travaille
  let daysSeen = 1;
  let firstSeen = today;
  if (existingEntry && typeof existingEntry === 'object') {
    const prevDays = Number(existingEntry.days_seen || 0);
    const prevLastSeen = existingEntry.last_seen || '';
    firstSeen = existingEntry.first_seen || prevLastSeen || today;
    // Incrementer days_seen seulement si last_seen est un jour different d'aujourd'hui
    if (prevLastSeen && prevLastSeen.substring(0, 10) !== today.substring(0, 10)) {
      daysSeen = prevDays + 1;
    } else {
      daysSeen = Math.max(prevDays, 1);
    }
  }
  // Format enrichi : {score, last_seen, first_seen, days_seen}
  mergedScores[concept] = { score: merged, last_seen: today, first_seen: firstSeen, days_seen: daysSeen };
}

return [{
  json: {
    username: original.username,
    domaine: original.domaine,
    contenu: resume.replace(/'/g, "''"),
    resume_clean: resume,
    niveau_global: parsed.niveau_global || '',
    points_forts: parsed.points_forts || '',
    lacunes: parsed.lacunes || '',
    plan_sessions: parsed.plan_sessions || '',
    scores_confiance: JSON.stringify(mergedScores),
    debug_raw: raw.substring(0, 500)
  }
}];"""
        },
        "typeVersion": 2
    },
    # 8. SQL Insert Snapshot (inchange sauf position)
    {
        "id": "443d5be6-94d4-4430-868a-d3b06b9e7d50",
        "name": "Execute a SQL query",
        "type": "n8n-nodes-base.postgres",
        "position": [1456, -100],
        "parameters": {
            "query": "WITH resolve_user AS (SELECT COALESCE((SELECT el.username FROM users u JOIN eleves el ON u.eleve_id = el.id WHERE u.dify_user_id = '{{ $json.username }}' LIMIT 1), '{{ $json.username }}') AS resolved_username)\nINSERT INTO snapshots_session (eleve_id, domaine, contenu)\n  SELECT e.id, '{{ $json.domaine }}', '{{ $json.contenu }}'\n  FROM eleves e\n  WHERE e.username = (SELECT resolved_username FROM resolve_user)",
            "options": {
                "queryReplacement": "={{ $json.domaine }}, {{ $json.contenu }}, {{ $json.username }}"
            },
            "operation": "executeQuery"
        },
        "credentials": {
            "postgres": {
                "id": "NpF5tjOzvAWkHR2n",
                "name": "Postgres account"
            }
        },
        "typeVersion": 2.6
    },
    # 9. Build Profil Update (MODIFIE — ajoute scores_confiance)
    {
        "id": "c3d4e5f6-a7b8-49c0-d1e2-f3a4b5c6d7e8",
        "name": "Build Profil Update",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1456, 100],
        "parameters": {
            "jsCode": r"""const d = $input.first().json;
const esc = (s) => (s || '').replace(/'/g, "''");
return [{
  json: {
    username:         d.username,
    domaine:          d.domaine,
    niveau_global:    esc(d.niveau_global),
    points_forts:     esc(d.points_forts),
    lacunes:          esc(d.lacunes),
    plan_sessions:    esc(d.plan_sessions),
    resume:           esc(d.resume_clean),
    scores_confiance: d.scores_confiance || '{}'
  }
}];"""
        }
    },
    # 10. SQL Profil Update (MODIFIE — ecrit scores_confiance)
    {
        "id": "f0a1b2c3-d4e5-46f7-a8b9-c0d1e2f3a4b5",
        "name": "SQL Profil Update",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2.6,
        "position": [1664, 100],
        "parameters": {
            "operation": "executeQuery",
            "query": """WITH resolve_user AS (
  SELECT COALESCE(
    (SELECT el.username FROM users u JOIN eleves el ON u.eleve_id = el.id WHERE u.dify_user_id = '{{ $json.username }}' LIMIT 1),
    '{{ $json.username }}'
  ) AS resolved_username
)
INSERT INTO profils_eleves (
    eleve_id, domaine, niveau_global, points_forts, lacunes, plan_sessions,
    scores_confiance, derniere_session, updated_at
  )
  SELECT e.id, '{{ $json.domaine }}',
    NULLIF('{{ $json.niveau_global }}', ''),
    NULLIF('{{ $json.points_forts }}', ''),
    NULLIF('{{ $json.lacunes }}', ''),
    NULLIF('{{ $json.plan_sessions }}', ''),
    '{{ $json.scores_confiance }}'::jsonb,
    NOW(), NOW()
  FROM eleves e WHERE e.username = (SELECT resolved_username FROM resolve_user)
  ON CONFLICT (eleve_id, domaine) DO UPDATE SET
    -- niveau_global is NEVER overwritten by snapshot — only diagnostic and exams change it
    points_forts     = COALESCE(NULLIF(EXCLUDED.points_forts,''),     profils_eleves.points_forts),
    lacunes          = COALESCE(NULLIF(EXCLUDED.lacunes,''),          profils_eleves.lacunes),
    plan_sessions    = COALESCE(NULLIF(EXCLUDED.plan_sessions,''),    profils_eleves.plan_sessions),
    scores_confiance = '{{ $json.scores_confiance }}'::jsonb,
    derniere_session = NOW(), updated_at = NOW()""",
            "options": {}
        },
        "credentials": {
            "postgres": {
                "id": "NpF5tjOzvAWkHR2n",
                "name": "Postgres account"
            }
        }
    },
    # 11. Respond to Webhook (inchange sauf position)
    {
        "id": "e5f6a7b8-c9d0-41e2-f3a4-b5c6d7e8f9a0",
        "name": "Respond to Webhook",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.1,
        "position": [1872, 100],
        "parameters": {
            "respondWith": "allIncomingItems"
        }
    }
]

# ============================================================
# CONNECTIONS
# ============================================================
connections = {
    "Webhook": {
        "main": [[{"node": "Code in JavaScript", "type": "main", "index": 0}]]
    },
    "Code in JavaScript": {
        "main": [[{"node": "Fetch Student Data", "type": "main", "index": 0}]]
    },
    "Fetch Student Data": {
        "main": [[{"node": "Fetch Dify Messages", "type": "main", "index": 0}]]
    },
    "Fetch Dify Messages": {
        "main": [[{"node": "Code in JavaScript1", "type": "main", "index": 0}]]
    },
    "Code in JavaScript1": {
        "main": [[{"node": "HTTP Request", "type": "main", "index": 0}]]
    },
    "HTTP Request": {
        "main": [[{"node": "Code in JavaScript2", "type": "main", "index": 0}]]
    },
    "Code in JavaScript2": {
        "main": [[
            {"node": "Execute a SQL query", "type": "main", "index": 0},
            {"node": "Build Profil Update", "type": "main", "index": 0}
        ]]
    },
    "Build Profil Update": {
        "main": [[
            {"node": "SQL Profil Update", "type": "main", "index": 0},
            {"node": "Respond to Webhook", "type": "main", "index": 0}
        ]]
    },
    "SQL Profil Update": {
        "main": [[]]
    }
}

# ============================================================
# BUILD & APPLY
# ============================================================
nodes_json = json.dumps(nodes, ensure_ascii=False)
connections_json = json.dumps(connections, ensure_ascii=False)

# Escape for SQL
nodes_sql = nodes_json.replace("'", "''")
connections_sql = connections_json.replace("'", "''")

# Update workflow_entity
sql1 = f"""UPDATE workflow_entity
SET nodes = '{nodes_sql}'::json,
    connections = '{connections_sql}'::json,
    "updatedAt" = NOW()
WHERE id = '{WORKFLOW_ID}';"""

# Update workflow_history (activeVersionId)
sql2 = f"""UPDATE workflow_history
SET nodes = '{nodes_sql}'::json,
    connections = '{connections_sql}'::json,
    "updatedAt" = NOW()
WHERE "versionId" = '{VERSION_ID}';"""

# Execute
for i, sql in enumerate([sql1, sql2], 1):
    result = subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db"],
        input=sql, capture_output=True, text=True
    )
    table = "workflow_entity" if i == 1 else "workflow_history"
    if result.returncode == 0:
        print(f"[OK] {table} updated: {result.stdout.strip()}")
    else:
        print(f"[ERR] {table}: {result.stderr.strip()}")

print("\nDone. Restart n8n: docker restart n8n-academie")
