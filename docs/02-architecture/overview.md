---
title: Architecture Overview
status: authoritative
last_reviewed: 2026-04-15
---

# Architecture Overview

> Vue macro de la stack AcademIA. Pour les détails : voir les docs liées en fin de page.

## Diagramme macro

```
┌──────────────────────────────────────────────────────────────┐
│                   Utilisateurs (familial ~20)                 │
│                   Browser: academia.petit-pont.com            │
└───────────────────────┬──────────────────────────────────────┘
                        │ HTTPS
                        ▼
┌──────────────────────────────────────────────────────────────┐
│             Cloudflare Tunnel (zéro port ouvert)              │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────────────────┐
│  cosmos (Debian VM, Proxmox, 192.168.1.181)                        │
│                                                                     │
│  ┌─────────────────────────────┐                                   │
│  │ nginx (HOST, port 8080)     │  ← sites-enabled/dify             │
│  │ systemd nginx.service        │    CSP + security headers        │
│  └───┬─────────────────────────┘                                   │
│      │                                                              │
│      ├── academia.petit-pont.com → 127.0.0.1:3001 (SvelteKit)      │
│      ├── dify.petit-pont.com     → 127.0.0.1:5001/3000 (Dify)      │
│      └── n8n.petit-pont.com      → 127.0.0.1:5678 (n8n)            │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Docker sur network academie-net-bridge (172.16.0.16/28 —    │   │
│  │ /28 = 14 IPs utilisables — SATURÉ : 12 IPs prises)          │   │
│  │                                                               │   │
│  │  academie-frontend (172.16.0.28, :3001) ─ SvelteKit          │   │
│  │  academie-api       (172.16.0.27, :8000) ─ FastAPI monolithe │   │
│  │                                                               │   │
│  │  dify-api           (172.16.0.20, :5001) ─ Chatflows         │   │
│  │  dify-web           (172.16.0.26, :3000) ─ UI Dify admin     │   │
│  │  dify-worker        (172.16.0.21)        ─ Celery            │   │
│  │  dify-plugin-daemon (172.16.0.23, :5002) ─ Plugin system     │   │
│  │  dify-sandbox       (172.16.0.18, :8194) ─ Code sandbox      │   │
│  │                                                               │   │
│  │  n8n-academie       (172.16.0.25, :5678) ─ Workflows         │   │
│  │  litellm-proxy      (172.16.0.24, :4000) ─ LLM gateway       │   │
│  │                                                               │   │
│  │  postgres-academie  (172.16.0.19, :5432) ─ PG 16.13          │   │
│  │    └ DBs: academie_db (198MB) + litellm_db + dify_plugin     │   │
│  │  redis-academie     (172.16.0.22)        ─ Cache + Celery    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ cosmos-server (HOST network, privileged !)                   │   │
│  │ UI admin Cosmos, / bind-mounté, docker.sock accessible       │   │
│  │ + cosmos-mongo-KIo (bridge default 172.17.0.0/16)            │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
           Providers externes (via LiteLLM proxy uniquement)
           - OpenAI (gpt-4o-mini + ft:gpt-4o-mini-v2 + v3)
           - Groq (Llama 3.3, Llama 3.1, Qwen 32B)
           - Mistral (mistral-small)
           - Ollama Cloud (nemotron-3-nano)
```

## Observations importantes

1. **nginx est sur le HOST** (systemd service), pas dans un container. Seule la UI Cosmos (`cosmos-server` container) est dans Docker — elle est privileged avec `/` bind-mounté → **risque sécurité à surveiller**.
2. **Subnet /28 saturé** : 14/14 IPs utilisées, 2 seulement dynamiquement dispos. Ajout d'un nouveau container requiert soit retrait d'un existant, soit migration vers /27 (nécessite recréation du bridge).
3. **Qdrant référencé mais pas déployé** : env var `QDRANT_HOST=qdrant-server` dans dify-api, mais pas de container `qdrant-server`. Dead pointer hérité (Qdrant déployé puis retiré en phase 1, cf. HISTORY.md). Non bloquant car RAG pas utilisé.
4. **MongoDB (`cosmos-mongo-KIo`)** : installé pour Cosmos Server admin UI, sur le bridge par défaut (172.17.0.0/16), isolé du reste.
5. **Dangling Docker volume** 820 MB non attaché — à cleanup (`docker volume prune`).

## Composants

### Frontend
**SvelteKit (Svelte 5 runes)** sur `:3001`. Geist font, Tailwind, dark theme, PWA-capable. **12 routes** + **17 components** (cf. [api-surface.md](api-surface.md)).

### Backend (monolithe actuel — cf. [ADR-001](../05-decisions/ADR-001-monolith-vs-microservices.md))
**FastAPI** sur `:8000`. **36 endpoints** via 6 routers (détail dans [api-surface.md](api-surface.md)) :
- `auth_router` (4 endpoints) — login JWT HS256, refresh 7j, users admin
- `chat_router` (4) — proxy SSE vers Dify, token tracking dual (tiktoken + LiteLLM), auto-switch gpt-4o-mini → groq-standard à 1.5M tokens
- `profile_router` (10) — profils, stats, streak, XP, badges (9 def), heatmap 180j
- `settings_router` (10) — préférences, password, session mgmt, weekly recap
- `error_analysis_router` (3) — endpoint interne `/internal/analyze-errors` appelé par n8n (auth `X-Internal-Token`)
- `admin_router` (4) — users, reset profile, exam-result, user delete

Rate limiting IP : 5/60s login, 10/60s refresh, 30/60s chat, 5/300s password.

Pool PostgreSQL asyncpg : 2 pools (academie_db + litellm_db pour tracking).

### Chatflows Dify
**Dify 1.13.3** sur `:5001`. Orchestration LLM visuelle.
- Teacher EN — **chatflow actif** `c52a451f-e381-46f1-a23a-077197b0fccb` (41 nodes, 45 edges, 15 conversation variables)
- **7 autres apps existent en mode `chat` simple** (Maestro/Sensei/Lehrer/Professore/PyMentor/CyberMentor + une app test `cccccccc` à cleanup) — pas de chatflow, pas en prod
- Futur : `language-tutor` unifié paramétré par langue (cf. [agent-topology.md](agent-topology.md))
- Détail dans [integrations.md](integrations.md).

### Workflows n8n
**n8n 2.14.2** sur `:5678`. Backend PG (même academie_db). **7 workflows actifs** :
- `dify-profil-get` (4 nodes, GET) — fetch profil — 2024 runs, 100% OK
- `dify-snapshot` (13 nodes, POST) — snapshots toutes les 10 interactions — 144 runs, **83% OK / 17% fail** ⚠️
- `dify-profil-update` (3 nodes, POST) — update profil — 83/87 OK
- `dify-diagnostic` (8 nodes, POST) — scoring CECRL — **23/32 OK / 28% fail** ⚠️ — **DOUBLON détecté** : 2 workflows avec même nom/webhook
- `dify-exam-scoring` (10 nodes, POST) — 58/60 OK
- `dify-exam-persist` (4 nodes, POST) — 842 runs, 100% OK

Détail dans [integrations.md](integrations.md).

### LiteLLM proxy
**LiteLLM 1.82.6** sur `:4000`. Seul gateway LLM. Routing + load-balancing + fallbacks + spend logs actifs (cf. [integrations.md](integrations.md)).

**21 entrées dans model_list** (10 actives + 11 commentées BYOK à activer) → **8 model_groups actifs** :
1. `gpt-4o-mini` (free tier OpenAI) — primary
2. `ft:gpt-4o-mini-v2:DTurinhs` (paid, DEPRECATED)
3. `ft:gpt-4o-mini-v3:DU6GUv6v` (paid) — error analysis (4208 exemples training)
4. `groq-standard` (Llama 3.3 70B, **pool 2 clés**)
5. `groq-snapshot` (Llama 3.1 8B Instant, **pool 2 clés**)
6. `groq-qwen` (Qwen 3 32B)
7. `mistral-small` (rpm=2 ⚠️ goulot)
8. `ollama-cloud` (nemotron-3-nano via ollama.com/v1)

Fallback chains : `gpt-4o-mini → groq-standard → mistral-small`. Load-balancing `usage-based-routing-v2` (cf. [ADR-006](../05-decisions/ADR-006-litellm-byok-familial.md)).

### Base de données
**PostgreSQL 16.13** sur `:5432`. Quatre DBs (cf. [data-model.md](data-model.md)) :
- `academie_db` (198 MB) — **mégabase mix 5 systèmes** : AcademIA + Dify + n8n + LiteLLM shadow + chat_hub. 250 tables.
- `litellm_db` (11 MB) — spend logs LiteLLM réels (source de vérité tracking)
- `dify_plugin` (8.3 MB) — Dify plugin daemon state
- `postgres` (7.5 MB) — maintenance

**Redis 7.4.8** sur `:6379` — cache + broker Celery (utilisé par Dify). 38 keys, 1.83 MB used. **Aucune donnée métier AcademIA en Redis** — tout est en PG.

### Networking
Docker network `academie-net-bridge` **en /28** : 14 IPs utilisables, **12 prises** (seulement 2 slots dynamiques libres) — ⚠️ contrainte de scalabilité imminente.

nginx sur le **host** (pas dans un container), port `:8080`, systemd. Routage par `Host:` header (cf. [integrations.md](integrations.md)).

Cloudflare Tunnel : hostname `academia.petit-pont.com` / `dify.petit-pont.com` / `n8n.petit-pont.com` → cosmos:8080 via tunnel chiffré. Zéro port ouvert sur le NAT.

## Flux typique (chat utilisateur)

```
1. User tape message dans SvelteKit /chat/teacher
2. POST /api/chat/send → FastAPI
3. FastAPI appelle Dify /v1/chat-messages (SSE streaming)
4. Dify exécute chatflow Teacher :
   a. code_profil_check (Python sandbox)
   b. GET /webhook/dify-profil-get vers n8n
   c. code_turn_check + code_check (sandbox)
   d. llm_session ou llm_onboarding — appel LiteLLM gpt-4o-mini
   e. code_eval_check (sandbox, strip markers)
   f. answer_node streamé vers FastAPI
5. FastAPI streame tokens vers SvelteKit
6. FastAPI tracke les tokens localement (tiktoken) pour auto-switch
7. LiteLLM logue spend dans LiteLLM_SpendLogs (batch ~30-60s)
8. Tous les 10 messages, Dify déclenche dify-snapshot n8n → update profil
```

## Volumétrie actuelle (avril 2026)

- Users actifs : ~5-10
- Interactions totales : ~quelques milliers
- Tokens OpenAI/jour : 50K-500K (variable selon tests)
- Latency chat (blocking mode, free tier OpenAI) : ~60s par tour
- Latency chat (streaming, real user) : ~1-5s first token, 15-25s full response

## Décisions architecturales en vigueur

- [ADR-001](../05-decisions/ADR-001-monolith-vs-microservices.md) — monolithe maintenu
- [ADR-002](../05-decisions/ADR-002-schema-from-day-1.md) — schéma multi-domaine dès départ
- [ADR-004](../05-decisions/ADR-004-hybrid-orchestrated-agent-topology.md) — architecture hybride orchestrée (in-principle)
- [ADR-005](../05-decisions/ADR-005-academie-core-shared-library.md) — package `academie-core`
- [ADR-006](../05-decisions/ADR-006-litellm-byok-familial.md) — pool BYOK LiteLLM

## Docs liées
- [data-model.md](data-model.md) — schéma DB détaillé
- [agent-topology.md](agent-topology.md) — topologie des agents (cible)
- [shared-core.md](shared-core.md) — interface `Domain`
- [../04-infra/deployment.md](../04-infra/deployment.md) — détails Docker Compose
