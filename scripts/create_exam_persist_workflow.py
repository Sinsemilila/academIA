#!/usr/bin/env python3
"""
Creates the n8n dify-exam-persist workflow.
Saves exam state to DB for resume after disconnection.
Flow: Webhook → Build SQL → SQL Update → Respond

Usage:
  python3 /opt/academie/scripts/create_exam_persist_workflow.py && docker restart n8n-academie
"""

import json
import subprocess
import uuid
from datetime import datetime

POSTGRES_CRED_ID = "NpF5tjOzvAWkHR2n"
WORKFLOW_ID = "ePrsExm8St4t2Svd"
VERSION_ID = "fabfcdd3-c791-4e0a"


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
            "path": "dify-exam-persist",
            "httpMethod": "POST",
            "responseMode": "responseNode",
            "options": {}
        }
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Build SQL",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [250, 0],
        "parameters": {
            "jsCode": r"""const body = $input.first().json.body || $input.first().json;
const username = (body.username || '').replace(/'/g, "''");
const domaine = (body.domaine || 'anglais').replace(/'/g, "''");
const shouldClear = body.clear === true;

let sql;
if (shouldClear) {
  sql = `UPDATE profils_eleves SET examen_en_cours = NULL
         WHERE eleve_id = (SELECT id FROM eleves WHERE username = '${username}')
         AND domaine = '${domaine}';`;
} else {
  const examState = body.exam_state || {};
  const stateJson = JSON.stringify(examState).replace(/'/g, "''");
  sql = `UPDATE profils_eleves SET examen_en_cours = '${stateJson}'::jsonb
         WHERE eleve_id = (SELECT id FROM eleves WHERE username = '${username}')
         AND domaine = '${domaine}';`;
}

return [{ json: { sql, username, domaine, shouldClear } }];"""
        }
    },
    {
        "id": str(uuid.uuid4()),
        "name": "SQL Update",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2.5,
        "position": [500, 0],
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
        "position": [750, 0],
        "parameters": {
            "respondWith": "json",
            "responseBody": '={{ JSON.stringify({ status: "ok" }) }}'
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
# UPDATE WORKFLOW
# ============================================================

nodes_json = json.dumps(nodes, ensure_ascii=False).replace("'", "''")
connections_json = json.dumps(connections, ensure_ascii=False).replace("'", "''")

sql1 = f"""UPDATE workflow_entity
SET nodes = '{nodes_json}'::json,
    connections = '{connections_json}'::json,
    "updatedAt" = NOW(),
    active = true
WHERE id = '{WORKFLOW_ID}';"""

sql2 = f"""INSERT INTO workflow_history ("versionId", "workflowId", authors, nodes, connections, "createdAt", "updatedAt")
VALUES ('{VERSION_ID}', '{WORKFLOW_ID}', 'Claude', '{nodes_json}'::json, '{connections_json}'::json, NOW(), NOW())
ON CONFLICT ("versionId") DO UPDATE SET nodes = '{nodes_json}'::json, connections = '{connections_json}'::json, "updatedAt" = NOW();

UPDATE workflow_entity SET "activeVersionId" = '{VERSION_ID}' WHERE id = '{WORKFLOW_ID}';"""

for i, sql in enumerate([sql1, sql2], 1):
    result = run_sql(sql)
    table = "workflow_entity" if i == 1 else "workflow_history"
    if result.returncode == 0:
        print(f"[OK] {table}: {result.stdout.strip()}")
    else:
        print(f"[ERR] {table}: {result.stderr.strip()}")

print(f"\nWorkflow ID: {WORKFLOW_ID}")
print(f"Webhook: POST http://n8n-academie:5678/webhook/dify-exam-persist")
print("Restart: docker restart n8n-academie")
