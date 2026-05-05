---
title: Deployment & Infrastructure
status: authoritative
last_reviewed: 2026-04-15
---

# Deployment & Infrastructure

> État production actuel (avril 2026). Servi par cosmos, une VM Debian sur NAS Proxmox.

## Topologie réseau

```
Internet
    │
    ▼
Cloudflare Tunnel (Bypass + require WARP + France)
    │
    ▼
cosmos (192.168.1.181) — nginx sur HOST via systemd, port :8080
    │    (security headers + static cache + CSP complet)
    ├── academia.petit-pont.com  → 127.0.0.1:3001 (SvelteKit via Docker bridge)
    ├── dify.petit-pont.com      → 127.0.0.1:5001/3000 (Dify api+web)
    └── n8n.petit-pont.com       → 127.0.0.1:5678 (n8n)
```

**Important** : **nginx N'EST PAS dans un container**, il tourne sur le host via `systemd nginx.service`. Le container `cosmos-server` est une **UI admin Cosmos Server (privileged)** — différent et indépendant.

**Aucun port ouvert** sur le NAT : tout passe par Cloudflare Tunnel.

## Hôte : Proxmox + VM cosmos

- **NAS** avec Proxmox, 2 SSDs (boot 119G + stockage 932G)
- **VM cosmos** (VMID 100)
  - Debian
  - 12 GB RAM
  - Boot disk : 50 GB sur SSD-STOCKAGE
  - Data disk : 850 GB sur SSD-STOCKAGE → mounted `/mnt/cosmos-data/`
- **Proxmox UI** : pve.petit-pont.com

## Docker stack

### Sur `academie-net-bridge` (172.16.0.0/**27** — 11/30 IPs)

| Container | Image | Port host | Healthcheck | Compose |
|---|---|---|---|---|
| `academie-frontend` | `webapp-academie-frontend:latest` (local build) | 127.0.0.1:3001 | ✅ node fetch | webapp |
| `academie-api` | `webapp-academie-api:latest` (local build) | 127.0.0.1:8000 | ✅ /api/health | webapp |
| `postgres-academie` | `postgres:16` | 127.0.0.1:5432 | — | ad-hoc |
| `redis-academie` | `redis:7-alpine` | 127.0.0.1:6379 | — | ad-hoc |
| `dify-api` | `langgenius/dify-api:latest` (v1.13.3) | 127.0.0.1:5001 | — | ad-hoc |
| `dify-web` | `langgenius/dify-web:latest` | 127.0.0.1:3000 | — | ad-hoc |
| `dify-worker` | `langgenius/dify-api:latest` | internal | — | ad-hoc |
| `dify-sandbox` | `langgenius/dify-sandbox:latest` | internal 8194 | — | ad-hoc |
| `dify-plugin-daemon` | `langgenius/dify-plugin-daemon:0.5.3-local` | internal 5002 | — | ad-hoc |
| `litellm-proxy` | `ghcr.io/berriai/litellm:main-latest` (v1.82.6) | 127.0.0.1:4000 | — | ad-hoc (DNS 8.8.8.8/1.1.1.1) |
| `n8n-academie` | `n8nio/n8n:latest` (v2.14.2) | 127.0.0.1:5678 | — | ad-hoc |

> IPs Docker non listées : assignées dynamiquement depuis 172.16.0.2 (recréation bridge Session 15). Communication inter-container via DNS names, jamais par IP.

### Hors academie-net-bridge

| Container | Image | Network | Rôle |
|---|---|---|---|
| `cosmos-server` | `azukaar/cosmos-server:latest` | **host** + `/` bind-mounté + `docker.sock` + privileged | **UI admin Cosmos Server** (pas nginx — nginx est sur le host) |
| `cosmos-mongo-KIo` | `mongo:8` | bridge default (172.17.0.0/16) | DB MongoDB pour Cosmos Server |

**Seuls 2 containers sont Compose-managés** (`academie-frontend` + `academie-api`, projet `webapp`). Les autres ont été démarrés manuellement via `docker run` ou via Cosmos UI.

Compose files :
- `/opt/academia/webapp/docker-compose.webapp.yml` (frontend + api seulement)
- Aucun autre compose file actif sur le host

### Alertes

- ✅ ~~Subnet /28 saturé~~ — migré en /27 (Session 15, 2026-04-15). 30 IPs, 11 utilisées.
- ✅ ~~Dangling volume 820 MB~~ — supprimé Session 15 (Nextcloud orphelin, pas de data).
- ⚠️ **`cosmos-server` est privileged + host network + `/` bind-mounted + docker.sock accessible** → point d'entrée critique en cas de compromission. À auditer.
- ⚠️ **`dify-api` env var `QDRANT_HOST=qdrant-server`** mais pas de container qdrant → dead pointer (RAG non utilisé, non bloquant).

## PostgreSQL

- **Host** : `postgres-academie` (depuis Docker) ou `127.0.0.1:5432` (depuis host)
- **IP Docker** : `172.16.0.19`
- **Port** : 5432
- **User** : `sinse`
- **Version** : PostgreSQL 16.13 (Debian)
- **Data** : `/mnt/cosmos-data/postgres/` (bind mount, ~305 MB actuellement)
- **DBs** (cf. [data-model.md](../02-architecture/data-model.md)) :
  - `academie_db` (198 MB) — mégabase mix 5 systèmes
  - `litellm_db` (11 MB) — spend logs LiteLLM (Session 12)
  - `dify_plugin` (8.3 MB)
  - `postgres` (7.5 MB, maintenance)
- **Connexions actives** : 27 academie_db + 3 litellm_db + 1 dify_plugin = 31 total

## Redis

- **Version** : 7.4.8-alpine
- **IP Docker** : `172.16.0.22`
- **Port** : `127.0.0.1:6379` sur host
- **Data** : anonymous volume `7f51671da32529…` (~20 KB, rien d'important)
- **Usage** : 38 keys totales, 1.83 MB used
  - db0 (17 keys) : Dify auth (`refresh_token`, `account_refresh_token`), plugin state (`provider_model_credentials`, `plugin_daemon`)
  - db1 (21 keys) : Celery `_kombu.binding.*` pour Dify worker
- **Aucune donnée métier AcademIA** — tout est en PostgreSQL

## LiteLLM

- **Config** : `/opt/litellm/config.yaml`
- **Port** : 4000 (host + interne)
- **DB spend logs** : `litellm_db` (activé Session 12, cf. ADR-006)

### Modèles configurés

| Alias | Provider | Tier | Usage |
|---|---|---|---|
| `gpt-4o-mini` | OpenAI | Free | Primary Teacher chat + onboarding + exam |
| `ft:gpt-4o-mini-v3` | OpenAI | Paid | Error analysis fine-tuned |
| `groq-standard` | Groq (Llama 3.3 70B) | Free | Fallback chat |
| `groq-snapshot` | Groq (Llama 3.1) | Free | Génération snapshots |
| `groq-qwen` | Groq (Qwen 2.5) | Free | Futur JP/ZH |
| `mistral-small` | Mistral | Free | Fallback FR/ES/IT |
| (commented) | — | — | Blocs BYOK à activer (cf. ADR-006) |

### Routing

- `routing_strategy: usage-based-routing-v2` (load-balance sur clés multiples du même modèle)
- `fallbacks` configurés : gpt-4o-mini → groq-standard → mistral-small
- `num_retries: 3`, `cooldown_time: 60s` après rate limit
- `num_fallback` : toutes les clés testées avant abandon

## Webapp FastAPI

- Container : `academie-api`
- Build : `/opt/academia/webapp/backend/Dockerfile`
- Entrypoint : `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Env vars via `.env` :
  - `DATABASE_URL` (pointe sur academie_db)
  - `DIFY_KEY_TEACHER`
  - `JWT_SECRET_KEY`
  - etc.
- Healthcheck : `GET /api/health` toutes les 30s

## SvelteKit frontend

- Container : `academie-frontend`
- Build : `/opt/academia/webapp/frontend/Dockerfile`
- SSR Node adapter
- Env vars : `ORIGIN`, `PROTOCOL_HEADER`, `HOST_HEADER`, `ADDRESS_HEADER`, `XFF_DEPTH`

## Réseau Docker

### academie-net-bridge (principal)
- **Subnet** : `172.16.0.0/27` (gateway 172.16.0.1)
- **Capacité** : 30 IPs utilisables
- **Utilisation actuelle** : 11 containers — 19 slots libres
- **Marqué `external: true`** dans compose (créé manuellement hors compose)
- Communication inter-container via noms DNS (`postgres-academie`, `litellm-proxy`, `dify-api`)
- **Migration 2026-04-15 (Session 15)** : ancien /28 (172.16.0.16/28, saturé 12/14) → /27 ; IPs réassignées dynamiquement.

### Autres networks
- `bridge` (docker0 default, 172.17.0.0/16) : utilisé par `cosmos-mongo-KIo` seulement
- `host` : utilisé par `cosmos-server` (privileged)
- `none` : non utilisé

### Bind mounts host

| Host path | Container target | Container | Taille |
|---|---|---|---|
| `/mnt/cosmos-data/postgres` | `/var/lib/postgresql/data` | postgres-academie | ~305 MB |
| `/opt/dify/storage` | `/app/api/storage` | dify-api, dify-worker | ~1.9 MB |
| `/opt/dify/plugin_daemon` | `/app/storage` | dify-plugin-daemon | ~227 MB |
| `/opt/n8n/data` | `/home/node/.n8n` | n8n-academie | ~3.2 MB |
| `/opt/litellm/config.yaml` | `/app/config.yaml` | litellm-proxy | 10 KB |
| `/mnt/cosmos-data/cosmos-config` | `/config` | cosmos-server | — |
| `/` | `/mnt/host` | cosmos-server (rslave) | **host entier** ⚠️ |
| `/var/run/docker.sock` | même | cosmos-server | — |

## Secrets actuels (dette)

⚠️ **ETAT DETTE** : plusieurs secrets en clair (détail dans [credentials.md](credentials.md)) :
- `/opt/litellm/config.yaml` contient les clés API OpenAI/Groq/Mistral en clair
- `general_settings.database_url` contient le DB password
- `/opt/academia/webapp/.env` contient JWT_SECRET_KEY, JWT_REFRESH_SECRET, DATABASE_URL, DIFY_KEY_TEACHER
- `/opt/academia-shared/secrets/` (9 fichiers chmod 600)

## Services systemd (sur host)

Seulement 2 services pertinents :
- `docker.service` — daemon Docker
- `nginx.service` — reverse proxy

## Cron actifs

| Frequency | Job | Via |
|---|---|---|
| Hourly | `pg-backup` → `/mnt/cosmos-data/backups/postgres/` | `/etc/cron.d/pg-backup` |
| Hourly | Snapshot safety fallback | root crontab |
| Daily 03:30 | `restic-backup` → Google Drive | `/etc/cron.d/restic-backup` |
| Every 15 min | `smoke-monitor` | `/etc/cron.d/smoke-monitor` |

Cf. [backup.md](backup.md) et [monitoring.md](monitoring.md).

## SSL / HTTPS

- Cloudflare Tunnel fournit le TLS
- nginx en interne parle en HTTP (pas de certificat local)
- HSTS et security headers gérés par nginx (CSP, X-Frame-Options, etc.)

## Performance

- Ressources dispo : 12 GB RAM, 4 vCPU, SSD
- Profile actuel : largement sous-utilisé (famille ~20 users)
- Limits docker :
  - academie-frontend : 256M RAM / 0.5 CPU
  - academie-api : 512M RAM / 1 CPU

## Références

- [overview.md](../02-architecture/overview.md) — vue macro stack
- [backup.md](backup.md) — stratégie de backup
- [monitoring.md](monitoring.md) — observability
- [credentials.md](credentials.md) — gestion des secrets
- [_legacy/infra.md](../_legacy/infra.md) — version pré-migration (à supprimer après validation)
