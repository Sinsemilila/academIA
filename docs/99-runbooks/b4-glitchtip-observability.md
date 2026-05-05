# B4 — GlitchTip self-hosted observability + bundle budget CI

**Status** : livré Session 47 — stack Docker up + SDK frontend/backend + workflow CI bundle budget + dashboard public via Cloudflare Access. Backend capture validée live.
**Last updated** : 2026-04-23
**Related** : ADR-001 §B4

---

## Architecture

3 nouveaux containers ajoutés dans `webapp/docker-compose.webapp.yml` :

| Container | Image | RAM limit | Rôle |
|---|---|---|---|
| `redis-glitchtip` | redis:7-alpine | 96M | Broker celery dédié (isolé de redis-academie sessions) |
| `glitchtip-web` | glitchtip/glitchtip:v5.0 | 512M | UI + API uwsgi, port 127.0.0.1:8001 |
| `glitchtip-worker` | glitchtip/glitchtip:v5.0 | 384M | Celery worker + beat scheduler |

**Postgres partagé** : DB `glitchtip_db` créée sur `postgres-academie` (cf. `scripts/sprint8/12_glitchtip_db_create.sql`).

**Network** : tous sur `academie-net-bridge` (external).

**Accès public** : `https://glitchtip.petit-pont.com` via Cloudflare Tunnel `proxmox-tunnel` (UUID `a57431d7-...`) → ingress vers Cosmos host (192.168.1.181:80) → Cosmos route `glitchtip.petit-pont.com` → `http://localhost:8001` (host network → glitchtip-web container).

**Auth** : Cloudflare Access avec 2 apps (path-based, plus spécifique gagne) :
- **App "GlitchTip Dashboard"** (path `/`) — Allow `email = segura_clement@hotmail.fr`, IdP One-time PIN, session 24h. Couvre l'UI dashboard.
- **App "GlitchTip SDK ingestion (bypass)"** (path `/api`) — Bypass Everyone. Couvre les endpoints Sentry SDK ingestion (`/api/<project>/envelope/`, `/api/<project>/store/`). Sans cette app de bypass, le SDK frontend reçoit 403 Cloudflare au lieu de poster les events.

---

## Setup initial (one-shot, **livré Session 47** — référence)

### 1. Accès dashboard

Ouvrir `https://glitchtip.petit-pont.com` dans le browser → Cloudflare Access challenge → entrer `segura_clement@hotmail.fr` → recevoir un PIN par email → entrer le PIN → redirigé vers GlitchTip Django login → `segura_clement@hotmail.fr` + password → dashboard.

Session Cloudflare Access valide 24h. Session GlitchTip Django valide jusqu'à logout explicite.

### 2. Création du superuser (déjà fait Session 47)

```bash
docker exec -it glitchtip-web ./manage.py createsuperuser  # interactif (legacy ref)
# OU non-interactive (Session 47 a utilisé celle-là) :
docker exec -e DJANGO_SUPERUSER_EMAIL='segura_clement@hotmail.fr' \
            -e DJANGO_SUPERUSER_PASSWORD='<password>' \
            glitchtip-web ./manage.py createsuperuser --noinput
```

### 3. Création de l'organisation + projects

Une fois loggé :
- Créer organization `academie`
- Créer 2 projects :
  - `academie-frontend` (platform: `javascript-svelte`) → noter le DSN
  - `academie-backend` (platform: `python-fastapi`) → noter le DSN

### 4. Ajouter les DSN à `.env.sops`

Décrypter, ajouter, re-encrypter :

```bash
SOPS_AGE_KEY_FILE=/opt/academia-shared/secrets/age.key sops --input-type dotenv --output-type dotenv -d webapp/.env.sops > /tmp/env.plain
# éditer /tmp/env.plain : ajouter PUBLIC_SENTRY_DSN_FRONTEND= et SENTRY_DSN_BACKEND=
mv /tmp/env.plain /tmp/env.new.sops
SOPS_AGE_KEY_FILE=/opt/academia-shared/secrets/age.key sops --config .sops.yaml --input-type dotenv --output-type dotenv -e /tmp/env.new.sops > webapp/.env.sops
rm /tmp/env.new.sops
```

Puis copier les valeurs claires aussi dans `webapp/.env` (les containers lisent .env, pas .env.sops directement) et rebuild :

```bash
docker compose -f webapp/docker-compose.webapp.yml up -d --build academie-api academie-frontend
```

### 5. Test capture end-to-end

**Backend** :
```bash
curl -s http://127.0.0.1:8000/api/debug/sentry-test
# → 500 Internal Server Error
# → vérifier dans GlitchTip UI : "Issues" → l'event "B4 sentry test" apparaît sous 30s
```

**Frontend** : ajouter temporairement `<button onclick={() => { throw new Error('B4 frontend test'); }}>test</button>` quelque part dans une `+page.svelte`, click, vérifier dans le project `academie-frontend` GlitchTip.

### 6. Cleanup

Une fois validé :
- Supprimer le endpoint `/api/debug/sentry-test` dans `webapp/backend/app/main.py`
- Supprimer le bouton de test frontend
- Commit : `[refactor-2026h2-B4] retire endpoint debug post-validation`

---

## PII scrubbing

**Backend** (`main.py` `_scrub_pii`) :
- Drop : `request.cookies`, headers `cookie`/`x-csrf-token`/`authorization`
- Body avec `password`/`secret` → remplacé par `<scrubbed>`
- `event.user.id` → `<redacted>`

**Frontend** (`hooks.client.ts` `beforeSend`) :
- Idem cookies + headers
- Body string contenant `password`/`secret` → `<scrubbed>`
- User → `<redacted>`

`send_default_pii=False` activé — Sentry ne capture pas IP, user-agent, ni request body par défaut sans confirmation explicite.

---

## Source maps

**Désactivées en alpha** (`vite.config.ts` → `sentrySvelteKit({ sourceMapsUploadOptions: { org: undefined } })`).

**Stack traces JS minifiées** dans GlitchTip — acceptable pour un solo dev qui lit les fonctions par contexte. À activer post-baseline :

```typescript
sentrySvelteKit({
  sourceMapsUploadOptions: {
    org: 'academie',
    project: 'academie-frontend',
    authToken: process.env.SENTRY_AUTH_TOKEN,
    url: 'http://localhost:8001',  // ou public URL si setup
  },
}),
```

Token créé dans GlitchTip : Settings → Account → API Tokens.

---

## Bundle budget CI

`.github/workflows/bundle-budget.yml` triggers sur PR + push main qui touche `webapp/frontend/`.

**Mesures (toutes gzipped)** :
- Entry (`app.*` + `start.*`) — budget **80 KB**
- Lazy chunks total — budget **500 KB**
- Page nodes + total `_app/immutable` — reference

**Comment PR sticky** affiché avec table ✅/⚠️.

### Flip strict gate (futur)

Quand baseline stable (3-4 PRs sans drift), ajouter dans `bundle-budget.yml` après `Comment PR` :

```yaml
- name: Enforce budget
  if: ${{ steps.m.outputs.entry_kb > 80 || steps.m.outputs.chunks_kb > 500 }}
  run: |
    echo "::error::Bundle budget exceeded (entry=${{ steps.m.outputs.entry_kb }}KB, chunks=${{ steps.m.outputs.chunks_kb }}KB)"
    exit 1
```

---

## Maintenance

- **GlitchTip image upgrade** : `docker compose pull glitchtip-web glitchtip-worker && docker compose up -d glitchtip-web glitchtip-worker`. Toujours vérifier le changelog GitHub releases avant.
- **Migration DB** : exécuter `docker exec glitchtip-web ./manage.py migrate` après chaque upgrade image.
- **Backup `glitchtip_db`** : inclus dans le backup PG global restic (sur l'instance `postgres-academie`).
- **Trivy scan image** : actuellement Trivy scan FS uniquement. Ajouter `trivy image glitchtip/glitchtip:v5.0` dans `security-audit.yml` pour couvrir les CVEs de l'image (followup).

---

## Future enhancements

- **Public dashboard** : sous-domaine `glitchtip.petit-pont.com` via Cloudflare DNS + cosmos route. Permet d'envoyer des alertes email/webhook directement vers Slack/Discord. Pas critique alpha (1 user, SSH tunnel suffit).
- **Source maps upload** : activer auth token + upload step CI quand baseline stable.
- **Alerting rules** : dans GlitchTip UI, configurer notifications (email console seul actuellement, configurer SMTP via `EMAIL_URL` dans `.env.glitchtip` quand provider transactionnel choisi cf. minors-flow-roadmap.md).
- **Stripe `release` tracking** : tag chaque deploy avec `release: <git-sha>` dans Sentry init pour grouper les errors par version, identifier la PR fautive.
- **Strict bundle gate** : flip en strict après 3-4 PRs stables.
