---
summary: "SvelteKit frontend, FastAPI backend, user auth, PWA, streaming chat"
read_when: "Modifying webapp frontend/backend, user auth, chat, dashboard, or stats"
---

# Webapp — AcademIA

## Architecture

```
SvelteKit (hooks.server.ts) proxy /api/* → FastAPI:8000
    FastAPI → PostgreSQL (profiles, scores, streaks, XP)
    FastAPI → Dify API (chat streaming SSE)
    FastAPI → rate limiter in-memory (per IP)
    FastAPI → structured logging (timestamps + duration)
```

## Frontend (SvelteKit)

- Port: 3001
- PWA enabled (service worker + offline)
- Pages: /login, /dashboard, /chat, /stats/concepts, /changelog, /settings

### Key components
- Header.svelte: CHANGELOG_VERSION constant (bump for "New" badge)
- Chat: SSE streaming from Dify via FastAPI proxy
- Dashboard: streaks, XP, level, avatar
- Stats: concept confidence scores (0-100), clickable tips

### Changelog rule
When adding user-visible features:
1. Update /opt/academia/webapp/frontend/src/routes/changelog/+page.svelte
2. Bump CHANGELOG_VERSION in Header.svelte

## Backend (FastAPI)

- Port: 8000
- Routers: auth, profile, chat, settings
- Auth: simple username/password, session-based
- Dify proxy: /api/chat → Dify API with SSE streaming

## Users

| ID | Username | Role |
|----|----------|------|
| 1 | sinse | Admin |
| 2 | nico | User |
| 3 | julien | User |
| 4 | noz_project | User |
| 5 | waigosan | User |
| 6 | 0tha | User |

Passwords stored securely — not in version control. See Sinse directly for credentials.
