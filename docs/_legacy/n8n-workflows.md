---
summary: "n8n workflows, memory system (snapshots + profiles), webhook endpoints"
read_when: "Modifying n8n workflows, memory system, or webhook integrations"
---

# n8n Workflows — AcademIA

Access UI: ssh -L 5678:127.0.0.1:5678 cosmos → http://localhost:5678

## Active workflows

| Workflow | Method | Internal URL | Role |
|----------|--------|-------------|------|
| dify-profil-get | GET | http://n8n-academie:5678/webhook/dify-profil-get?username=X&domaine=Y | Returns profile + last snapshot |
| dify-snapshot | POST | http://n8n-academie:5678/webhook/dify-snapshot | AI session summary → snapshots_session |
| dify-profil-update | POST | http://n8n-academie:5678/webhook/dify-profil-update | Update profils_eleves |

## Memory system (2 levels)

### Level 1 — Session (short term)
Every 10 interactions, groq-snapshot generates a rolling summary.
Each snapshot integrates the previous (coherent chain).
Stored in snapshots_session table.

### Level 2 — Long term (between sessions)
Full pedagogical profile in profils_eleves.
Auto-injected via n8n (dify-profil-get) at Teacher session start.
Updated at session end via dify-profil-update.

## Pipeline

dify-snapshot: Webhook → Code → LiteLLM (groq-snapshot) → Code → Postgres
dify-profil-get: auto-creates student if unknown (ON CONFLICT DO NOTHING)

## Encryption

n8n encryption key: /opt/academie-shared/secrets/n8n-encryption-key
If lost: ALL n8n workflows become unreadable.
