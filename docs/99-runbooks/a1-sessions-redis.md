# A1 — Sessions opaques Redis + cookies HttpOnly + CSRF (refactor 2026-H2 Phase A)

**Status** : code livré Session 46 ; à activer (rebuild + re-login)
**Last updated** : 2026-04-23
**Related** : [`docs/05-decisions/ADR-001-refactor-complete-2026-H2.md`](../05-decisions/ADR-001-refactor-complete-2026-H2.md)

Suppression de la vulnérabilité XSS structurelle (JWT en localStorage) en migrant vers sessions opaques Redis + cookies `__Host-as_session` HttpOnly + CSRF double-submit.

## Code livré

### Backend

- **`webapp/backend/requirements.txt`** : `+ redis==5.2.0`
- **`webapp/backend/app/sessions.py`** (nouveau) : Redis store
  - `create_session(user_id, username, ip, ua) -> (token, csrf_token)` — 48-byte token URL-safe + 32-byte CSRF, TTL 7j
  - `get_session(token)` — sliding TTL refresh à chaque appel
  - `delete_session(token)` / `delete_session_by_short_id(uid, short)` / `delete_all_sessions_for_user(uid, except_token)`
  - `list_sessions_for_user(uid, current_token)` — purge stale entries
- **`webapp/backend/app/auth.py`** :
  - JWT helpers supprimés (`create_access_token`, `decode_token`, etc.)
  - Constants `COOKIE_SESSION = "__Host-as_session"`, `COOKIE_CSRF = "csrf_token"`
  - `get_current_user(request)` — lit cookie, lookup Redis, charge user PG, expose `_session_token`
  - `require_admin`, `hash_password`, `verify_password`, `verify_and_rehash` (A2) conservés
- **`webapp/backend/app/main.py`** :
  - Lifespan ouvre/ferme Redis pool
  - Middleware `csrf_protect` : pour POST/PUT/PATCH/DELETE hors whitelist (`/auth/login`, `/auth/login-mfa`, `/csp-report`, `/telemetry/onboarding-event`), exige header `X-CSRF-Token` == cookie `csrf_token`, sinon 403
  - CORS `allow_headers` mis à jour `["Content-Type", "X-CSRF-Token"]` (retire Authorization)
- **`webapp/backend/app/routers/auth_router.py`** :
  - `/login` + `/login-mfa` : sur succès, `create_session()` + `set_cookie()` les 2 cookies (`__Host-` prefix force secure+path=/+no domain), retourne `{user: {...}}` (no tokens body)
  - `/logout` (nouveau) : delete Redis session + clear cookies (best-effort, no auth required)
  - `/logout-all-sessions` (nouveau, auth required) : `delete_all_sessions_for_user()` + clear cookies + rate-limit 5/min/IP
  - `/refresh` **supprimé** (sliding TTL Redis remplace)
- **`webapp/backend/app/routers/settings_router.py`** :
  - `/me/sessions` GET → `list_sessions_for_user()` Redis-backed, retourne `id` (sha1[:16]), ip, user_agent, dates, `is_current`
  - `/me/sessions/{id}` DELETE → `delete_session_by_short_id()` (lookup via SCAN du reverse index)
  - `/me/sessions` DELETE → `delete_all_sessions_for_user(except_token=current)` (laisse session courante)

### Frontend

- **`webapp/frontend/src/lib/api.ts`** :
  - Suppression complète de `token`, `refreshToken`, `setToken`, `setRefreshToken`, `loadToken`, `tryRefresh`
  - `fetch()` ajoute `credentials: 'include'` + lit cookie `csrf_token` (helper `getCookie`) → injecte `X-CSRF-Token` sur POST/PUT/PATCH/DELETE
  - `login()` retourne `{user}` ou `{mfa_required, username}` sans toucher au localStorage
  - `logout()` (modifié) : POST `/auth/logout` (best-effort) + redirect `/login`
  - `logoutAllSessions()` (nouveau) : POST `/auth/logout-all-sessions` + redirect `/login`
- **`webapp/frontend/src/hooks.server.ts`** :
  - Proxy `/api/*` forwarde `cookie` + `x-csrf-token` (whitelist élargie)
  - Forward explicite `Set-Cookie` via `response.headers.getSetCookie()` (Node 20+) pour éviter consolidation comma-joined cassante

## Activation

```bash
cd /opt/academie/webapp
docker compose -f docker-compose.webapp.yml build academie-api academie-frontend
docker compose -f docker-compose.webapp.yml up -d --force-recreate academie-api academie-frontend
```

## Tests

### Smoke test backend (1 commande)

```bash
USERNAME=sinse PASSWORD='<ton_password>' TOTP='<6_digits_aegis>' \
  bash /opt/academie/scripts/sprint8/05_test_sessions_redis.sh
```

Couvre : login (+ MFA si enrolled) → cookies posées → /auth/me OK → CSRF rejet sans header → CSRF accept avec header → /me/sessions list → Redis state → logout → /auth/me 401 → Redis purge.

### Smoke test browser (toi)

1. **Logout actuel** (ou clear cookies + localStorage manuellement)
2. Re-login via UI : password + Aegis TOTP
3. **Devtools → Application → Cookies** :
   - `__Host-as_session` (HttpOnly ✅, Secure ✅, SameSite Lax)
   - `csrf_token` (HttpOnly ❌, Secure ✅) — JS doit pouvoir le lire
4. **Devtools → Application → Local Storage** : aucune clé `token` ou `refresh_token`
5. **Network tab** sur une mutation (changer profile par ex.) :
   - Request headers : `X-CSRF-Token: <valeur csrf_token>`
   - Cookie envoyé : `__Host-as_session=...; csrf_token=...`
6. Test `/settings/security` → "Désactiver TOTP" doit demander password (POST CSRF-protégé)
7. Logout via menu → cookies clear → redirect /login

### Vérif Redis

```bash
docker exec redis-academie redis-cli KEYS 'session:*'
docker exec redis-academie redis-cli KEYS 'user_sessions:*'
docker exec redis-academie redis-cli HGETALL session:<token>
docker exec redis-academie redis-cli TTL session:<token>
```

TTL doit être ~604800 (7j) après login, et se rafraîchir à chaque request /auth/me.

## Rollback rapide

```bash
cd /opt/academie
git revert <a1_commit_sha>
cd webapp && docker compose -f docker-compose.webapp.yml up -d --build academie-api academie-frontend
```

L'environnement JWT (`JWT_SECRET_KEY`, `JWT_REFRESH_SECRET`) reste en place dans `webapp/.env.sops`, et la table `active_sessions` PG reste présente — le revert restaure le mode JWT immédiatement.

## Risques + comportements observés

- **Lockout admin si bug middleware** : la migration force tous les users à se re-logger (les sessions JWT pré-A1 ne sont plus reconnues). Si CSRF middleware bug, mutations bloquées 403. Mitigation : smoke test backend avant rebuild prod.
- **Cookie `__Host-` prefix requires HTTPS** : derrière Cloudflare le `X-Forwarded-Proto: https` est présent ; FastAPI fait confiance via Starlette. En localhost HTTP pur, le cookie n'est pas posé par le browser. Test smoke contourne via curl.
- **Sessions perdues sur Docker restart** : Redis 7.4.8 a-t-il `appendonly yes` ou `save` actif ? À auditer (`docker exec redis-academie redis-cli CONFIG GET appendonly`). Si non, restart container = tous users déconnectés. Pas bloquant alpha.
- **CSRF whitelist** : login + login-mfa + csp-report + telemetry exempts. Tout ajout futur de mutation un-authed nécessite ajout explicite à `_CSRF_EXEMPT_PATHS` dans `main.py`.
- **PG `active_sessions` table devient orpheline** : aucune écriture désormais, lectures redirigées vers Redis. À DROP en A1-cleanup après validation 1 semaine.

## Cleanup post-validation (A1-cleanup, ~1 semaine après)

- DROP TABLE `active_sessions` (migration `scripts/sprint8/06_drop_active_sessions.sql`)
- Retirer `JWT_SECRET_KEY` + `JWT_REFRESH_SECRET` de `webapp/.env.sops`
- Retirer `python-jose` de `requirements.txt` (plus utilisé)
- Retirer `RefreshRequest` + `TokenResponse` de `models.py` si plus référencés

## Intégration avec autres items Phase A

- **A2 Argon2id** : intact, le rehash continue à se faire en login
- **A4 MFA TOTP** : intact, juste le retour de tokens devient `set_cookie()`
- **A3 CSP** : aucun impact, headers cross-cutting restent
- **A5 PII scrubber** (à venir) : middleware se branchera après csrf_protect, ordre d'exécution OK
- **A6 RGPD DSAR** : `delete_all_sessions_for_user` réutilisable pour le flow "delete account"
