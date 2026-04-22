# A7 — Infra hardening + supply chain (refactor 2026-H2 Phase A)

**Status** : in progress
**Last updated** : 2026-04-23
**Related** : [`docs/05-decisions/ADR-001-refactor-complete-2026-H2.md`](../05-decisions/ADR-001-refactor-complete-2026-H2.md)

Runbook actionable pour Sinse. Ce document liste TOUS les items A7, marque ceux livrés en code (CI/Dependabot) et détaille pas-à-pas ceux qui nécessitent une action manuelle (Cloudflare dashboard, Dockerfile rebuild, backup audit).

## ✅ Livrés en code (Session 46)

- **Dependabot** : `.github/dependabot.yml` — auto-PR hebdomadaires sur pip (backend + academie-core), npm (frontend), GitHub Actions, Docker. Groups `minor-patch` pour réduire le bruit. **Action Sinse** : activer Dependabot dans Settings → Code security → Enable Dependabot.
- **CI security-audit** : `.github/workflows/security-audit.yml` — pip-audit (HIGH blocking), npm audit (HIGH blocking), syft SBOM (CycloneDX + SPDX, retained 90j), Trivy filesystem scan (CRITICAL+HIGH blocking, ignore-unfixed). Run on push main / PR / weekly Monday 5am UTC. **Action Sinse** : aucune, s'active dès merge sur main.

## 🟡 À faire manuellement — DNS Cloudflare (5-10 min, zéro coût)

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

Cloudflare est déjà devant academie.petit-pont.com (IPs 188.114.96.x confirmées). Activer le free tier offre WAF managed rules + bot mitigation basique sans coût.

### WAF Managed Rules (free tier)

1. Cloudflare dashboard → academie.petit-pont.com → Security → WAF
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

- [ssllabs.com/ssltest/analyze.html?d=academie.petit-pont.com](https://www.ssllabs.com/ssltest/analyze.html?d=academie.petit-pont.com) → viser A+
- [observatory.mozilla.org/analyze/academie.petit-pont.com](https://observatory.mozilla.org/analyze/academie.petit-pont.com) → viser A+ (note : sera limité tant que A3 CSP/HSTS pas appliqués au niveau origin)

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

`/opt/academie-shared/secrets/restic-passphrase` existe → un setup restic existe quelque part (probablement Cosmos-managed ou cron OS-level). À auditer :

```bash
# Lister les snapshots restic actuels
restic snapshots --password-file /opt/academie-shared/secrets/restic-passphrase

# Vérifier la rotation
restic forget --password-file /opt/academie-shared/secrets/restic-passphrase --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --dry-run

# Test restore (sur un dossier temp)
restic restore latest --target /tmp/restic-restore-test --password-file /opt/academie-shared/secrets/restic-passphrase
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
- [ ] Dependabot activé dans Settings GitHub
- [x] CI security-audit créé (pip-audit + npm audit + syft + Trivy)
- [ ] CI green sur main
- [ ] SPF record TXT ajouté
- [ ] DMARC record TXT ajouté (phase 1 `p=none`)
- [ ] DKIM (si envoi mail tiers) record TXT ajouté
- [ ] Cloudflare Free Managed Ruleset activé en `Block`
- [ ] Cloudflare Bot Fight Mode ON
- [ ] Cloudflare Rate limiting `/api/*` 100r/m IP
- [ ] Cloudflare Cache rule `/_app/immutable/`
- [ ] Cloudflare SSL/TLS Full (strict) + Always HTTPS + HSTS
- [ ] SSL Labs A+
- [ ] Mozilla Observatory A+ (peut attendre A3 CSP)
- [ ] Docker hardening appliqué + smoke-test green
- [ ] Restore restic testé une fois
- [ ] DMARC bumped à `p=quarantine` après 2 semaines collecte clean
