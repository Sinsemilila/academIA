---
summary: "AI-powered language learning platform — self-hosted on Proxmox/Docker"
read_when: "Every session start"
---

# AcademIA

Self-hosted learning platform. SvelteKit frontend + FastAPI backend + Dify chatflows + n8n orchestration + LiteLLM gateway. Running on Proxmox VM (cosmos).

## Quick refs

| What | Where |
|------|-------|
| Webapp code | /opt/academia/webapp/ |
| FastAPI backend | /opt/academia/webapp/backend/ |
| Scripts | /opt/academia/scripts/ |
| Dify compose | /opt/dify/ |
| LiteLLM config | /opt/litellm/config.yaml |
| n8n data | /opt/n8n/ |
| PG data | /mnt/cosmos-data/postgres/ |
| Secrets | /opt/academia-shared/secrets/ |
| Backups PG | /mnt/cosmos-data/backups/postgres/ |
| Backup scripts | /opt/academia-shared/scripts/ |

## Docs (read selectively)

Run `docs-list` for summaries + read_when triggers. Or browse:

| Doc | Content |
|-----|---------|
| docs/infra.md | Docker stack, nginx, Cloudflare, PG, LiteLLM |
| docs/dify-teacher.md | Dify agents, Teacher v17 chatflow |
| docs/n8n-workflows.md | 5 workflows, memory system |
| docs/webapp.md | FastAPI + SvelteKit + users |
| docs/pedagogy.md | TTT approach, taxonomies A1→C2 |
| docs/gotchas.md | Known issues, traps, workarounds |

## Users (6 active)

sinse (id=1, admin), nico (id=2), julien (id=3), noz_project (id=4), waigosan (id=5), 0tha (id=6)

## DB access

PG: host postgres-academie (Docker network), port 5432, db academie_db, user sinse.
PG password: stored on server only — ask Sinse or check `/opt/academia-shared/secrets/`
Dify admin key: `cat /opt/academia-shared/secrets/dify-admin-key`

## LLM routing

| Use case | Model | Provider |
|----------|-------|----------|
| Sessions normales | groq-standard (Llama 3.3 70B) | Groq free |
| Snapshots | groq-snapshot (Llama 3.1 8B) | Groq free |
| Japonais/CJK | groq-qwen (Qwen 32B) | Groq free |
| Examens | gpt-4o-mini | OpenAI paid |
| Fallback | mistral-small | Mistral free |

## Domains

academia.petit-pont.com (webapp), dify.petit-pont.com (Dify admin), n8n.petit-pont.com (n8n)
All via Cloudflare Zero Trust (Bypass + WARP + France).

## Current phase

Phases 1-4 complete. Phase 7 in progress (n8n deployed, weekly reports TODO).
Refactor workflow v1.0 in progress (S1 done, S2 executing).
