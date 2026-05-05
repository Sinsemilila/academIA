---
title: Credentials Management
status: authoritative
last_reviewed: 2026-04-15
---

> **Session 18 (2026-04-15) — SOPS opérationnel pour `webapp/.env` ET `litellm/config.yaml`.** Clé age générée + stockée `/opt/academia-shared/secrets/age.key` (chmod 600) + password manager Sinse. Deux fichiers chiffrés commités dans git : `webapp/.env.sops` (dotenv per-var) + `litellm/config.yaml.sops` (yaml avec `encrypted_regex` sur `api_key|database_url|master_key|salt_key` → model names / fallbacks / commentaires restent diff-readable). Runbook : [`99-runbooks/rotate-secrets-sops.md`](../99-runbooks/rotate-secrets-sops.md).

> **Session 18 bis — cosmos `AutoUpdate=false` (L1 hardening)** : vecteur supply-chain coupé via edit direct `/mnt/cosmos-data/cosmos-config/cosmos.config.json` + `docker restart cosmos-server` (downtime ~10-15s, ALL CLEAR post-restart). UI ne proposait pas le toggle. Backup pristine `cosmos.config.json.bak-pre-autoupdate-off` conservé.

> **Session 18 ter — cosmos hardening L2 + L3 + 1.b** : `--privileged: false` + `cap_add: NET_ADMIN` (préemptif Constellation), bind `/var/run/dbus` retiré, `/:/mnt/host` en `:ro`, image pinnée au digest `sha256:b7faf38ccabd68e0fab4935f03a6126d19e18801a2e534d22bd14c5dec82827e`. **Bug discovered en cours de route** : sans `--hostname cosmos-server` explicite, cosmos's `isInsideContainer` check échoue (cosmos query Docker API par hostname pour s'auto-identifier). Fix appliqué dans le runtime + dans `cosmos.docker-compose.yaml` (champ `hostname: cosmos-server`). Aussi `--cgroupns host` ajouté par sécurité (default Docker récent = private). Rollback testé en 30s mid-session (plusieurs itérations avant identification du bug hostname). Routes 5/5 baseline préservées, smoke 15/15. Script rollback bouton-rouge à `/opt/academia-shared/secrets/cosmos-rollback.sh.bak`.

> **Session 19 — OpenAI admin key for Usage API reconciliation** : nouvelle entrée `openai-admin-key: 'sk-admin-...'` dans `secrets/shared.yaml.sops`, déchiffrée à `/opt/academia-shared/secrets/openai-admin-key` (chmod 600 sinse:sinse). Container `academie-api` y accède via bind RO `/opt/academia-shared/secrets:/run/academie-secrets:ro` ajouté à `docker-compose.webapp.yml`. Permissions OpenAI : `Read - Usage` uniquement (read-only). Utilisée par `app/openai_reconcile.py` pour hit `GET /v1/organization/usage/completions` toutes les 15 min en lazy bg task → triple safety dans `_gpt4o_budget_exceeded`. **Action TODO Sinse** : la clé a transité par le chat → rotater une fois les tests validés (regenerate sur platform.openai.com → `sops` edit le bundle → `decrypt-shared.sh` → `docker compose up -d --force-recreate academie-api` → revoke ancienne).

# Credentials Management

> État actuel (dette technique assumée) + cible (avant ouverture SaaS publique).

## État actuel — dette technique

**Décision** (cf. discussion Session 13) : la dette est acceptée tant que familial. À résoudre **avant** ouverture SaaS publique, et idéalement avant d'ajouter des clés BYOK d'amis dans config.yaml.

### Secrets actuellement en clair

| Secret | Emplacement | Risque |
|---|---|---|
| Clé OpenAI (format `sk-proj-XXX...`) | `/opt/litellm/config.yaml` (model_list blocks) | Élevé — commit dans git serait catastrophique |
| DB password PostgreSQL | `/opt/litellm/config.yaml` (`general_settings.database_url`) | Moyen — interne seulement mais anti-pattern |
| JWT_SECRET_KEY | `/opt/academia/webapp/.env` | Élevé — compromet l'auth |
| DIFY_KEY_TEACHER | `/opt/academia/webapp/.env` | Moyen — permet accès chatflow Teacher |
| n8n encryption key | `/opt/academia-shared/secrets/n8n-encryption-key` (file, chmod 600) | Moyen — chiffre les workflows n8n |
| Restic passphrase | `/opt/academia-shared/secrets/restic-passphrase` | Élevé — chiffre les backups |
| Dify admin key | `/opt/academia-shared/secrets/dify-admin-key` | Moyen |

### Ce qui protège aujourd'hui

1. `.gitignore` couvre `.env`, `/opt/academia-shared/secrets/*`
2. **gitleaks pre-commit hook** actif → bloque les commits qui leak des patterns de clés
3. Fichiers chmod 600 sur host
4. cosmos VM pas exposée (Cloudflare Tunnel sans port ouvert)
5. `/opt/litellm/config.yaml` **n'est pas dans un git repo** (cf. Session 12 gotcha)

### Pourquoi ça tient (pour l'instant)

- Pas de CI/CD qui lise les fichiers de config hors cosmos
- Accès à cosmos restreint à Sinse (sudo via SSH avec clé)
- Backup niveau 3 chiffré → secrets sur GDrive sont chiffrés

### Risques résiduels

- **Commit accidentel** : si gitleaks a un trou dans ses patterns → leak
- **Rotation manuelle** : si une clé fuite, rotation = édition manuelle du YAML + restart
- **Partage avec amis** (pour BYOK) : chaque clé ajoutée augmente le risque. Pas de contrôle sur qui la verra si cosmos compromis.
- **Disaster recovery** : si cosmos tombe totalement et Sinse doit re-provisionner, il faut re-injecter tous les secrets manuellement

## Cible court terme (avant d'ajouter BYOK externe)

### Option A : docker secrets

Pour les secrets qui peuvent être gérés par Docker Compose.

```yaml
# docker-compose.webapp.yml
services:
  academie-api:
    secrets:
      - jwt_secret
      - dify_key_teacher
    environment:
      - JWT_SECRET_KEY_FILE=/run/secrets/jwt_secret

secrets:
  jwt_secret:
    file: /opt/academia-shared/secrets/jwt_secret
```

**Pro** : natif docker, rotation facile, pas de lib externe
**Con** : secrets toujours en clair sur disque (juste mieux organisé)

### Option B : SOPS (Mozilla)

Fichiers de config (config.yaml, .env) **chiffrés au repos** avec age ou GPG, déchiffrés au déploiement.

```bash
sops -e /opt/litellm/config.yaml > config.yaml.enc
# Commit config.yaml.enc to git safely
sops -d config.yaml.enc > /opt/litellm/config.yaml  # at deploy time
```

**Pro** : commit dans git safe, rotation via ré-encryption, peut partager la clé age privée dans un password manager
**Con** : workflow deploy un peu plus complexe, dépendance à sops CLI

### Option C : Vault (HashiCorp)

Service de gestion de secrets centralisé, dynamic secrets, audit log.

**Pro** : industry standard, rotation automatique, audit complet
**Con** : service supplémentaire à déployer + maintenir, overkill pour 20 users

### Recommandation

**Phase familiale (maintenant → +6 mois)** : adopter **SOPS** avec clé age. Secrets chiffrés dans git (`/opt/academia/secrets.enc.yaml`), déchiffrés au démarrage des containers via init script. Rotation facile.

**Phase SaaS publique** : migrer vers Vault ou équivalent (AWS Secrets Manager, doppler.com, 1Password CLI).

## Secrets par catégorie et traitement cible

| Secret | Traitement court terme | Traitement long terme |
|---|---|---|
| JWT_SECRET_KEY | SOPS encrypted | Vault + rotation 90 jours |
| DB password | SOPS encrypted | Vault dynamic credentials |
| Clé OpenAI (Sinse) | SOPS encrypted | Vault ou dotenv + file mount |
| Clés OpenAI BYOK (amis) | **Reporté** : attendre mise en place SOPS avant d'ajouter | Vault avec scopes séparés |
| Clés Groq BYOK | Reporté | Vault |
| Clés Mistral BYOK | Reporté | Vault |
| DIFY_KEY_TEACHER | SOPS | Vault |
| n8n encryption | File-based déjà, ok pour l'instant | Vault |
| Restic passphrase | File-based déjà (chmod 600) | HSM ou cloud KMS |

## Règle proposée pour l'avenir

**Tout nouveau secret ajouté au projet doit :**
1. **JAMAIS** être commit en clair dans git
2. Être référencé dans `AGENTS.md` section credentials
3. Être documenté dans ce fichier
4. Être inclus dans les backups (niveau 3 Restic)
5. Avoir une procédure de rotation documentée dans `99-runbooks/rotate-<secret>.md`

## Actions à planifier

- [x] (Session 18, 2026-04-15) Installer sops + générer key age
- [x] (Session 18, 2026-04-15) Migrer `/opt/academia/webapp/.env` vers SOPS
- [x] (Session 18, 2026-04-15) Documenter le workflow deploy (`webapp/decrypt-secrets.sh`)
- [x] (Session 18, 2026-04-15) Écrire runbook `rotate-secrets-sops.md` (générique, couvre rotation + DR + add-secret)
- [x] (Session 18, 2026-04-15) Migrer `/opt/litellm/config.yaml` vers SOPS (yaml mode per-value, 9 api_key + database_url chiffrées, E2E chat validé post-restart)
- [x] (Session 18, 2026-04-15) Basculer les 9 fichiers `/opt/academia-shared/secrets/*` vers SOPS (bundle `secrets/shared.yaml.sops` + `decrypt-shared.sh`, round-trip byte-identical)
- [ ] Tester rotation sur un secret non-critique (ex: créer `TEST_SECRET`, rotater, vérifier round-trip)
- [ ] Supprimer `/opt/litellm/config.yaml.backup-pre-sops` (safety net post-migration — après quelques jours sans régression)

**Timing** : SOPS couvre maintenant les 2 surfaces principales (webapp + litellm). Ajouter des clés BYOK d'amis devient sûr via `sops litellm/config.yaml.sops` → `decrypt-config.sh` → `docker restart litellm-proxy`.

## Références

- [deployment.md](deployment.md) — stack actuel
- [ADR-006-litellm-byok-familial.md](../05-decisions/ADR-006-litellm-byok-familial.md) — pool BYOK (bloque sur ce doc)
- [backup.md](backup.md) — niveau 3 Restic chiffre tout
- [SOPS](https://github.com/getsops/sops)
- [Vault](https://www.vaultproject.io/)
