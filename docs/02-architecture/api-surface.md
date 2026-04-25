---
title: API Surface (FastAPI + SvelteKit)
status: authoritative
last_reviewed: 2026-04-15
---

# API Surface

> Inventaire complet de tous les endpoints FastAPI + routes SvelteKit. Mise à jour au scan 2026-04-15.

## FastAPI — 36 endpoints via 6 routers

Container `academie-api`, port `127.0.0.1:8000`.

### auth_router — 4 endpoints (`/api/auth/*`)

Fichier : `/opt/academie/webapp/backend/app/routers/auth_router.py`

| Méthode | Path | Auth | RL | Description |
|---|---|---|---|---|
| POST | `/api/auth/login` | — | 5/60s | Login username/password → access (30min) + refresh (7j) tokens JWT HS256. Auto-link `eleve_id`. |
| POST | `/api/auth/refresh` | — | 10/60s | Échange refresh token contre nouvelle paire access+refresh |
| GET | `/api/auth/me` | ✅ | — | Retourne `UserResponse` du user courant |
| POST | `/api/auth/users` | admin | — | Créer user + eleve (bcrypt hash) |

### profile_router — 10 endpoints

Fichier : `/opt/academie/webapp/backend/app/routers/profile_router.py` (692 lignes)

| Méthode | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/profile/{domain}` | ✅ | Profil complet : niveau, scores concept, progress_pct, dernier examen, plan_sessions. Derivation `scores_confiance` (priority n8n) avec fallback error-profile. |
| GET | `/api/streak` | ✅ | current/longest streak + total sessions |
| GET | `/api/stats/weekly` | ✅ | Sessions/concepts/minutes des 7 derniers jours |
| GET | `/api/me/concepts` | ✅ | Scores par concept groupés par module + insights + `CONCEPT_TIPS` (20 concepts hardcodés) |
| GET | `/api/me/history` | ✅ | Sessions `snapshots_session` (default limit=20) |
| GET | `/api/me/exams` | ✅ | `current_exam`, `last_exam`, `nb_exams` |
| GET | `/api/me/xp` | ✅ | Total XP + rank (6 paliers: Debutant/Explorateur 200/Apprenti 500/Praticien 1500/Expert 5000/Maitre 15000) + 10 derniers logs |
| GET | `/api/me/xp-history` | ✅ | XP cumulatif 30 jours |
| GET | `/api/me/heatmap` | ✅ | Activité 180j (sessions + minutes par jour) |
| GET | `/api/me/badges` | ✅ | 9 badges (`perseverant/infatigable/premier_exam/promotion/perfectionniste/assidu/centurion/explorateur_xp/expert_xp`) + progression |

### chat_router — 4 endpoints

Fichier : `/opt/academie/webapp/backend/app/routers/chat_router.py`

| Méthode | Path | Auth | RL | Description |
|---|---|---|---|---|
| POST | `/api/chat/send` | ✅ | 30/60s | Stream SSE via Dify `/v1/chat-messages`. Injecte `minutes_since_last`, `turn_response_secs`, `error_feedback` (rules + tolerance_matrix), `repeated_errors` (7j). Track tokens gpt-4o-mini. Auto-switch `groq-standard` si budget > 1.5M tokens/jour. Update streak + session + XP (50 à 10 msg). |
| GET | `/api/chat/token-usage` | ✅ | — | Usage quotidien gpt-4o-mini (source `LiteLLM_SpendLogs` sinon estimate tiktoken) + breakdown par modèle + model courant |
| GET | `/api/chat/conversations` | ✅ | — | Liste conversations Dify (limit=20) |
| GET | `/api/chat/messages` | ✅ | — | Messages d'une conversation (limit=100) |

Keys agents : `DIFY_KEY_TEACHER` seul actif. `DIFY_API_URL` défault `http://dify-api:5001/v1`.

### settings_router — 10 endpoints

Fichier : `/opt/academie/webapp/backend/app/routers/settings_router.py`

| Méthode | Path | Auth | RL | Description |
|---|---|---|---|---|
| PATCH | `/api/me/profile` | ✅ | — | display_name, avatar_color, theme, daily_goal_minutes (5-120), centres_interet, style_correction |
| PATCH | `/api/me/mode` | ✅ | — | Change `mode_apprentissage` (structure/libre) |
| POST | `/api/me/password` | ✅ | 5/300s | Change password (verify current + bcrypt) |
| GET | `/api/me/settings` | ✅ | — | Settings complets (user + personnalite JSONB) |
| GET | `/api/me/sessions` | ✅ | — | Liste active_sessions |
| DELETE | `/api/me/sessions/{session_id}` | ✅ | — | Revoke une session |
| DELETE | `/api/me/sessions` | ✅ | — | Revoke toutes sessions |
| GET | `/api/me/recommendation` | ✅ | — | Recommandation contextuelle (start/comeback si ≥3j absent) |
| GET | `/api/me/daily-progress` | ✅ | — | Temps pratique aujourd'hui vs objectif |
| GET | `/api/me/weekly-recap` | ✅ | — | Sessions/minutes/XP/streak/concepts de la semaine |

### error_analysis_router — 3 endpoints

Fichier : `/opt/academie/webapp/backend/app/routers/error_analysis_router.py`

| Méthode | Path | Auth | Description |
|---|---|---|---|
| POST | `/internal/analyze-errors` | `X-Internal-Token` | **Appelé par n8n `dify-snapshot`**. Pipeline 2 couches : rules déterministes + LLM monolithique (ft:gpt-4o-mini-v3). Dedup par turn+code. Update `error_exam_eligible`. |
| GET | `/api/student/{username}/error-profile` | admin | Profil d'erreurs détaillé d'un élève |
| GET | `/api/error-profile/{domain}` | ✅ | Son propre profil d'erreurs |

### admin_router — 4 endpoints

Fichier : `/opt/academie/webapp/backend/app/routers/admin_router.py`

| Méthode | Path | Auth | Description |
|---|---|---|---|
| POST | `/internal/exam-result` | `X-Internal-Token` | XP +200 si exam pass, +500 si promotion |
| GET | `/api/admin/users` | admin | Liste users + stats (niveau, streak, XP, online <15min) |
| POST | `/api/admin/reset-profile/{username}` | admin | Wipe complet profil + error_log + snapshots + xp_log + streaks + user_sessions + new dify UUID |
| DELETE | `/api/admin/users/{user_id}` | admin | Suppression totale user + eleve + relations |

### Autre endpoint

| Méthode | Path | Description |
|---|---|---|
| GET | `/api/health` | Healthcheck `SELECT 1` → `{"status":"ok/degraded","service":"academie-api","db":"connected/disconnected"}` |

### Middlewares et infrastructure transverse

- **CORS** : origins `http://localhost:3001`, `http://localhost:5173`, `https://academie.petit-pont.com`. Credentials: true. Methods GET/POST/PATCH/DELETE/OPTIONS.
- **Middleware `security_headers`** : `X-Content-Type-Options=nosniff`, `X-Frame-Options=DENY`, `Referrer-Policy=strict-origin-when-cross-origin`
- **Middleware `log_requests`** : log méthode/path/status/durée (sauf `/api/health`)
- **Rate limiter** : in-memory token bucket par IP (respect `X-Forwarded-For`), cleanup task toutes les 60s, fenêtre 300s
- **Auth** : HTTPBearer, JWT HS256 (access 30min/refresh 7j), `get_current_user()` décode + lookup user + update `last_seen_at` (debounced 5min)
- **Pools DB** : asyncpg 2 pools (academie_db min:2 max:10, litellm_db min:1 max:4)

### Modules error_taxonomy

Les routers appellent `webapp/backend/app/error_taxonomy/` :

| Fichier | Lignes | Rôle |
|---|---|---|
| `categories.py` | 55 | 57 codes + 6 fusions. `is_valid_code()`. |
| `differ.py` | 134 | `extract_edits()` alignement token-level |
| `llm.py` | 303 | Prompt monolithique → LiteLLM `ft:gpt-4o-mini-v3`. Tenacity retry (2 essais). |
| `rules.py` | 754 | `detect_errors()` déterministe 98% coverage A1-C1. Mapping `ERROR_CODE_TO_FAMILY` (57→11 familles). |
| `scoring.py` | 356 | `compute_error_profile()` — agrège + tolerance_matrix + progression |

Config : `webapp/backend/app/config/tolerance_matrix.yaml`.

---

## SvelteKit Frontend — 12 routes, 17 components

Container `academie-frontend`, port `127.0.0.1:3001`. **Svelte 5** (runes). Tailwind. Dark theme.

### hooks.server.ts

Proxy `/api/*` vers `API_BACKEND` (env, défault `http://academie-api:8000`). Forwarde `content-type`, `authorization`, `accept`. SSE passthrough (stream body + headers).

**Pas d'auth guard SSR** — auth côté client via `api.loadToken()` dans `+layout.svelte`.

### Routes

| Route | Lignes | Guard | API calls principaux |
|---|---|---|---|
| `/` | — | redirect `/login` if no token | `me()`, `getProfile('anglais')`, `getWeeklyStats()`, `getConcepts('anglais')` |
| `/login` | 91 | public | `login(username, password)` |
| `/legal` | 73 | public | — (static) |
| `/changelog` | 123 | layout-level | — (hardcoded entries) |
| `/admin` | 279 | `is_admin` | `adminGetUsers`, `adminCreateUser`, `adminResetProfile`, `adminDeleteUser`, `getTokenUsage` |
| `/profile` | 324 | layout-level | `getSettings`, `getActiveSessions`, `updateProfile`, `changePassword`, `revokeSession`, `revokeAllSessions`, `changeMode` |
| `/stats` | 222 | layout-level | `getConcepts`, `getExams`, `getXp`, `getBadges`, `getXpHistory` |
| `/stats/concepts` | 208 | layout-level | `getConcepts(domain)` |
| `/chat/[agent]` | 547 | layout-level | `getProfile`, `getConversations`, `getChatMessages`, `loadToken`, `changeMode` + **SSE direct fetch `/api/chat/send`** |

### Root layout (`routes/+layout.svelte`)

- Charge `api.me()` + streak + XP + daily progress au mount
- Redirige `/login` si fail
- **Listeners window** : `xp-update`, `streak-milestone` (7/14/30/50/100), `rate-limited`, `badge-unlock`, `profile-updated`
- Pages publiques (pas de layout chrome) : `/login`, `/legal`
- Components globaux : Toasts, ConnectionIndicator, CommandPalette, KeyboardShortcuts, CelebrationModal
- Sidebar + Header si user ready

### $lib/ — 17 components

**Components racine** :
- `ActivityHeatmap.svelte`
- `AgentFlag.svelte`
- `CelebrationModal.svelte`
- `CommandPalette.svelte`
- `ConfirmDialog.svelte`
- `ConnectionIndicator.svelte`
- `Header.svelte`
- `KeyboardShortcuts.svelte`
- `ProgressionGraph.svelte`
- `Sidebar.svelte`
- `SkillTree.svelte` (395 lignes)
- `Toasts.svelte`
- `Tooltip.svelte`
- `WeeklyRecap.svelte`

**Components chat** :
- `chat/ChatBubble.svelte`
- `chat/ChatInput.svelte`
- `chat/TypingIndicator.svelte`

**Stores** :
- `stores/auth.ts` — writable user/token (peu utilisé, ApiClient gère)
- `stores/theme.ts` — getTheme/setTheme/toggleTheme/initTheme/onThemeChange
- `stores/user.ts` — writable userAppearance
- `stores/toasts.ts` — Custom toast system (Set listeners)

**Utils** :
- `api.ts` (329 lignes) — singleton `ApiClient` : token management (localStorage), auto-refresh sur 401 (déduplication via `this.refreshing`), event dispatch `rate-limited` sur 429, redirect `/login` si refresh fail
- `config.ts` — liste 7 agents (teacher actif + 6 coming soon)

### Sidebar nav (hardcoded)

`/`, `/chat/teacher`, `/stats`, `/profile` + `/admin` si admin + liste des 7 agents (certains disabled).

---

## Healthchecks cross-services (snapshot 2026-04-15)

| URL | HTTP | Temps |
|---|---|---|
| `http://localhost:3001/` | 200 | 2.2 ms |
| `http://localhost:8000/api/health` | 200 | 1.8 ms |
| `http://localhost:4000/health/readiness` | 200 | 6.2 ms |
| `http://localhost:5001/health` | 200 | 3.3 ms |
| `http://localhost:5678/healthz` | 200 | 2.5 ms |
| `http://localhost:8080/` (nginx, Host: academie.petit-pont.com) | 200 | 2.1 ms |

Tous services **healthy**.

## Références

- [overview.md](overview.md) — contexte stack
- [integrations.md](integrations.md) — n8n workflows, Dify chatflows, LiteLLM, nginx
- [data-model.md](data-model.md) — schémas DB consommés
- Code : `/opt/academie/webapp/backend/app/`, `/opt/academie/webapp/frontend/src/`
