# A4 — MFA TOTP (refactor 2026-H2 Phase A)

**Status** : A4a backend livré, admin (sinse) à enrôler immédiatement via CLI. UI users en /settings = A4b session suivante.
**Last updated** : 2026-04-23
**Related** : [`docs/05-decisions/ADR-001-refactor-complete-2026-H2.md`](../05-decisions/ADR-001-refactor-complete-2026-H2.md)

TOTP RFC 6238 (Google Authenticator / 1Password / Aegis / Bitwarden compatible). Phase A4a verrouille en priorité l'admin (Sinse) — compte le plus critique du système. WebAuthn/Passkeys = phase 2 post-beta.

## Code livré (Session 46 A4a)

### Backend
- **`webapp/backend/requirements.txt`** : `pyotp==2.10.1` + `qrcode[pil]==9.3.0`
- **`webapp/backend/app/totp.py`** (nouveau) :
  - `generate_secret()` — base32 RFC 4226, 160 bits
  - `provisioning_uri(secret, username)` — `otpauth://totp/AcademIA:<user>?...`
  - `qr_data_url(uri)` — PNG base64 data URL
  - `verify_code(secret, code)` — RFC 6238, ±30s tolerance
  - `generate_recovery_codes()` — 10 codes de 10 chars base32 (50 bits entropy chacun)
  - `hash_recovery_codes(codes)` — argon2id (même CryptContext que passwords)
  - `verify_and_consume_recovery_code(stored, code)` — verify + nullify la position consommée pour empêcher reuse
- **`webapp/backend/app/routers/security_router.py`** — endpoints :
  - `GET  /api/security/totp/status` — enrolled? + recovery codes restants
  - `POST /api/security/totp/enroll-start` — secret + QR + URI
  - `POST /api/security/totp/enroll-confirm` — verify 1er code → save → return 10 recovery codes plaintext (à noter par l'user)
  - `POST /api/security/totp/disable` — require password + (TOTP code OR recovery code)
- **`webapp/backend/app/routers/auth_router.py`** :
  - `POST /api/auth/login` : si user a TOTP enrolled → retourne `{"mfa_required": true, "username": ...}` (PAS de tokens)
  - `POST /api/auth/login-mfa` (nouveau) : body `{username, password, code}` → re-verify password + TOTP/recovery → issue tokens. Rate-limited 5/min/IP.

### Migration
- **`scripts/sprint8/03_user_totp_schema.sql`** — table `user_totp` (PK user_id, secret TEXT, enrolled_at, last_used_at, recovery_codes JSONB list of hashes, recovery_codes_used INTEGER counter)

### CLI enrollment script
- **`scripts/sprint8/04_totp_enroll_admin.py`** — interactif :
  - Génère secret + provisioning URI + QR ASCII terminal
  - Demande à l'user de scanner avec son app TOTP (Google Auth / 1Password / Aegis / etc.)
  - Vérifie le 1er code à 6 chiffres
  - Insert row + print les 10 recovery codes plaintext

## Activation immédiate (Sinse, MAINTENANT)

```bash
# 1. Migration
docker exec -i postgres-academie psql -U sinse -d academie_db \
  < /opt/academie/scripts/sprint8/03_user_totp_schema.sql

# 2. Rebuild backend (pyotp + qrcode added)
cd /opt/academie/webapp
docker compose -f docker-compose.webapp.yml build academie-api
docker compose -f docker-compose.webapp.yml up -d academie-api

# 3. Install pyotp + qrcode locally too (le script CLI les utilise depuis le host)
pip3 install pyotp qrcode[pil] passlib[bcrypt,argon2]

# 4. Enroll Sinse (compte admin)
python3 /opt/academie/scripts/sprint8/04_totp_enroll_admin.py sinse
```

Le script :
1. Affiche un QR code ASCII dans le terminal — scan avec Google Authenticator / 1Password / Aegis / Bitwarden / Raivo
2. Te demande le 1er code à 6 chiffres pour confirmer
3. Imprime les 10 recovery codes — **note-les sur papier ou dans un password manager hors-ligne**, ils ne seront plus jamais affichés en clair

## Validation post-enrollment

```bash
# Status MFA
docker exec postgres-academie psql -U sinse -d academie_db -c \
  "SELECT user_id, enrolled_at, recovery_codes_used FROM user_totp;"

# Test login flow via curl (depuis host bypass Cloudflare Access)
# 1. Step 1 : password — attendu réponse {"mfa_required": true, "username": "sinse"}
curl -sX POST -H 'Content-Type: application/json' \
  -d '{"username":"sinse","password":"<TON_PASSWORD>"}' \
  http://127.0.0.1:8000/api/auth/login

# 2. Step 2 : password + TOTP code — attendu access_token
curl -sX POST -H 'Content-Type: application/json' \
  -d '{"username":"sinse","password":"<TON_PASSWORD>","code":"123456"}' \
  http://127.0.0.1:8000/api/auth/login-mfa
```

## UI frontend — pas encore livré (A4b session suivante)

Aujourd'hui, le frontend SvelteKit n'a PAS encore le flow MFA. Si tu te logges via l'UI après avoir enrollé TOTP via CLI, le frontend va :
- Recevoir `{"mfa_required": true}` au lieu d'un token
- Probablement crash ou afficher "erreur de connexion"

**Donc fais l'enrollment juste avant qu'on attaque A4b** (UI), ou accepte que tu ne peux te connecter que via curl/script en attendant.

Alternative pragmatique : enroll immédiatement + utilise les recovery codes pour disable temporairement si tu as besoin de te re-logger via UI avant A4b.

A4b livrera (session suivante) :
- Page `/settings/security` SvelteKit avec QR display + flow enrollment
- Page `/login` mise à jour avec champ TOTP en step 2
- Page `/settings/security/recovery-codes` avec regeneration
- Migration secret plaintext → Fernet at-rest encryption

## Disable d'urgence (perte de device + recovery codes épuisés)

```bash
docker exec postgres-academie psql -U sinse -d academie_db -c \
  "DELETE FROM user_totp WHERE user_id = (SELECT id FROM users WHERE username = 'sinse');"
```

À utiliser UNIQUEMENT en cas de lockout total. Documente dans audit log + change immédiatement le password ensuite.

## Rate limiting

- `/api/auth/login` : 5/min/IP (déjà existant)
- `/api/auth/login-mfa` : 5/min/IP (nouveau)
- `/api/security/totp/*` : pas rate-limited séparément (auth-required, donc déjà protégé par session)

## Prochaines étapes Phase A4

- **A4b** : UI frontend (settings + login flow + recovery codes management) + Fernet encryption + WebAuthn/Passkeys scaffolding
- **Étendre à TOUS les users** : invitation email "Activez 2FA" + opt-in dashboard `/settings/security`. Pas de force-enroll en alpha.
- **Admin policy stricte** : `users.is_admin = TRUE` ne peut pas SE désactiver MFA via UI (DELETE force via DB). Implémentation A4b.
