---
title: Filesystem Scan (snapshot 2026-04-15)
status: snapshot
last_reviewed: 2026-04-15
---

# Filesystem Scan — AcademIA on cosmos

> **⚠️ SNAPSHOT PONCTUEL** — ce fichier est un dump d'état pris le 2026-04-15 par un agent de scan.
> Il n'est **pas maintenu automatiquement**. Les informations structurelles ont été extraites dans les docs authoritative (`deployment.md`, `backup.md`, etc.). Consulter ces docs pour l'état courant.
> Ce fichier reste ici comme référence historique et en cas d'audit détaillé.
>
> **Éléments rendus obsolètes par Session 15** : subnet `172.16.0.16/28` → `172.16.0.0/27` ; dangling volumes 820M+24K supprimés ; `pg-backup` couvre 3 DBs ; workflow `dify-diagnostic` `f79033231f7644` archivé ; app Dify `cccccccc` supprimée.

Host: `cosmos` (Debian Linux 6.12.74+deb13+1-amd64)
Scan date: 2026-04-15
Scope: `/opt/academia`, `/opt/academia-shared`, `/opt/litellm`, `/mnt/cosmos-data`, systemd services, cron, nginx, git state.

---

## 1. `/opt/academia` — Top-level structure

### 1.1 Directory tree (depth 3–4, excluding `node_modules`, `__pycache__`, `.git/*`)

```
/opt/academia
├── .claude
│   └── commands
├── .git
├── AGENTS.md
├── HISTORY.md
├── README.fr.md
├── README.md
├── .gitignore
├── .dify_admin_key                 (symlink → /opt/academia-shared/secrets/dify-admin-key)
├── docs
│   ├── api-overview.md             (1.3K)
│   ├── architecture.md             (2.5K)
│   ├── decisions.md                (3.8K)
│   ├── test-plan-features.md       (5.5K)
│   └── test-results-features.md    (7.0K)
├── scripts                         (39 .py files, 616K)
└── webapp
    ├── PLAN.md
    ├── docker-compose.webapp.yml
    ├── backend
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── app
    │       ├── config/             (tolerance_matrix.yaml)
    │       ├── error_taxonomy/     (5 .py modules)
    │       └── routers/            (6 .py routers)
    └── frontend
        ├── Dockerfile
        ├── README.md
        ├── package.json
        ├── package-lock.json (96K)
        ├── svelte.config.js
        ├── tsconfig.json
        ├── vite.config.ts
        ├── node_modules/           (570M — not scanned)
        ├── .svelte-kit/types
        ├── .vscode
        ├── src/
        │   ├── app.d.ts
        │   ├── app.html
        │   ├── hooks.server.ts
        │   ├── lib/                (api.ts, config.ts, components/, stores/, assets/)
        │   └── routes/             (9 route folders)
        └── static/                 (flags/, fonts/, icons/, 232K)
```

### 1.2 Sub-folder sizes

| Path | Size |
|---|---|
| `/opt/academia/AGENTS.md` | 4.0K |
| `/opt/academia/README.fr.md` | 4.0K |
| `/opt/academia/HISTORY.md` | 12K |
| `/opt/academia/README.md` | 12K |
| `/opt/academia/docs` | 32K |
| `/opt/academia/scripts` | 616K |
| `/opt/academia/webapp` | 571M |
| &nbsp;&nbsp;&nbsp;`webapp/backend` | 328K |
| &nbsp;&nbsp;&nbsp;`webapp/frontend` | 570M (of which `node_modules` = 570M) |
| &nbsp;&nbsp;&nbsp;`webapp/frontend/src` | 352K |
| &nbsp;&nbsp;&nbsp;`webapp/frontend/static` | 232K |

### 1.3 Last modification date per folder

| Folder | Last mtime |
|---|---|
| `/opt/academia/docs` | 2026-04-15 09:57 |
| `/opt/academia/scripts` | 2026-04-15 09:39 |
| `/opt/academia/webapp` | 2026-04-13 18:26 |
| `/opt/academia/webapp/backend` | 2026-04-12 20:26 |
| `/opt/academia/webapp/backend/app` | 2026-04-15 10:14 |
| `/opt/academia/webapp/backend/app/routers` | 2026-04-15 10:14 |
| `/opt/academia/webapp/backend/app/error_taxonomy` | 2026-04-14 14:02 |
| `/opt/academia/webapp/frontend/src` | 2026-04-07 13:53 |
| `/opt/academia/webapp/frontend/src/routes` | 2026-04-14 13:41 |
| `/opt/academia/webapp/frontend/src/lib` | 2026-04-14 15:28 |
| `/opt/academia/webapp/frontend/src/lib/components` | 2026-04-13 19:02 |

---

## 2. `/opt/academia/webapp`

### 2.1 Backend Python files (`webapp/backend/app/`)

| Path | Lines | Module docstring / first comment |
|---|---:|---|
| `app/__init__.py` | 0 | (empty) |
| `app/auth.py` | 99 | (no module docstring) — "Config / Password helpers / JWT helpers" |
| `app/database.py` | 36 | (no module docstring) — "LiteLLM SpendLogs lives in litellm_db (same PG instance as academie_db)" |
| `app/main.py` | 89 | (no module docstring) — "Structured logging" |
| `app/models.py` | 80 | (no module docstring) — "Auth / User" |
| `app/rate_limit.py` | 69 | "Simple in-memory rate limiter for FastAPI." |
| `app/routers/__init__.py` | 0 | (empty) |
| `app/routers/admin_router.py` | 162 | "AcademIA — Admin & internal endpoints" |
| `app/routers/auth_router.py` | 104 | (no module docstring) |
| `app/routers/chat_router.py` | 471 | (no module docstring) — "Daily token budget for gpt-4o-mini (free tier protection)" |
| `app/routers/error_analysis_router.py` | 238 | "AcademIA Error Taxonomy — Monolithic analysis endpoint" |
| `app/routers/profile_router.py` | 692 | (no module docstring) — "Rank thresholds / Badge definitions" |
| `app/routers/settings_router.py` | 291 | "Profile settings, password change, active sessions, recommendations." |
| `app/error_taxonomy/__init__.py` | 0 | (empty) |
| `app/error_taxonomy/categories.py` | 55 | "AcademIA Error Taxonomy — 57 effective categories (63 model outputs, 6 fused)" |
| `app/error_taxonomy/differ.py` | 134 | "AcademIA Error Taxonomy — Step 2: Diff engine" |
| `app/error_taxonomy/llm.py` | 303 | "AcademIA Error Taxonomy — LLM layer" |
| `app/error_taxonomy/rules.py` | 754 | "AcademIA Error Taxonomy — Step 3: Rule-based span classification" |
| `app/error_taxonomy/scoring.py` | 356 | "AcademIA — Unified Progression Scoring Engine" |

Config file:
- `app/config/tolerance_matrix.yaml` — 17.3K (CEFR tolerance thresholds, mod 2026-04-13)

`requirements.txt` (12 deps): fastapi 0.115.12, uvicorn[standard] 0.34.3, asyncpg 0.30.0, python-jose[cryptography] 3.4.0, passlib[bcrypt] 1.7.4, bcrypt 4.0.1, pydantic 2.11.7, httpx 0.28.1, python-multipart 0.0.20, tenacity 9.1.2, pyyaml 6.0.3, tiktoken 0.9.0.

### 2.2 Frontend SvelteKit routes (`frontend/src/routes/`)

| Path | Lines | First comment / purpose |
|---|---:|---|
| `+error.svelte` | 23 | (no comment) |
| `+layout.svelte` | 222 | (no comment — global layout) |
| `+page.svelte` | 341 | `// Concept popover state` (home) |
| `layout.css` | — | global layout styles |
| `admin/+page.svelte` | 279 | (no comment) admin dashboard |
| `changelog/+page.svelte` | 123 | (no comment) |
| `chat/[agent]/+page.svelte` | 547 | (no comment) dynamic chat route |
| `legal/+page.svelte` | 73 | (no comment) |
| `login/+page.svelte` | 91 | (no comment) |
| `profile/+page.svelte` | 324 | (no comment) |
| `stats/+page.svelte` | 222 | (no comment) |
| `stats/concepts/+page.svelte` | 208 | (no comment) |

### 2.3 Frontend `lib/` — components & stores

Library code:

| Path | Lines | First comment |
|---|---:|---|
| `lib/api.ts` | 328 | (no comment) — API client wrappers |
| `lib/config.ts` | 20 | `// Agent definitions — single source of truth` |
| `lib/index.ts` | 1 | `// place files you want to import through the $lib alias in this folder.` |
| `lib/stores/auth.ts` | 12 | (no comment) |
| `lib/stores/theme.ts` | 47 | `// Theme store — syncs with DOM, localStorage, and DB` |
| `lib/stores/toasts.ts` | 82 | `// Enhanced toast notification store — supports undo, progress, countdown` |
| `lib/stores/user.ts` | 14 | `// User appearance store — set by layout, read by chat components` |

Components:

| Path | Lines | First comment |
|---|---:|---|
| `lib/components/ActivityHeatmap.svelte` | 179 | (no comment) |
| `lib/components/AgentFlag.svelte` | 25 | (no comment) |
| `lib/components/CelebrationModal.svelte` | 151 | `/** ... */` |
| `lib/components/CommandPalette.svelte` | 160 | (no comment) |
| `lib/components/ConfirmDialog.svelte` | 44 | (no comment) |
| `lib/components/ConnectionIndicator.svelte` | 23 | (no comment) |
| `lib/components/Header.svelte` | 169 | (no comment) |
| `lib/components/KeyboardShortcuts.svelte` | 106 | (no comment) |
| `lib/components/ProgressionGraph.svelte` | 149 | `/** ... */` |
| `lib/components/Sidebar.svelte` | 133 | (no comment) |
| `lib/components/SkillTree.svelte` | 395 | `/** ... */` |
| `lib/components/Toasts.svelte` | 69 | (no comment) |
| `lib/components/Tooltip.svelte` | 11 | (no comment) |
| `lib/components/WeeklyRecap.svelte` | 48 | `<!-- Accent bar — brighter on Monday -->` |
| `lib/components/chat/ChatBubble.svelte` | 143 | (no comment) |
| `lib/components/chat/ChatInput.svelte` | 56 | (no comment) |
| `lib/components/chat/TypingIndicator.svelte` | 53 | `<!-- Bot avatar -->` |

Root sources:

| Path | Lines | First comment |
|---|---:|---|
| `src/app.d.ts` | 13 | `// See https://svelte.dev/docs/kit/types#app.d.ts` |
| `src/app.html` | — | HTML shell |
| `src/hooks.server.ts` | 37 | `// Proxy /api/* requests to FastAPI backend` |

### 2.4 `webapp/docker-compose.webapp.yml` — containers

Two services, bridged on external network `academie-net-bridge`:

| Service | Image build | Host port | Memory | CPUs |
|---|---|---|---|---|
| `academie-frontend` | `${WEBAPP_SRC}/frontend` | 127.0.0.1:3001 → 3000 | 256M | 0.5 |
| `academie-api` | `${WEBAPP_SRC}/backend` | 127.0.0.1:8000 → 8000 | 512M | 1.0 |

Frontend env: `ORIGIN=https://academia.petit-pont.com`, `PROTOCOL_HEADER=x-forwarded-proto`, `HOST_HEADER=x-forwarded-host`, `ADDRESS_HEADER=x-forwarded-for`, `XFF_DEPTH=1`.

---

## 3. `/opt/academia/scripts` — Utility Python scripts

39 files; total 616K. Purpose extracted from first line of module docstring where available.

| Script | Size | Lines | Purpose |
|---|---:|---:|---|
| `add_error_analysis_to_snapshot.py` | 5.4K | 166 | Adds error analysis trigger to the dify-snapshot n8n workflow. |
| `add_exam_reset.py` | 3.6K | 112 | Add var_assigner_exam_reset after exam bilan to reset exam_mode to "off". |
| `add_exam_scoring_trigger.py` | 8.6K | 257 | Wire exam scoring into the chatflow. |
| `add_exam_to_chatflow.py` | 20.3K | 519 | Ajoute le système d'examen au chatflow Teacher. |
| `create_diagnostic_workflow.py` | 10.6K | 310 | Crée le workflow n8n `dify-diagnostic`. |
| `create_exam_persist_workflow.py` | 4.9K | 146 | Creates the n8n `dify-exam-persist` workflow. |
| `create_exam_scoring_workflow.py` | 17.3K | 529 | Creates the n8n `dify-exam-scoring` workflow. |
| `cron_snapshot_safety.py` | 2.9K | 91 | Cron snapshot safety net. |
| `e2e_onboarding_test.py` | 14.2K | 352 | E2E test — Full onboarding flow (new user → diagnostic → bilan). |
| `e2e_promo_test.py` | 25.9K | 602 | E2E test — Promotion B1→B2 Teacher anglais. |
| `e2e_validate.py` | 22.0K | 548 | E2E Validation — AcademIA. |
| `fix_diagnostic_trigger.py` | 5.0K | 136 | Corrige le trigger diagnostic dans le chatflow Teacher. |
| `fix_eval_ready_fallback.py` | 2.1K | 66 | Patch `code_eval_check` to handle LLM fallback. |
| `fix_exam_assigners.py` | 4.5K | 126 | Corrige le format des `var_assigner_exam` / `_exam_start`. |
| `fix_exam_assigners_v2.py` | 3.8K | 106 | Fix `var_assigner_exam` / `_start`. |
| `fix_exam_counter.py` | 2.2K | 69 | Add edge from `llm_exam` to `var_assigner` so `nb_interactions` increments. |
| `fix_exam_plan_prompt.py` | 3.8K | 99 | Fix `llm_plan_choice`: remove `[EXAM_START]` instruction. |
| `fix_exam_prompt.py` | 3.8K | 97 | Fix `llm_exam` prompt. |
| `fix_http_exam_scoring.py` | 3.1K | 89 | Fix `http_exam_scoring` node for correct Dify HTTP request format. |
| `fix_session_concepts.py` | 3.9K | 100 | Ajoute `selected_concepts` au prompt `llm_session`. |
| `fix_snapshot_during_onboarding.py` | 2.5K | 70 | Corrige `code_check` pour bloquer le snapshot pendant l'onboarding. |
| `generate_v3_training_data.py` | 13.1K | 261 | Generate ~5000 training examples for fine-tune v3. |
| `inject_concept_keys.py` | 3.7K | 124 | Injecte les `concept_keys` pour tous les niveaux anglais A1→C2. |
| `inject_curriculum_anglais.py` | 42.9K | 658 | Injection du curriculum Anglais A1→C2 — version complète et affinée. |
| `launch_finetune_v3.py` | 9.2K | 289 | Download batch output file + launch fine-tune v3. |
| `migrate_onboarding.py` | 3.4K | 105 | Migration onboarding : colonnes `profils_eleves` + FK repair `users↔eleves`. |
| `phase1b_battery_1212.py` | 7.0K | 190 | Phase 1b — Full 1212-case battery from fine-tuning training+val data. |
| `phase1b_full_battery.py` | 23.9K | 505 | Phase 1b — Full battery: 3 test cases per category (63 categories = 189 cases). |
| `phase1b_test_taxonomy.py` | 11.6K | 281 | Phase 1b — Synthetic error detection test suite. |
| `phase1b_test_v2.py` | 11.2K | 260 | Phase 1b v2 — Confirmation battery. |
| `prepare_batch_v3.py` | 9.9K | 165 | Prepare OpenAI Batch API JSONL for generating ~5000 training examples. |
| `profil_manager.py` | 4.8K | 133 | (no docstring) |
| `test_rules_coverage.py` | 3.9K | 108 | Test suite for error detection rules coverage A1–C1. |
| `update_diagnostic_workflow.py` | 10.0K | 261 | Met à jour le workflow n8n `dify-diagnostic` (v2). |
| `update_profil_get_workflow.py` | 10.6K | 303 | Met à jour le workflow n8n `dify-profil-get` (v5). |
| `update_snapshot_workflow.py` | 20.7K | 555 | Met à jour le workflow n8n `dify-snapshot`. |
| `update_teacher_chatflow.py` | 110.8K | 2097 | Source de vérité Teacher v14 — Cooldown module échoué (#5) + Mode révision lacunes (#6). |
| `update_teacher_onboarding.py` | 9.8K | 257 | Modifie le chatflow Teacher pour le diagnostic CECRL. |
| `validate_14_categories.py` | 9.0K | 211 | Validate 14 categories — calls Groq directly (bypasses LiteLLM cooldown). |

`__pycache__/` contains three compiled files (`phase1b_full_battery`, `phase1b_test_v2`, `validate_14_categories`).

---

## 4. `/opt/litellm`

### 4.1 Directory structure

```
/opt/litellm/
└── config.yaml           (10 038 bytes, mod 2026-04-15 10:12)
```
Total size: 16K (one file only).

### 4.2 `config.yaml` — sections present

Top-level keys (exactly three):
- `general_settings`
- `router_settings`
- `model_list`

`litellm_settings` is **absent**.

### 4.3 Model count

- **Active models: 10** (lines starting with `- model_name:`)
- **Commented models: 11** (lines starting with `# - model_name:`)

Active model names (order of appearance):
1. `gpt-4o-mini`
2. `ft:gpt-4o-mini-2024-07-18:personal:academie-errors-v2:DTurinhs`
3. `ft:gpt-4o-mini-2024-07-18:personal:academie-errors-v3:DU6GUv6v`
4. `groq-standard` (2 entries — fallback replicas)
5. `groq-snapshot` (2 entries — fallback replicas)
6. `groq-qwen`
7. `ollama-cloud`
8. `mistral-small`

Commented-out models: groq-standard (×3), groq-snapshot (×3), groq-qwen, mistral-small (×4) — left for rollback/test reference.

---

## 5. `/opt/academia-shared`

### 5.1 Tree

```
/opt/academia-shared/
├── scripts/
│   ├── pg-backup.sh       → /root/sinse-tools/pg-backup (symlink)
│   ├── restic-backup.sh   → /root/sinse-tools/restic-backup (symlink)
│   └── smoke-test.sh      → /root/sinse-tools/smoke-test (symlink)
└── secrets/
    (see below — filenames only)
```

### 5.2 `secrets/` — filenames only (no content)

| File | Size (bytes) | Mode |
|---|---:|---|
| `dify-admin-key` | 40 | 0600 sinse:sinse |
| `dify-teacher-key` | 29 | 0600 sinse:sinse |
| `groq-key-2` | 57 | 0600 sinse:sinse |
| `jwt-refresh-secret` | 65 | 0600 sinse:sinse |
| `jwt-secret` | 65 | 0600 sinse:sinse |
| `n8n-encryption-key` | 49 | 0600 sinse:sinse |
| `ollama-cloud-key` | 58 | 0600 sinse:sinse |
| `pg-password` | 33 | 0600 sinse:sinse |
| `restic-passphrase` | 65 | 0600 sinse:sinse |

Contents intentionally **not** scanned.

### 5.3 `curriculum*.yaml`

No `curriculum*.yaml` file is present under `/opt/academia-shared` or anywhere else on the host. The curriculum source of truth is `/opt/academia/scripts/inject_curriculum_anglais.py` (42.9K, 658 lines) which injects curriculum into Dify via API.

---

## 6. `/mnt/cosmos-data`

### 6.1 Tree (level 2)

```
/mnt/cosmos-data/
├── backups/
│   └── postgres/
├── cloud-files/
├── cosmos-config/
│   └── snapraid/
├── dify/
│   └── storage/
├── lost+found/
├── media/
│   ├── downloads/
│   ├── films/
│   └── series/
├── n8n/
├── ollama/
├── postgres/            (19 subfolders — standard PostgreSQL cluster layout)
│   ├── base/
│   ├── global/
│   ├── pg_wal/
│   ├── pg_commit_ts/, pg_dynshmem/, pg_logical/, pg_multixact/,
│   │   pg_notify/, pg_replslot/, pg_serial/, pg_snapshots/,
│   │   pg_stat/, pg_stat_tmp/, pg_subtrans/, pg_tblspc/,
│   │   pg_twophase/, pg_xact/
└── qdrant/
    ├── aliases/
    └── collections/
```

### 6.2 Sizes (`du -h`)

| Path | Size |
|---|---|
| `cloud-files` | 4.0K |
| `n8n` | 4.0K |
| `ollama` | 4.0K |
| `dify` | 8.0K |
| `lost+found` | 16K |
| `qdrant` | 20K |
| `media` | 36K |
| `cosmos-config` | 17M |
| `postgres` | 305M |
| `backups` | **1.5G** |

### 6.3 `backups/postgres/` inventory

Layout: hourly dumps at root + rotation folders `daily/`, `weekly/`, `monthly/`.

- **Hourly dumps (root): 24 files** (rolling 24h window), all named `academie_db_YYYY-MM-DD_HHMM.sql.gz`.
- **Daily dumps (`daily/`): 3 files** — 2026-04-13, 04-14, 04-15.
- **Weekly dumps (`weekly/`): 0 files** (folder present, empty).
- **Monthly dumps (`monthly/`): 0 files** (folder present, empty).
- **Total dumps: 27**.
- **Oldest dump**: `daily/academie_db_2026-04-13_0000.sql.gz` (2026-04-13 00:00).
- **Most recent dump**: `academie_db_2026-04-15_1200.sql.gz` (2026-04-15 12:00).
- **Typical dump size**: ~56–58 MB each.
- **Size of `daily/`**: 132M.

---

## 7. Systemd services & cron

### 7.1 Running services (`systemctl list-units --type=service --state=running`, filtered for academie/docker/related)

| Unit | State | Description |
|---|---|---|
| `docker.service` | loaded active running | Docker Application Container Engine |
| `nginx.service` | loaded active running | A high performance web server and a reverse proxy server |

There is **no** dedicated `academie.service`, `litellm.service`, or `n8n.service` systemd unit — all workloads run inside Docker.

### 7.2 Running Docker containers

| Container | Image | Uptime |
|---|---|---|
| `academie-frontend` | webapp-academie-frontend | Up 2h (healthy) |
| `academie-api` | webapp-academie-api | Up 2h (healthy) |
| `cosmos-mongo-KIo` | mongo:8 | Up 8h |
| `dify-worker` | langgenius/dify-api:latest | Up 21h |
| `dify-api` | langgenius/dify-api:latest | Up 21h |
| `dify-web` | langgenius/dify-web:latest | Up 8d |
| `n8n-academie` | n8nio/n8n | Up 22h |
| `cosmos-server` | azukaar/cosmos-server:latest | Up 8d |
| `dify-sandbox` | langgenius/dify-sandbox:latest | Up 10d |
| `litellm-proxy` | ghcr.io/berriai/litellm:main-latest | Up 2h |
| `dify-plugin-daemon` | langgenius/dify-plugin-daemon:0.5.3-local | Up 10d |
| `redis-academie` | redis:7-alpine | Up 10d |
| `postgres-academie` | postgres:16 | Up 10d |

### 7.3 Docker networks

| Network | Driver |
|---|---|
| `academie-net-bridge` | bridge (external, shared by compose) |
| `bridge` | bridge (default) |
| `host` | host |
| `none` | null |

### 7.4 Cron jobs

**Root crontab (`crontab -l`):**
```
0 * * * * /usr/bin/python3 /opt/academia/scripts/cron_snapshot_safety.py >> /var/log/academie-snapshot-cron.log 2>&1
```
Hourly snapshot safety net script.

**`/etc/cron.d/` — AcademIA-related (3 files):**

| File | Schedule | Command |
|---|---|---|
| `pg-backup` | `0 * * * *` (hourly) | `/opt/academia-shared/scripts/pg-backup.sh >> /var/log/pg-backup.log` |
| `restic-backup` | `30 3 * * *` (daily 03:30) | `/opt/academia-shared/scripts/restic-backup.sh >> /var/log/restic-backup.log` |
| `smoke-monitor` | `*/15 * * * *` (every 15 min) | `/root/sinse-tools/smoke-test --quick` → appends to `/var/log/smoke-alert.log` on FAILED |

**Other cron directories (system defaults only, no academie content):**
- `/etc/cron.daily/`: `apt-compat`, `dpkg`, `exim4-base`, `logrotate`, `man-db`, `rkhunter`.
- `/etc/cron.weekly/`: `man-db`, `rkhunter`.
- `/etc/cron.hourly/`, `/etc/cron.monthly/`, `/etc/cron.yearly/`: empty (placeholder only).

---

## 8. Environment files

Single env file found under `/opt/academia`:

- **`/opt/academia/webapp/.env`** — variable names only (values redacted):

| Variable |
|---|
| `DATABASE_URL` |
| `DIFY_KEY_TEACHER` |
| `JWT_SECRET_KEY` |
| `JWT_REFRESH_SECRET` |

No other `.env`, `.env.local`, `.env.production`, etc. exist anywhere under `/opt/academia` (confirmed via `find -maxdepth 3 -name ".env*"`).

---

## 9. Nginx

### 9.1 Location

Nginx runs on **host** (not in Docker): `nginx.service` systemd unit, config at `/etc/nginx/`.

```
/etc/nginx/
├── conf.d/               (empty)
├── fastcgi.conf, fastcgi_params, koi-utf, koi-win, mime.types  (defaults)
├── modules-available/
├── sites-available/      (not scanned — holds dify)
└── sites-enabled/
    └── dify              → /etc/nginx/sites-available/dify (symlink)
```

### 9.2 `sites-enabled/dify` — server blocks

One file, two `server { ... }` blocks, both listening on **port 8080** (HTTP → Cloudflare tunnel terminates TLS upstream).

**Block 1 — `dify.petit-pont.com`** (upstream: Dify containers on host ports):

| Location | Upstream | Notes |
|---|---|---|
| `/files/` | `http://127.0.0.1:5001` | `client_max_body_size 20M` |
| `/console/api` | `http://localhost:5001` | |
| `/api` | `http://127.0.0.1:5001` | |
| `/` (default) | `http://127.0.0.1:3000` | Dify web UI |

**Block 2 — `academia.petit-pont.com`** (upstream: AcademIA frontend on `127.0.0.1:3001`):

Security headers applied globally (block-level `add_header`):
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' https://flagcdn.com data:; connect-src 'self'; frame-ancestors 'none';`
- HSTS handled by Cloudflare.

Location blocks (in order — order matters because of regex precedence):

| Location pattern | Upstream | Behaviour |
|---|---|---|
| `~* (manifest\.json\|sw\.js)$` | `http://127.0.0.1:3001` | `expires -1`, `Cache-Control: no-cache, no-store, must-revalidate` |
| `~* \.(png\|jpg\|jpeg\|gif\|ico\|svg\|woff2?\|ttf\|eot\|css\|js)$` | `http://127.0.0.1:3001` | `expires 7d`, `Cache-Control: public, max-age=604800, immutable` |
| `/` | `http://127.0.0.1:3001` | HTTP/1.1, WebSocket upgrade supported, `proxy_buffering off`, `proxy_read_timeout 120s` |

All three proxies forward `Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`.

---

## 10. Git state

### 10.1 `/opt/academia`

- **Branch**: `main`
- **Latest commit**: `b7d5ed6 [feat] centralized token tracking — LiteLLM SpendLogs as truth + dual-tracking with tiktoken for sub-second auto-switch`
- **Modified (not committed)**:
  - `M .claude/commands/handoff.md`
  - `M .claude/commands/pickup.md`
  - `M .claude/settings.local.json`
- **Untracked**: `.claude/scheduled_tasks.lock`

### 10.2 `/root/sinse-workspace` (archived as `/root/sinse-archive-2026-pre-vault/` post-Phase 3 vault migration 2026-04-25)

- **Branch**: `main`
- **Latest commit**: `1ab08d8 [docs] Session 12 handoff — token tracking centralized via LiteLLM`
- **Modified / renamed (not committed)**:
  - `M AGENTS.md`
  - `R projects/academie-ia/docs/dify-teacher.md → _legacy/dify-teacher.md`
  - `R projects/academie-ia/docs/gotchas.md → _legacy/gotchas.md`
  - `R projects/academie-ia/docs/infra.md → _legacy/infra.md`
  - `R projects/academie-ia/docs/n8n-workflows.md → _legacy/n8n-workflows.md`
  - `R projects/academie-ia/docs/pedagogy.md → _legacy/pedagogy.md`
  - `R projects/academie-ia/docs/webapp.md → _legacy/webapp.md`
  - `D slash-commands/handoff.md`
  - `D slash-commands/pickup.md`
- **Untracked** (38 files):
  - `projects/academie-ia/docs/00-project/` (new tree)
  - `projects/academie-ia/docs/01-pedagogy/`
  - `projects/academie-ia/docs/02-architecture/`
  - `projects/academie-ia/docs/03-domain/`
  - `projects/academie-ia/docs/04-infra/`
  - `projects/academie-ia/docs/05-decisions/`
  - `projects/academie-ia/docs/99-runbooks/`
  - `projects/academie-ia/docs/INDEX.md`
  - `projects/academie-ia/docs/README.md`
  - `projects/academie-ia/docs/_legacy/README.md`
  - 5 archived merge-requests under `projects/academie-ia/merge-requests/archive/`
- **Summary**: 24 lines in `git status -s` (incl. renames), 38 paths untracked.

---

## Appendix A — Top-level `.claude/` in `/opt/academia`

```
/opt/academia/.claude/
├── commands/
│   ├── handoff.md
│   └── pickup.md
├── scheduled_tasks.lock        (untracked)
└── settings.local.json         (modified)
```

## Appendix B — Existing `04-infra/` docs (neighbour files)

Neighbour docs in `/opt/academia/docs/04-infra/` (moved here from `/root/sinse-workspace/projects/academie-ia/docs/04-infra/` during Phase 3 vault migration 2026-04-25):
- `backup.md`
- `credentials.md`
- `deployment.md`
- `monitoring.md`

This `filesystem-scan.md` is intended to complement those.
