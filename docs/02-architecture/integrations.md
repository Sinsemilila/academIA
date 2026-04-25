---
title: Integrations — Dify, n8n, LiteLLM, nginx
status: authoritative
last_reviewed: 2026-04-15
---

# Integrations

> Détail des 3 intégrations critiques (Dify chatflows, n8n workflows, LiteLLM config) + routage nginx. Snapshot 2026-04-15.

## Dify — 8 apps, 1 chatflow actif

**Source** : `docker exec postgres-academie psql -U sinse -d academie_db -c "SELECT id, name, mode FROM apps;"`

### Inventaire apps

| ID (préfixe) | Nom | Mode | Conversations | Messages | Workflow |
|---|---|---|---|---|---|
| `39565197…` | **Teacher - Professeur d'Anglais** | **advanced-chat** | 125 | **1693** | `c52a451f-…` |
| `62dd705f…` | Maestro - Professeur d'Espagnol | chat | 8 | 10 | — |
| `9312757e…` | Sensei - Professeur de Japonais | chat | 5 | 8 | — |
| `0105e199…` | cccccccc | chat | 2 | 7 | — (app test à cleanup) |
| `bbff768c…` | PyMentor - Professeur de Python | chat | 4 | 4 | — |
| `6c60c1e3…` | CyberMentor - Professeur de Cybersécurité | chat | 2 | 3 | — |
| `97bcee50…` | Lehrer - Professeur d'Allemand | chat | 3 | 3 | — |
| `0e5a692d…` | Professore - Professeur d'Italien | chat | 3 | 3 | — |

**Seul Teacher** est en mode `advanced-chat` (chatflow complet). Les 6 autres agents et l'app test sont en mode `chat` simple — aucun workflow, pas utilisés en prod.

### Teacher chatflow — 41 nodes / 45 edges

Détail complet dans [`../03-domain/languages/en.md`](../03-domain/languages/en.md).

### Provider models actifs Dify (5)

Tous via provider `langgenius/openai_api_compatible` → pointe vers LiteLLM proxy :

| model_name | usage |
|---|---|
| `gpt-4o-mini` | Teacher primary (free tier OpenAI) |
| `groq-standard` | Fallback chat (Llama 3.3 70B) |
| `groq-snapshot` | Snapshots session |
| `groq-qwen` | Futur JP/ZH (Qwen 32B) |
| `mistral-small` | Fallback FR/ES/IT |

Tenant ID unique : `4c3e17be-144c-4e7a-968e-478d6c48fb2f`.

### Cleanup recommandé

- ❌ Supprimer l'app test `cccccccc` (7 messages orphelins)
- 🔄 Les 6 agents placeholders (mode chat simple) seront archivés/reconfigurés quand on migrera vers le chatflow paramétré unifié `language-tutor` (cf. [ADR-004](../05-decisions/ADR-004-hybrid-orchestrated-agent-topology.md))

---

## n8n — 7 workflows actifs

**Backend PG** (même `academie_db`, table `workflow_entity`).

### Inventaire workflows

| ID | Nom | Nodes | Webhook path | Method | Runs | Success | Fail |
|---|---|---|---|---|---|---|---|
| `8NnhEQWCSr0octMS` | dify-profil-get | 4 | `dify-profil-get` | GET | 2024 | 2024 | 0 ✅ |
| `Rxuu4JTe8KMlgJ9L` | dify-profil-update | 3 | `dify-profil-update` | POST | 87 | 83 | 4 |
| `tVfLg92ijYUvBc94` | **dify-snapshot** | 13 | `dify-snapshot` | POST | 144 | 119 | **25 ⚠️ 17%** |
| `58dd0014770a4c` | **dify-diagnostic** | 8 | `dify-diagnostic` | POST | 32 | 23 | **9 ⚠️ 28%** |
| `f79033231f7644` | **dify-diagnostic (DOUBLON)** | 8 | `dify-diagnostic` | POST | — | — | **doublon ⚠️** |
| `y52Fa9sYBmtuwz8y` | dify-exam-scoring | 10 | `dify-exam-scoring` | POST | 60 | 58 | 2 |
| `ePrsExm8St4t2Svd` | dify-exam-persist | 4 | `dify-exam-persist` | POST | 842 | 842 | 0 ✅ |

**Total** : 3189 exécutions (3149 OK, 40 errors). 2 workflows avec même nom/path → **bug à résoudre**.

### Détail par workflow

**`dify-profil-get`** (4 nodes) — GET webhook → postgres → code → respond

**`dify-profil-update`** (3 nodes) — POST webhook → code → postgres (async, pas de respond)

**`dify-snapshot`** (13 nodes, le plus complexe) :
1. Webhook POST
2. `Fetch Dify Messages` (httpRequest vers `dify-api:5001/console/api/apps/.../chat-messages`)
3. 3× Code JS
4. `Fetch Student Data` (postgres)
5. `Build Profil Update` (code)
6. `SQL Profil Update` (postgres)
7. `HTTP Request` → **LiteLLM** (`litellm-proxy:4000/v1/chat/completions`) pour génération snapshot
8. `Execute a SQL query` (postgres)
9. `Build Error Analysis Body` (code)
10. **`Trigger Error Analysis`** → `http://academie-api:8000/internal/analyze-errors` (pipeline erreurs)
11. `Respond to Webhook`

**`dify-diagnostic`** (8 nodes) — webhook → postgres (fetch profile) → code → **LiteLLM** (scoring CECRL) → postgres → respond

**`dify-exam-scoring`** (10 nodes) — webhook → **Dify Console API** (fetch exam messages) → postgres (error profile) → code → **LiteLLM** (LLM score) → code → postgres (update) → respond

**`dify-exam-persist`** (4 nodes) — webhook → code → postgres update → respond

### Node types utilisés

- `n8n-nodes-base.webhook` (trigger HTTP)
- `n8n-nodes-base.respondToWebhook`
- `n8n-nodes-base.code` (JavaScript)
- `n8n-nodes-base.postgres` (tous en `executeQuery`)
- `n8n-nodes-base.httpRequest`

### Volumétrie n8n

- `execution_data` : 3189 rows, 32 MB
- `workflow_history` : 8 rows (versions)

---

## LiteLLM — 10 modèles actifs, 21 entrées total

**Fichier** : `/opt/litellm/config.yaml` (270 lignes, non versionné git).
**Container** : `litellm-proxy`, port `127.0.0.1:4000`.
**Version** : LiteLLM 1.82.6.
**DB spend logs** : `litellm_db` (activé Session 12, cf. [ADR-006](../05-decisions/ADR-006-litellm-byok-familial.md)).

### Sections config.yaml

1. `general_settings` — database_url (litellm_db), `disable_spend_logs: false`, `store_prompts_in_spend_logs: false`
2. `router_settings` — routing_strategy, fallbacks, retry config
3. `model_list` — 21 entrées (10 actives + 11 commentées = blocs BYOK à activer)

### model_groups actifs (8)

| model_group | Provider | Modèle upstream | Tier | Usage |
|---|---|---|---|---|
| `gpt-4o-mini` | OpenAI | openai/gpt-4o-mini | Free tier | **Teacher primary** |
| `ft:gpt-4o-mini-...v2:DTurinhs` | OpenAI | openai/ft:gpt-4o-mini-... | Paid | DEPRECATED |
| `ft:gpt-4o-mini-...v3:DU6GUv6v` | OpenAI | openai/ft:gpt-4o-mini-...v3 | Paid | **error_analysis** (4208 exemples training) |
| `groq-standard` | Groq (**pool 2 clés**) | llama-3.3-70b-versatile | Free | Fallback chat |
| `groq-snapshot` | Groq (**pool 2 clés**) | llama-3.1-8b-instant | Free | Snapshots |
| `groq-qwen` | Groq | qwen/qwen3-32b | Free | Futur JP/ZH |
| `mistral-small` | Mistral | mistral-small-latest | Free | ⚠️ rpm=2 |
| `ollama-cloud` | Custom (ollama.com/v1) | openai/nemotron-3-nano:30b-cloud | — | Expérimental |

### Routing strategy

- `routing_strategy: usage-based-routing-v2` (load-balance sur la clé la moins utilisée)
- `allowed_fails: 1`, `cooldown_time: 60s` après rate limit
- `num_retries: 3`, `retry_after: 5s`

### Fallback chains

```yaml
gpt-4o-mini      → groq-standard → mistral-small
groq-snapshot    → mistral-small
groq-standard    → ollama-cloud → mistral-small
groq-qwen        → mistral-small
```

⚠️ **Mistral rpm=2** → goulot si cascade tombe jusqu'à lui.

### Spend logs aujourd'hui (2026-04-15)

- `gpt-4o-mini` : 4 calls, **52 104 tokens**, $0.0078
- Autres : quelques calls mistral-small, nemotron, qwen

### BYOK à activer

11 blocs de modèles commentés dans config.yaml prêts pour BYOK (clés amis) cf. [ADR-006](../05-decisions/ADR-006-litellm-byok-familial.md). À décommenter après mise en place SOPS (cf. [credentials.md](../04-infra/credentials.md)).

---

## nginx — hôte, port 8080

**nginx sur le HOST** (systemd `nginx.service`), pas dans un container.

Fichiers :
- `/etc/nginx/nginx.conf` (global)
- `/etc/nginx/sites-enabled/dify` → `sites-available/dify` (seul vhost actif)

### nginx.conf global

- user `www-data`
- TLS : TLSv1.2 + TLSv1.3, `ssl_prefer_server_ciphers off`
- `server_tokens off`
- gzip on
- worker_connections 768, worker_processes auto

### vhost `dify` — 2 server blocks sur port 8080

**Server 1 : `dify.petit-pont.com`**

| Location | proxy_pass | Notes |
|---|---|---|
| `/files/` | `http://127.0.0.1:5001` | `client_max_body_size 20M` |
| `/console/api` | `http://localhost:5001` | |
| `/api` | `http://127.0.0.1:5001` | |
| `/` | `http://127.0.0.1:3000` | dify-web |

**Pas de security headers** sur ce vhost.

**Server 2 : `academie.petit-pont.com`** — security headers globaux :

```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; 
                         style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
                         font-src 'self' https://fonts.gstatic.com;
                         img-src 'self' https://flagcdn.com data:;
                         connect-src 'self'; frame-ancestors 'none';
```

| Location | proxy_pass | Cache |
|---|---|---|
| `~* (manifest\|sw\.js)$` | `127.0.0.1:3001` | `no-cache, no-store, must-revalidate` |
| `~* \.(png\|jpg\|...\|css\|js)$` | `127.0.0.1:3001` | `expires 7d, public, immutable` |
| `/` | `127.0.0.1:3001` | WebSocket upgrade, `proxy_buffering off`, `proxy_read_timeout 120s` |

**HSTS géré côté Cloudflare**, pas dupliqué ici.

### Pas de default_server

Requête sans `Host:` → 307 redirect vers `/apps` (comportement Dify capturé par défaut). Non bloquant mais à nettoyer (ajouter un `default_server` explicite qui renvoie 444 ou page d'info).

---

## Cosmos Server UI

- Container `cosmos-server` (privileged, host network, `/` bind-mounté)
- UI admin sur port 80/443 (ports exposés en network=host)
- Backend MongoDB via `cosmos-mongo-KIo` (réseau docker0 bridge par défaut, isolé)

**Action à faire** : audit sécurité Cosmos Server avant ouverture SaaS public (privileged + Docker socket = très sensible).

---

## Diagramme des flux principaux

### Flux chat (user → Teacher)

```
User (browser)
  ↓ HTTPS via Cloudflare Tunnel
nginx :8080 (Host: academie.petit-pont.com)
  ↓ /api/* → 
academie-api :8000 (POST /api/chat/send)
  ↓ SSE request
dify-api :5001 (/v1/chat-messages)
  ↓ chatflow Teacher (41 nodes)
  ├── n8n :5678 (/webhook/dify-profil-get) → postgres
  ├── litellm-proxy :4000 (LLM call)
  │     └── OpenAI / Groq / Mistral
  └── n8n :5678 (/webhook/dify-snapshot) [every 10 turns]
        └── academie-api:8000 (/internal/analyze-errors)
              └── litellm-proxy :4000 (ft:gpt-4o-mini-v3)
```

### Flux onboarding diagnostic

```
User complète 5-7 questions EN
  ↓ [EVAL_READY] détecté
Teacher chatflow if_eval_ready → true
  ↓ HTTP
n8n /webhook/dify-diagnostic
  ↓ litellm :4000 (scoring CECRL)
  ↓ postgres: UPDATE profils_eleves (niveau_global, scores_confiance, ...)
  ↓ respond
```

## Références

- [overview.md](overview.md) — stack macro
- [api-surface.md](api-surface.md) — endpoints FastAPI + routes SvelteKit
- [data-model.md](data-model.md) — schémas DB
- [../03-domain/languages/en.md](../03-domain/languages/en.md) — Teacher chatflow détaillé
- [../04-infra/deployment.md](../04-infra/deployment.md) — infrastructure
- [../99-runbooks/gotchas.md](../99-runbooks/gotchas.md) — risques et workarounds
