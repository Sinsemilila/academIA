#!/usr/bin/env python3
"""
Adds error analysis trigger to the dify-snapshot n8n workflow.
Adds 2 nodes:
1. Code node that builds the request body for /internal/analyze-errors
2. HTTP Request node that calls the FastAPI endpoint (non-blocking)

Connected in parallel with existing SQL operations after Code in JavaScript2.
If the error analysis fails, the snapshot workflow continues normally.
"""

import json
import subprocess

WORKFLOW_ID = "tVfLg92ijYUvBc94"
VERSION_ID = "fb0f3b42-e2f8-4607-929f-d0ef008e5437"

# ── Step 1: Read current workflow from DB ──
read_sql = f"""SELECT nodes::text, connections::text FROM workflow_entity WHERE id = '{WORKFLOW_ID}';"""
result = subprocess.run(
    ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db", "-t", "-A", "-F", "|||"],
    input=read_sql, capture_output=True, text=True
)
if result.returncode != 0:
    print(f"[ERR] Failed to read workflow: {result.stderr}")
    exit(1)

parts = result.stdout.strip().split("|||")
nodes = json.loads(parts[0])
connections = json.loads(parts[1])

print(f"[OK] Read workflow: {len(nodes)} nodes, {len(connections)} connections")

# ── Step 2: Add new nodes ──

# Node: Build Error Analysis Body
build_error_body_node = {
    "id": "ea-build-body-001",
    "name": "Build Error Analysis Body",
    "type": "n8n-nodes-base.code",
    "position": [1456, 300],
    "parameters": {
        "jsCode": r"""// Build transcript from Dify messages for error analysis
const difyResp = $('Fetch Dify Messages').first().json;
const parsed = $('Code in JavaScript').first().json;
const messages = difyResp.data || [];

// Build transcript in the format the FastAPI endpoint expects
let transcript = "";
if (messages.length > 0) {
  const exchanges = messages.slice().reverse();
  exchanges.forEach((m, i) => {
    const turn = i + 1;
    transcript += `--- Turn ${turn} ---\n`;
    transcript += `USER: ${m.query || ""}\n`;
    transcript += `TEACHER: ${(m.answer || "").substring(0, 300)}\n\n`;
  });
}

return [{
  json: {
    username: parsed.username,
    domaine: parsed.domaine,
    session_id: parsed.conversation_id || "unknown",
    transcript: transcript
  }
}];"""
    },
    "typeVersion": 2
}

# Node: Call Error Analysis Endpoint
call_error_analysis_node = {
    "id": "ea-http-call-001",
    "name": "Trigger Error Analysis",
    "type": "n8n-nodes-base.httpRequest",
    "typeVersion": 4.4,
    "position": [1664, 300],
    "parameters": {
        "method": "POST",
        "url": "http://academie-api:8000/internal/analyze-errors",
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": '={{ JSON.stringify($json) }}',
        "sendHeaders": True,
        "headerParameters": {
            "parameters": [
                {"name": "Content-Type", "value": "application/json"},
                {"name": "X-Internal-Token", "value": "REDACTED_INTERNAL_API_TOKEN"}
            ]
        },
        "options": {
            "timeout": 120000,
            "redirect": {"redirect": {"maxRedirects": 0}}
        }
    },
    "continueOnFail": True  # CRITICAL: don't break snapshot if analysis fails
}

nodes.append(build_error_body_node)
nodes.append(call_error_analysis_node)

print(f"[OK] Added 2 nodes (total: {len(nodes)})")

# ── Step 3: Update connections ──
# Add the new branch from Code in JavaScript2 (fork point)
# Current: Code in JavaScript2 → [Execute a SQL query, Build Profil Update]
# New: Code in JavaScript2 → [Execute a SQL query, Build Profil Update, Build Error Analysis Body]

fork_node = "Code in JavaScript2"
if fork_node in connections:
    main_outputs = connections[fork_node]["main"][0]
    main_outputs.append({
        "node": "Build Error Analysis Body",
        "type": "main",
        "index": 0
    })

# Add: Build Error Analysis Body → Trigger Error Analysis
connections["Build Error Analysis Body"] = {
    "main": [[{
        "node": "Trigger Error Analysis",
        "type": "main",
        "index": 0
    }]]
}

# Trigger Error Analysis has no downstream — it's a fire-and-forget
connections["Trigger Error Analysis"] = {
    "main": [[]]
}

print(f"[OK] Updated connections (total: {len(connections)})")

# ── Step 4: Write back to DB ──
nodes_json = json.dumps(nodes, ensure_ascii=False)
connections_json = json.dumps(connections, ensure_ascii=False)

nodes_sql = nodes_json.replace("'", "''")
connections_sql = connections_json.replace("'", "''")

sql1 = f"""UPDATE workflow_entity
SET nodes = '{nodes_sql}'::json,
    connections = '{connections_sql}'::json,
    "updatedAt" = NOW()
WHERE id = '{WORKFLOW_ID}';"""

sql2 = f"""UPDATE workflow_history
SET nodes = '{nodes_sql}'::json,
    connections = '{connections_sql}'::json,
    "updatedAt" = NOW()
WHERE "versionId" = '{VERSION_ID}';"""

for i, sql in enumerate([sql1, sql2], 1):
    r = subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db"],
        input=sql, capture_output=True, text=True
    )
    table = "workflow_entity" if i == 1 else "workflow_history"
    if r.returncode == 0:
        print(f"[OK] {table} updated: {r.stdout.strip()}")
    else:
        print(f"[ERR] {table}: {r.stderr.strip()}")

print("\n✅ Error analysis trigger added to snapshot workflow.")
print("Restart n8n: docker restart n8n-academie")
