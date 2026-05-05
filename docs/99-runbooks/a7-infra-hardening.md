# A7 — Infra hardening + supply chain (refactor 2026-H2 Phase A)

**Status** : in progress
**Last updated** : 2026-04-23
**Related** : [`docs/05-decisions/ADR-001-refactor-complete-2026-H2.md`](../05-decisions/ADR-001-refactor-complete-2026-H2.md)

Runbook actionable pour Sinse. Ce document liste TOUS les items A7, marque ceux livrés en code (CI/Dependabot) et détaille pas-à-pas ceux qui nécessitent une action manuelle (Cloudflare dashboard, Dockerfile rebuild, backup audit).

## ✅ Livrés en code + appliqués (Session 46)

- **Dependabot** : `.github/dependabot.yml` créé + `dependabot_security_updates` + `vulnerability_alerts` activés via API GitHub (Sinsemilila/academIA).
- **CI security-audit** : `.github/workflows/security-audit.yml` — pip-audit (HIGH blocking), npm audit (HIGH blocking), syft SBOM (CycloneDX + SPDX, retained 90j), Trivy filesystem scan (CRITICAL+HIGH blocking, ignore-unfixed). S'active dès push origin/main.
- **Cloudflare DNS** :
  - SPF TXT `petit-pont.com` = `v=spf1 -all` (no mail self-hosted)
  - DMARC TXT `_dmarc.petit-pont.com` = `v=DMARC1; p=none; rua=mailto:dmarc-reports@petit-pont.com; fo=1; adkim=s; aspf=s` (phase 1, bump à `p=quarantine` après 2 sem clean)
- **Cloudflare SSL/TLS** :
  - SSL mode = Full (strict)
  - Always Use HTTPS = ON
  - Min TLS 1.2 + TLS 1.3 ON
  - Automatic HTTPS Rewrites = ON
  - Opportunistic Encryption = ON
  - HSTS : max_age 31536000 (1 an), includeSubdomains, no-preload (preload activé après A3 enforce stable)
- **Cloudflare WAF** : Free Managed Ruleset activé (entrypoint `http_request_firewall_managed` créé pointant vers ruleset id `77454fe2d30c4220b5701f6fdfb893ba`)
- **Cloudflare ratelimit existant** : "Leaked credential check" (rule pré-existante, conservée — bloque les requêtes avec credentials fuités)

## 🟡 Restent à faire manuellement (perms account-level non incluses dans token zone)

- **Bot Fight Mode** : Cloudflare dashboard → academia.petit-pont.com → Security → Bots → Bot Fight Mode = ON. (API requiert Account-level Bot Management edit, non inclus dans le token A7 zone-scope.)
- **Cache Rule `/_app/immutable/*`** : dashboard → Caching → Cache Rules → créer règle. Match `(http.request.uri.path matches "^/_app/immutable/")`, Edge TTL 1 month, Browser TTL 1 month. (API a renvoyé "request is not authorized" — perm Cache Rules pas mappée à Page Rules dans le token actuel.)

## ⏭️ Reporté en backend — Rate limiting `/api/*`

Free tier Cloudflare = **1 seule règle ratelimit max** (déjà occupée par "Leaked credential check"). Le rate limit `/api/*` 100r/m sera implémenté en backend FastAPI via `slowapi` middleware en **Phase A5** (déjà au plan ADR-001). Cloudflare rate limit reportée si on passe en tier payant.

## 📚 Référence — DNS Cloudflare (déjà appliqué, garder pour rotation/upgrade)

petit-pont.com est sur Cloudflare (registrar + DNS confirmé via whois). Aucun MX record actuellement (pas de mail self-hosted), donc on configure **SPF + DKIM + DMARC** pour bloquer le spoofing du domaine. Si tu envoies des emails (auth, reset password, notifs) via un provider tiers (Resend, Mailgun, SendGrid, Postmark, etc.), adapte les valeurs ci-dessous selon ton provider.

### SPF (Sender Policy Framework)

**Cas A — pas d'envoi mail du tout** :
```
Type: TXT
Name: @
Content: v=spf1 -all
TTL: Auto
```
Refuse explicitement tout email prétendant venir de petit-pont.com.

**Cas B — envoi mail via provider tiers** :
```
Type: TXT
Name: @
Content: v=spf1 include:<spf-du-provider>.com -all
```
Exemples include :
- Resend : `include:_spf.resend.com`
- Mailgun : `include:mailgun.org`
- SendGrid : `include:sendgrid.net`
- Postmark : `include:spf.mtasv.net`

### DKIM (DomainKeys Identified Mail)

**Cas A — pas d'envoi mail** : pas de DKIM nécessaire.

**Cas B — envoi mail via provider tiers** : génère la clé DKIM côté provider (dashboard du provider → Domain → DKIM setup), il te donnera un record TXT à ajouter, typiquement :
```
Type: TXT
Name: <selector>._domainkey
Content: v=DKIM1; k=rsa; p=<long base64>
```

### DMARC (Domain-based Message Authentication, Reporting & Conformance)

Phase 1 (collecte 2 semaines, none = pas de blocage) :
```
Type: TXT
Name: _dmarc
Content: v=DMARC1; p=none; rua=mailto:dmarc-reports@petit-pont.com; ruf=mailto:dmarc-reports@petit-pont.com; fo=1; adkim=s; aspf=s
TTL: Auto
```

Phase 2 (après 2 semaines de collecte sans faux positifs) :
```
Content: v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@petit-pont.com; pct=100; adkim=s; aspf=s
```

Phase 3 (après 1 mois en quarantine sans incident) :
```
Content: v=DMARC1; p=reject; rua=mailto:dmarc-reports@petit-pont.com; pct=100; adkim=s; aspf=s
```

### Vérification post-ajout

```bash
dig +short petit-pont.com TXT | grep spf
dig +short _dmarc.petit-pont.com TXT
dig +short <selector>._domainkey.petit-pont.com TXT  # si DKIM
```

Outils en ligne : [mxtoolbox.com/SuperTool.aspx](https://mxtoolbox.com/SuperTool.aspx), [dmarcian.com/dmarc-inspector](https://dmarcian.com/dmarc-inspector/).

## 🟡 À faire manuellement — Cloudflare WAF + Bot Fight Mode (free tier, 10 min)

Cloudflare est déjà devant academia.petit-pont.com (IPs 188.114.96.x confirmées). Activer le free tier offre WAF managed rules + bot mitigation basique sans coût.

### WAF Managed Rules (free tier)

1. Cloudflare dashboard → academia.petit-pont.com → Security → WAF
2. Section **Managed rules** :
   - Activer **Cloudflare Free Managed Ruleset** (anciennement OWASP Core Rule Set lite)
   - Mode : `Block` (pas `Log` qui ne fait que journaliser)
3. Section **Custom rules** : laisser vide pour l'instant (limité à 5 règles en free tier, on garde le quota pour quand on en aura besoin)
4. Section **Rate limiting rules** : créer 1 règle gratuite :
   - Field : `URI Path`, Operator : `contains`, Value : `/api/`
   - Then : `Block` if exceeds `100 requests per 1 minute` from same IP

### Bot Fight Mode (free tier)

1. Security → Bots → **Bot Fight Mode** : ON
2. Couvre les bots simples (scrapers, scanners). Pas de Super Bot Fight Mode (Pro/Business only).

### Page Rules / Cache Rules pour assets

1. Caching → Cache Rules → créer :
   - Match : `(http.request.uri.path matches "^/_app/immutable/")`
   - Cache eligibility : `Eligible for cache`
   - Edge TTL : `1 month`
   - Browser TTL : `1 month`
2. SvelteKit emet des assets versionnés sous `/_app/immutable/*` qui sont safe à cacher longtemps.

### SSL / TLS settings

1. SSL/TLS → Overview → Encryption mode : **Full (strict)**
2. SSL/TLS → Edge Certificates :
   - **Always Use HTTPS** : ON
   - **HTTP Strict Transport Security (HSTS)** : Enable, max-age 12 months, Apply HSTS to subdomains, Preload (uncheck preload until A3 enforce stable)
   - **Minimum TLS Version** : 1.2 (1.3 si tu veux casser les vieux clients)
   - **Opportunistic Encryption** : ON
   - **TLS 1.3** : ON
   - **Automatic HTTPS Rewrites** : ON

### Vérification post-config

- [ssllabs.com/ssltest/analyze.html?d=academia.petit-pont.com](https://www.ssllabs.com/ssltest/analyze.html?d=academia.petit-pont.com) → viser A+
- [observatory.mozilla.org/analyze/academia.petit-pont.com](https://observatory.mozilla.org/analyze/academia.petit-pont.com) → viser A+ (note : sera limité tant que A3 CSP/HSTS pas appliqués au niveau origin)

## 🟡 À faire prochaine session — Docker hardening (rebuild requis)

Le `webapp/docker-compose.webapp.yml` actuel n'a pas de durcissement. Patches proposés (à appliquer + rebuild + smoke-test après) :

```yaml
services:
  academie-frontend:
    # ... existant ...
    user: "node"  # nécessite USER node dans Dockerfile frontend
    read_only: true
    tmpfs:
      - /tmp:size=100M
      - /app/.svelte-kit:size=200M
    cap_drop: [ALL]
    security_opt:
      - no-new-privileges:true

  academie-api:
    # ... existant ...
    user: "1000:1000"  # nécessite useradd dans Dockerfile backend
    read_only: true
    tmpfs:
      - /tmp:size=100M
    cap_drop: [ALL]
    security_opt:
      - no-new-privileges:true
```

Dockerfiles à modifier en parallèle :

`webapp/backend/Dockerfile` (ajouter avant `EXPOSE`) :
```dockerfile
RUN useradd -u 1000 -m -s /bin/bash academie && \
    chown -R academie:academie /app /packages
USER academie
```

`webapp/frontend/Dockerfile` (l'image officielle node a déjà un user `node`) :
```dockerfile
RUN chown -R node:node /app
USER node
```

**À tester soigneusement** : certains chemins en écriture peuvent casser (cache pip, build cache Vite, sessions SvelteKit). À itérer avec smoke-test après chaque changement.

## 🟡 À faire — Audit backup actuel + restore mensuel testé

`/opt/academia-shared/secrets/restic-passphrase` existe → un setup restic existe quelque part (probablement Cosmos-managed ou cron OS-level). À auditer :

```bash
# Lister les snapshots restic actuels
restic snapshots --password-file /opt/academia-shared/secrets/restic-passphrase

# Vérifier la rotation
restic forget --password-file /opt/academia-shared/secrets/restic-passphrase --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --dry-run

# Test restore (sur un dossier temp)
restic restore latest --target /tmp/restic-restore-test --password-file /opt/academia-shared/secrets/restic-passphrase
```

Action Sinse : confirmer où tourne restic (cron quel user ? quel host ? quel target — Drive ? S3 compatible ?), puis :
1. Documenter dans ce runbook la commande/cron exacte
2. Ajouter un cron mensuel de test restore avec alerte mail/notif si fail
3. Si pas de restic actif : l'activer ou créer un nouveau setup pg_dump+age+rclone vers Drive

## 🟡 À faire — Cosign Docker image signing

Pas urgent en alpha self-hosted (pas d'images publiées sur registry public), mais à mettre en place dès qu'on aura un build push vers ghcr.io ou Docker Hub.

```bash
# Generate keypair (one-time)
cosign generate-key-pair

# Sign image post-build
cosign sign --key cosign.key ghcr.io/sinsemilila/academia:<tag>

# Verify pre-deploy
cosign verify --key cosign.pub ghcr.io/sinsemilila/academia:<tag>
```

Action : reporter à quand on aura un registry. Pas bloquant pour beta privée fermée.

## Checklist A7 finale (pour KPI gate Phase A)

- [x] Dependabot config créée
- [x] Dependabot security updates + vulnerability alerts activés (API GitHub)
- [x] CI security-audit créé (pip-audit + npm audit + syft + Trivy)
- [ ] CI green sur main (vérif après push)
- [x] SPF record TXT ajouté (`v=spf1 -all` Session 47, auto-rewrite Session 55 par CF Email Routing → `v=spf1 include:_spf.mx.cloudflare.net ~all`)
- [x] DMARC record TXT ajouté (phase 1 `p=none` Session 47, **bumped `p=quarantine` Session 55 jalon 2026-05-07**)
- [x] DKIM record TXT ajouté (`cf2024-1._domainkey` Session 55, auto via Cloudflare Email Routing)
- [x] Cloudflare Free Managed Ruleset activé
- [ ] Cloudflare Bot Fight Mode ON (manuel dashboard, perm account-level)
- [ ] Cloudflare Cache rule `/_app/immutable/` (manuel dashboard, perm Cache Rules)
- [⏭️] Cloudflare Rate limiting `/api/*` (reporté → backend slowapi en A5, free tier limite à 1 règle déjà occupée par leaked-creds check)
- [x] Cloudflare SSL/TLS Full (strict) + Always HTTPS + Min TLS 1.2 + TLS 1.3 + HSTS 1 an
- [ ] SSL Labs A+ (vérifier post-application : ssllabs.com/ssltest/analyze.html?d=academia.petit-pont.com)
- [ ] Mozilla Observatory A+ (peut attendre A3 CSP origin)
- [ ] Docker hardening appliqué + smoke-test green (A7b prochaine session)
- [ ] Restore restic testé une fois
- [x] DMARC bumped à `p=quarantine` après 2 semaines collecte clean (**jalon 2026-05-07 hit Session 55**)
- [x] A3 CSP `Report-Only` → enforce flip (Session 55 jalon 2026-05-07, commit `e1fa359` + Access bypass app PWA assets id `7eaa58d0-c3df-4e73-bd12-3fb2291a904e`)
- [x] Cloudflare Email Routing — 3 alias `security@/dmarc-reports@/dsar@petit-pont.com` → forward `sinseproduction@gmail.com` (Session 55)
