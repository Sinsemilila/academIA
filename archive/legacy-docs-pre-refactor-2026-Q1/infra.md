---
summary: "Docker stack, nginx, Cloudflare Zero Trust, PostgreSQL, LiteLLM gateway"
read_when: "Modifying infrastructure, Docker, networking, reverse proxy, DB connection, or LLM routing"
---

# Infrastructure — AcademIA

## Network topology

```
Cloudflare Zero Trust (Bypass + require WARP + France)
    ↓
192.168.1.181:8080 (nginx) — security headers + cache static
    ├── academie.petit-pont.com → localhost:3001 (SvelteKit)
    ├── dify.petit-pont.com     → localhost:3000 (Dify web)
    └── n8n.petit-pont.com      → localhost:5678 (n8n)
```

## Proxmox / VM

NAS with Proxmox → VM Debian "cosmos" (VMID 100).
- 2 SSDs: boot (119G) + storage (932G)
- cosmos boot disk: 50G on SSD-STOCKAGE
- cosmos data disk: 850G on SSD-STOCKAGE → /mnt/cosmos-data/
- 12 GB RAM allocated
- Proxmox UI: pve.petit-pont.com

## Docker stack (all on academie-net-bridge)

| Container | Port | Role |
|-----------|------|------|
| academie-frontend | 3001 | SvelteKit webapp |
| academie-api | 8000 | FastAPI backend |
| dify-web | 3000 | Dify admin UI |
| dify-api | 5001 | Dify backend |
| dify-worker | — | Celery async tasks |
| dify-plugin-daemon | — | Plugin system |
| dify-sandbox | — | Jinja2 code execution |
| litellm-proxy | 4000 | LLM gateway |
| postgres-academie | 5432 (172.16.0.25) | Main DB |
| redis-academie | — | Cache + broker |
| n8n-academie | 5678 | Workflow orchestrator |
| cosmos-server | — | Reverse proxy |

## PostgreSQL

- Host: 172.16.0.25 (from host) / postgres-academie (from Docker)
- Port: 5432, DB: academie_db, User: sinse
- Data stored: /mnt/cosmos-data/postgres/ (bind mount, 850G disk)
- Tables: eleves, profils_eleves, snapshots_session, historique_sessions + webapp tables

## LiteLLM

Config: /opt/litellm/config.yaml

| Model | Provider | Free? | CJK | Use case |
|-------|----------|-------|-----|----------|
| groq-standard | Groq (Llama 3.3 70B) | Yes | No | Sessions |
| groq-snapshot | Groq (Llama 3.1 8B) | Yes | No | Snapshots |
| groq-qwen | Groq (Qwen 32B) | Yes | Yes | Japanese/CJK |
| gpt-4o-mini | OpenAI | Paid | Yes | Exams |
| mistral-small | Mistral | Yes | Yes | Fallback |

## Secrets

All in /opt/academie-shared/secrets/ (chmod 600):
- dify-admin-key, n8n-encryption-key, restic-passphrase
- Symlinked from original locations for backward compatibility

## Backups

| Level | What | Where | Frequency |
|-------|------|-------|-----------|
| 1 | Vzdump VM | Proxmox local (SSD1) | Daily 4h |
| 2 | PG dump | /mnt/cosmos-data/backups/postgres/ | Hourly |
| 3 | Restic encrypted | Google Drive 5TB | Daily 3h30 |
| 4 | Git | GitHub | Per commit |
