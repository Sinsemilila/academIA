# A3 — CSP Report-Only + security headers (refactor 2026-H2 Phase A)

**Status** : in progress (collection window opened)
**Last updated** : 2026-04-23
**Related** : [`docs/05-decisions/ADR-001-refactor-complete-2026-H2.md`](../05-decisions/ADR-001-refactor-complete-2026-H2.md)

Collecte 2 semaines des violations CSP en mode report-only → analyse → flip à enforce strict. Séquencé en premier dans Phase A parce que la fenêtre de collecte tourne en arrière-plan pendant qu'on travaille sur A1/A2/A4/A5/A6.

## Code livré (Session 46)

### Backend
- **`webapp/backend/app/main.py`** — extension du middleware `security_headers` existant :
  - `X-Content-Type-Options: nosniff` (déjà en place)
  - `X-Frame-Options: DENY` (déjà en place)
  - `Referrer-Policy: strict-origin-when-cross-origin` (déjà en place)
  - **NOUVEAU** : `Cross-Origin-Opener-Policy: same-origin`
  - **NOUVEAU** : `Cross-Origin-Resource-Policy: same-origin`
  - **NOUVEAU** : `Permissions-Policy` (27 features disabled)
- **`webapp/backend/app/routers/security_router.py`** (nouveau) :
  - `POST /api/csp-report` — endpoint un-authed pour violations
  - Accepte `application/csp-report` (legacy) + `application/reports+json` (Reporting API W3C)
  - Rate-limited 60r/min/IP (anti-spam navigateur)
  - Query strings stripped (`document_uri`, `referrer`, `blocked_uri`) pour éviter PII
  - IP SHA256 daily-salted (pas l'IP brute stockée)
  - Cap 10 reports par payload
  - Insert `csp_violations` (JSONB raw + colonnes extraites)

### Frontend
- **`webapp/frontend/src/hooks.server.ts`** — handler étendu :
  - Pages HTML SvelteKit reçoivent `Content-Security-Policy-Report-Only` avec directives permissives initiales (`'unsafe-inline'` / `'unsafe-eval'` tolérés temporairement pour collecte baseline)
  - `connect-src` inclut `wss://` pour streaming SSE chat + `https://dify.petit-pont.com`
  - `frame-src` inclut Dify embed + `challenges.cloudflare.com` (Turnstile futur)
  - `frame-ancestors 'none'` (clickjacking protection)
  - `report-uri /api/csp-report`
  - Headers transverses pour pages HTML : COOP same-origin, CORP same-origin, X-Content-Type-Options nosniff, Referrer-Policy strict-origin-when-cross-origin
  - Proxy `/api/*` préserve `x-forwarded-for` pour IP hashing côté backend

### Migration
- **`scripts/sprint8/01_csp_violations_schema.sql`** — nouvelle table `csp_violations` + index + vue agrégée `csp_violations_24h`

## À faire pour activation (manuel)

### 1. Appliquer la migration

```bash
docker exec -i postgres-academie psql -U sinse -d academie_db \
  < /opt/academia/scripts/sprint8/01_csp_violations_schema.sql
```

Vérif :
```bash
docker exec postgres-academie psql -U sinse -d academie_db -c "\d csp_violations"
```

### 2. Rebuild containers backend + frontend

```bash
cd /opt/academia/webapp
docker compose -f docker-compose.webapp.yml build academie-api academie-frontend
docker compose -f docker-compose.webapp.yml up -d academie-api academie-frontend
```

### 3. Vérifier les headers sortent bien

```bash
# API response
curl -sI https://academia.petit-pont.com/api/health | grep -iE "cross-origin|permissions-policy|referrer|content-type"

# Page HTML
curl -sI https://academia.petit-pont.com/ | grep -iE "content-security|cross-origin|permissions-policy|referrer"
```

Attendu sur la page HTML :
```
content-security-policy-report-only: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; ...; report-uri /api/csp-report
cross-origin-opener-policy: same-origin
cross-origin-resource-policy: same-origin
referrer-policy: strict-origin-when-cross-origin
```

### 4. Lancer le collecteur (automatique dès rebuild)

Les navigateurs des 141 users actuels + tous futurs visiteurs commencent à envoyer des violations à `/api/csp-report` dès que leur cache se rafraîchit sur le nouveau HTML. Collecte passive.

## Phase d'analyse (J+7, J+14)

### Requêtes d'analyse

Top directives violées :
```sql
SELECT effective_directive, blocked_uri, hits, unique_ips, last_seen
FROM csp_violations_24h
ORDER BY hits DESC
LIMIT 20;
```

Top source files déclenchant :
```sql
SELECT source_file, effective_directive, COUNT(*) AS n
FROM csp_violations
WHERE reported_at > now() - INTERVAL '7 days'
GROUP BY source_file, effective_directive
ORDER BY n DESC;
```

Violations depuis un seul IP (bot probable) :
```sql
SELECT ip_hash, COUNT(*) AS n, COUNT(DISTINCT effective_directive) AS distinct_directives
FROM csp_violations
WHERE reported_at > now() - INTERVAL '24 hours'
GROUP BY ip_hash
HAVING COUNT(*) > 100
ORDER BY n DESC;
```

### Décision flip enforce (J+14)

Après 2 semaines :
1. Whitelist précise des hashes/nonces Svelte 5 inline scripts (`'sha256-...'` au lieu de `'unsafe-inline'`)
2. Retirer `'unsafe-eval'` si aucun hit non-trivial
3. Identifier domaines externes utilisés dans `connect-src` / `frame-src` / `img-src`
4. Remplacer `Content-Security-Policy-Report-Only` par `Content-Security-Policy` (enforce) dans `hooks.server.ts`
5. Garder `report-uri` actif pour monitoring continu

### KPI gate flip-to-enforce

- [ ] 0 violation unexpected domain dans les 48h précédant le flip
- [ ] 100% des inline scripts Svelte 5 couverts par hashes/nonces connus
- [ ] Tests e2e Playwright passent avec enforce mode actif en staging
- [ ] Rollback plan : revert `hooks.server.ts` + redeploy = 2 min si casse prod

## Risques à surveiller pendant la collecte

- **Volume** : si 1000+ violations/heure = anomalie (user agent compromis ou fuite d'origine). Alerte cost-runaway sur logs.
- **PII dans raw_report** : les navigateurs peuvent leaker des URLs complètes dans `blocked-uri`. On strip les query strings mais les paths peuvent contenir des IDs. Audit visuel périodique du JSONB.
- **GDPR** : IP hashées + rotation 90j + pas d'`eleve_id` stocké → pas de PII directement identifiable. À documenter dans le registre A6.

## Intégration avec autres items Phase A

- **A4 MFA + Turnstile** : `frame-src` inclut déjà `challenges.cloudflare.com` pour Turnstile
- **A5 PII scrubber** : le même mécanisme de redaction peut être réutilisé pour les logs LLM
- **A6 RGPD** : table `csp_violations` à lister dans le registre traitements (données = logs techniques, finalité = sécurité applicative, durée = 90 jours)
- **Cloudflare Page Shield** (déjà actif) : complémentaire CSP — détecte les scripts tiers côté edge. CSP détecte les violations côté navigateur. Les deux ensemble = défense en profondeur.

## Rollback rapide

Si un header casse le site :
```bash
cd /opt/academia
git revert <commit-sha>
cd webapp && docker compose -f docker-compose.webapp.yml up -d --build academie-frontend academie-api
```

`Content-Security-Policy-Report-Only` ne bloque JAMAIS — que signale. Donc risque réel uniquement sur COOP/COEP/Permissions-Policy. Si problème → retirer COOP en premier (c'est celui qui casse le plus d'intégrations legacy).
