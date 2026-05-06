---
title: Rotate secrets via SOPS
status: authoritative
last_reviewed: 2026-04-20
owner: claude
---

# Rotate secrets via SOPS

> Workflow opérationnel pour éditer, ajouter ou rotater un secret chiffré avec SOPS + age.
> Pose la clé age dans `/opt/academie-shared/secrets/age.key` (chmod 600, out-of-repo).

## Fichiers chiffrés actuels

| Fichier | Contenu | Déchiffré à | Mode SOPS |
|---|---|---|---|
| `webapp/.env.sops` | `DATABASE_URL`, `DIFY_KEY_TEACHER`, `JWT_SECRET_KEY`, `JWT_REFRESH_SECRET`, `INTERNAL_API_TOKEN`, feature flags | `webapp/.env` (gitignored) | dotenv per-var |
| `litellm/config.yaml.sops` | OpenAI key (3×, dont 2 fine-tunes), Groq keys (4×), Mistral, Ollama-Cloud, DB password (`database_url`) | `/opt/litellm/config.yaml` (hors repo, gitignored par prudence) | yaml avec `encrypted_regex: '^(api_key\|database_url\|master_key\|salt_key)$'` (model names / params / commentaires restent diff-readable) |
| `petit-pont-infra/secrets/shared.yaml.sops` (post-S62, ex `secrets/shared.yaml.sops` dans repo academia) | 9 secrets file-based : `dify-admin-key`, `dify-teacher-key`, `groq-key-2`, `jwt-{refresh-,}secret`, `n8n-encryption-key`, `ollama-cloud-key`, `pg-password`, `restic-passphrase` | `/opt/academie-shared/secrets/<name>` (chmod 600, sinse:sinse, trailing `\n` préservé) | yaml default (tous les values chiffrés, keys = filenames en plaintext) |

### Redondance avec autres bundles

Certains secrets du bundle `petit-pont-infra/secrets/shared.yaml.sops` sont des copies de référence — la source canonique est ailleurs. Quand tu rotates la source canonique, **rotate aussi ici** pour maintenir la parité :

| Filename | Canonique | Consommateur du fichier |
|---|---|---|
| `jwt-secret` | `webapp/.env.sops` (`JWT_SECRET_KEY`) | aucun direct — copie DR |
| `jwt-refresh-secret` | `webapp/.env.sops` (`JWT_REFRESH_SECRET`) | aucun direct — copie DR |
| `pg-password` | `webapp/.env.sops` (`DATABASE_URL`) + `litellm/config.yaml.sops` | 3 scripts (`profil_manager.py`, `inject_curriculum_anglais.py`, `e2e_onboarding_test.py`) |
| `groq-key-2` | `litellm/config.yaml.sops` (sinse-alt groq) | aucun direct — copie DR |
| `ollama-cloud-key` | `litellm/config.yaml.sops` (ollama) | aucun direct — copie DR |
| `dify-admin-key` | **canonique ici** | 3 scripts Dify orchestration |
| `dify-teacher-key` | **canonique ici** | 2 scripts E2E tests |
| `n8n-encryption-key` | **canonique ici** (et dans config n8n hors repo) | n8n process (triple backup critique, si perdu → workflows illisibles) |
| `restic-passphrase` | **canonique ici** | `/root/sinse-tools/restic-backup` (niveau 3 chiffré, si perdu → backups illisibles) |

## Prérequis

- `sops` CLI (`/usr/local/bin/sops`, v3.12+)
- `age` CLI (apt `age` package)
- Clé privée : `/opt/academie-shared/secrets/age.key` (chmod 600)
- Public key déclarée dans `.sops.yaml` racine repo : `age18jr3jdq05a4wr9hdgpdfz3vtya9u4rng88tu58lnv7jlw5hkxszsl00nnv`

## Éditer un secret existant

```bash
cd /opt/academia
SOPS_AGE_KEY_FILE=/opt/academie-shared/secrets/age.key \
  sops webapp/.env.sops
# ou:
SOPS_AGE_KEY_FILE=/opt/academie-shared/secrets/age.key \
  sops litellm/config.yaml.sops
```

→ Ouvre `$EDITOR` avec le contenu déchiffré. À la sauvegarde, SOPS ré-encrypte automatiquement. Commit le `.sops` mis à jour.

## Ajouter une nouvelle variable / clé BYOK

Même commande — pour `.env.sops` ajouter une ligne `NEW_KEY=value`. Pour `config.yaml.sops`, ajouter un bloc `model_name: ...` complet sous `model_list:` puis `api_key: "gsk_..."` au bon endroit. SOPS chiffre automatiquement les champs matchant `encrypted_regex` (api_key + database_url + master_key + salt_key).

## Déployer après modification

**webapp** :
```bash
cd /opt/academia/webapp
./decrypt-secrets.sh
docker compose -f docker-compose.webapp.yml up -d --force-recreate --no-deps academie-api
```

`docker compose restart` ne relit PAS `env_file` — toujours `up -d --force-recreate` pour webapp.

**LiteLLM** :
```bash
/opt/academia/litellm/decrypt-config.sh
docker restart litellm-proxy
# Patienter ~20-30s (prisma migrations + startup) puis tester:
curl -s http://127.0.0.1:4000/health/liveliness
```

`docker restart` suffit pour LiteLLM (bind mount `/opt/litellm/config.yaml` → `/app/config.yaml`, le process relit au startup).

**Downtime LiteLLM ≈ 20-30s** : chat Dify → LiteLLM casse le temps du restart. Prévoir bas usage pour rotations non-urgentes.

**Shared secrets** :
```bash
/opt/petit-pont-infra/secrets/decrypt-shared.sh
# Restart des consommateurs selon le secret édité :
#   - dify-*          → docker restart dify-api dify-worker dify-plugin-daemon
#   - pg-password     → aucun (scripts les relisent à chaque run)
#   - n8n-encryption  → docker restart n8n-academie (⚠ workflows illisibles si mismatch)
#   - restic-passphrase → aucun (restic relit à chaque backup)
```

Le wrapper est idempotent, préserve l'ownership (sinse:sinse) et ajoute un trailing `\n` (format attendu des consommateurs).

## Rotater la clé age (compromis, rotation périodique)

1. Générer nouvelle keypair : `age-keygen -o /tmp/new-age.key`
2. Ajouter la nouvelle public key dans `.sops.yaml` (garder l'ancienne temporairement)
3. Ré-encrypter tous les `.sops` : `sops updatekeys webapp/.env.sops`
4. Remplacer l'ancienne clé privée : `mv /tmp/new-age.key /opt/academie-shared/secrets/age.key && chmod 600 …`
5. Mettre la nouvelle clé privée dans le password manager de Sinse (et sauvegarder l'ancienne le temps de vérifier)
6. Retirer l'ancienne public key de `.sops.yaml` + `sops updatekeys` à nouveau
7. Commit + redeploy

## Disaster recovery (host wiped)

1. Installer `sops` + `age` (`apt install age` + binary GitHub pour sops v3.12+)
2. Restaurer la clé age depuis le password manager → `/opt/academie-shared/secrets/age.key`, chmod 600
3. `chown sinse:sinse /opt/academie-shared/secrets/age.key`
4. `cd /opt/academia/webapp && ./decrypt-secrets.sh` → régénère `webapp/.env`
5. `/opt/academia/litellm/decrypt-config.sh` → régénère `/opt/litellm/config.yaml`
6. `/opt/petit-pont-infra/secrets/decrypt-shared.sh` → régénère les 9 fichiers sous `/opt/academie-shared/secrets/`
7. Reprendre le deploy normal : `docker compose -f webapp/docker-compose.webapp.yml up -d` + `docker restart litellm-proxy` (si le container existe déjà) ou `docker run` selon l'historique orchestration

## Vérifier la santé du setup

**webapp** (round-trip strict, byte-identical) :
```bash
SOPS_AGE_KEY_FILE=/opt/academie-shared/secrets/age.key \
  sops -d --input-type dotenv --output-type dotenv webapp/.env.sops | diff - webapp/.env
```

**litellm** (round-trip sémantique — SOPS yaml reformate indentation/commentaires) :
```bash
SOPS_AGE_KEY_FILE=/opt/academie-shared/secrets/age.key \
  sops -d --input-type yaml --output-type yaml litellm/config.yaml.sops | diff - /opt/litellm/config.yaml
```

Attendu litellm : **zéro diff** si `decrypt-config.sh` a été lancé après la dernière édition de `.sops`. Si diff → relancer le wrapper avant `docker restart litellm-proxy`.

## Anti-patterns

- ❌ **Ne jamais** committer `webapp/.env` ou `/opt/litellm/config.yaml` (plaintext) — gitleaks bloque, `.gitignore` aussi
- ❌ **Ne jamais** committer la clé privée age (elle vit dans `/opt/academie-shared/secrets/`, hors du repo `/opt/academia`)
- ❌ **Ne pas** éditer `.env.sops` / `config.yaml.sops` à la main — utiliser `sops <file>` pour garder l'intégrité du format
- ❌ **Ne pas** oublier de backup la clé age avant de renverser son host — sans elle, les `.sops` deviennent irrécupérables
- ❌ **Ne pas** committer les plaintext ronces de build : `webapp/.env`, `litellm/config.yaml` (dans le repo), `*.backup*` — couvert par `.gitignore` mais à double-checker manuellement

## Auth hardening (post-Session 31)

- `pg_hba.conf` : **`trust` retiré sur `127.0.0.1/32` + `::1/128`** (remplacé par `scram-sha-256`). `local` socket reste `trust` car utilisé par `pg-backup` via `docker exec pg_dump` (socket unix, pas TCP). Backup : `/mnt/cosmos-data/postgres/pg_hba.conf.bak-2026-04-20`. Reload via `SELECT pg_reload_conf();` (non-disruptif).
- **pre-commit gitleaks** : hook trackable dans `.githooks/pre-commit` (active via `git config core.hooksPath .githooks`). Le hook legacy `.git/hooks/pre-commit` reste en place sur les hosts existants.

## Rotation non-interactive (`sops set`) — pattern Session 31

Quand `$EDITOR` n'est pas disponible (Claude en assistance, CI, script) — `sops set` modifie une valeur sans ouvrir l'éditeur :

```bash
# dotenv (webapp/.env.sops)
SOPS_AGE_KEY_FILE=/opt/academie-shared/secrets/age.key \
  sops set --input-type dotenv --output-type dotenv \
  webapp/.env.sops '["JWT_SECRET_KEY"]' '"'"$NEW_VALUE"'"'

# yaml (shared.yaml.sops ou litellm/config.yaml.sops)
SOPS_AGE_KEY_FILE=... sops set --input-type yaml --output-type yaml \
  /opt/petit-pont-infra/secrets/shared.yaml.sops '["pg-password"]' '"'"$NEW_VALUE"'"'

# yaml nested (litellm)
SOPS_AGE_KEY_FILE=... sops set --input-type yaml --output-type yaml \
  litellm/config.yaml.sops '["general_settings"]["database_url"]' '"'"$NEW_URL"'"'
```

Sans `--input-type` / `--output-type`, sops 3.12 auto-detect fail sur les .sops files (retourne "invalid character 'g' looking for beginning of value" — suggère JSON alors que c'est yaml/dotenv).

## Rotation complète (prod secrets rotated + git history rewrite)

Voir [ADR-012](../05-decisions/ADR-012-security-remediation-2026-04-19.md) pour le playbook complet Session 31.

**Checklist par secret** :

| Secret | Canonique (sops) | Runtime location | Rebuild requis ? | Restart service | Notes |
|---|---|---|---|---|---|
| `DIFY_KEY_TEACHER` | `webapp/.env.sops` + `shared.yaml.sops` | env academie-api | Non | `docker compose up -d academie-api` | Rotate dans Dify UI → API Access → Delete + Create |
| `DIFY_ADMIN_KEY` (`ADMIN_API_KEY`) | `shared.yaml.sops` | **Cosmos UI env var sur dify-api** | Non | Cosmos recreate auto | Pas dans sops (env Cosmos side), mais fichier DR dans shared |
| `JWT_SECRET_KEY` + `JWT_REFRESH_SECRET` | `webapp/.env.sops` + `shared.yaml.sops` | env academie-api | Non | `docker compose up -d academie-api` | Invalide toutes sessions users → re-login requis |
| `INTERNAL_API_TOKEN` | `webapp/.env.sops` | env academie-api + n8n workflows | **Oui si code code récent** | `docker compose build academie-api && up -d` + `docker restart n8n-academie` | **n8n SQL patch**: UPDATE `workflow_entity` + `workflow_history` (Session 27 gotcha) |
| `PG_PASSWORD` (user `sinse`) | `webapp/.env.sops` (`DATABASE_URL`) + `litellm/config.yaml.sops` (`database_url`) + `shared.yaml.sops` (`pg-password`) | env academie-api + litellm config + 4 Cosmos envs (`DB_PASSWORD` / `DB_POSTGRESDB_PASSWORD`) + **n8n credential "Postgres account"** (via n8n UI → Credentials) | Non | restart 5 services + `ALTER USER sinse PASSWORD '...'` | Fenêtre 30-60s downtime multi-service. **Oublier le n8n credential = workflows SQL renvoient body vide → cascade Dify "Output X missing".** |

### Gotchas Session 31

- **`docker compose up -d` sans `--build`** utilise l'image cachée → si le code source a changé depuis le dernier build, le container tourne avec l'ancien code. Toujours `docker compose build <service>` avant `up -d` quand la rotation dépend d'un commit récent (fail-fast env checks, par ex).
- **n8n workflow tables** : patcher `workflow_entity` (actif) **ET** `workflow_history` (snapshots) — sinon n8n peut restore l'ancienne valeur depuis history au prochain save de l'UI.
- **`pg_hba.conf` trust 127.0.0.1** : toute connexion depuis le container postgres via `psql -h 127.0.0.1` bypass le password check. Pour tester une rotation PG, utiliser une connexion docker network (depuis autre container vers `postgres-academie:5432`, force scram-sha-256).
- **Cosmos UI sauve immédiatement** : quand tu modifies un env dans Cosmos UI et cliques "Save", le container est recréé immédiatement. Pour rotation multi-service avec ALTER USER en parallèle, générer le nouveau password **d'abord**, sauvegarder tous les envs, puis ALTER USER au dernier moment (les 4 containers crash-loop entre Cosmos save et ALTER USER si l'ordre est inversé).

## Références

- [credentials.md](../04-infra/credentials.md) — stratégie globale secrets
- [ADR-012](../05-decisions/ADR-012-security-remediation-2026-04-19.md) — remédiation Session 31
- [SOPS docs](https://github.com/getsops/sops)
- [age docs](https://github.com/FiloSottile/age)
