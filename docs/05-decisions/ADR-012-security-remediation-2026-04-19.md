---
title: ADR-012 — Remédiation sécurité repo public (secrets leakés)
status: accepted
last_reviewed: 2026-04-20
decision_date: 2026-04-20
authors: [sinse, claude]
---

# ADR-012 — Remédiation sécurité repo public (secrets leakés)

## Contexte

Audit Session 29 (general-purpose agent, 6 min) sur `github.com/Sinsemilila/academIA` (public)
a révélé :

- **3 CRITIQUES** : 5 secrets en clair exposés dans le commit initial `71e1c4f` et
  encore présents dans des fichiers working-tree post-Session 18 SOPS migration.
- **Secrets concernés** :
  - `hABT7G9rcPMU3scyx-HY_HEEIRo3FG29` — password Postgres user `sinse` (actif prod, 3 DBs)
  - `app-REDACTED-TEACHER-PRE-S46-revoked` — clé API Dify Teacher (actif prod)
  - `academie-admin-a5c62b96f96fb8f0b3b05bea` — Dify `ADMIN_API_KEY` (workspace console)
  - `academie-ia-jwt-secret-2026-change-in-prod` — `JWT_SECRET_KEY`
  - `academie-ia-refresh-secret-2026-change-in-prod` — `JWT_REFRESH_SECRET`
- **Leaks secondaires** découverts en Session 30 :
  - `academie-internal-2026` (`INTERNAL_API_TOKEN`) — 12 occurrences history
  - `sk-litellm-master-key` — placeholder string jamais réellement utilisé (5 occurrences)

Commit `6a160fa` (fix audit antérieur) avait retiré du working tree mais **laissé
l'historique intact** + **raté `webapp/PLAN.md` ligne 178**.

Le commit Phase 1 Session 30 (`ffa761e` + `1ca28b5` + `9226b74`) a nettoyé le
working tree et remplacé les fallbacks de sécurité par des lectures `os.environ[...]`
fail-fast. Mais **les literals restaient dans l'historique git public** et les
containers prod utilisaient encore l'image cachée avec les anciennes valeurs.

## Options envisagées

### Option A — Rotation sans rewrite historique

- Pour : pas de rewrite destructif, pas de casse pour les clones tiers, aucun
  force-push.
- Contre : les secrets morts restent lisibles indéfiniment dans le repo public,
  y compris dans tout fork. Communication sur "bug de sécurité" obligatoire.

### Option B — Rewrite historique sans rotation

- Pour : historique propre rapidement.
- Contre : **inutile** — les secrets restent exploitables tant que pas rotés ;
  les clones tiers existants gardent l'ancien historique.

### Option C — Rotation + rewrite historique (retenue)

- Pour : secrets morts + historique public clean. Les clones tiers résiduels
  gardent l'ancien historique mais ses secrets sont inexploitables.
- Contre : force-push main (coordination), downtime multi-service 30-60s pour 2C,
  rotation invalide ~6 sessions users (JWT 2E).

## Décision

**Option retenue** : C (rotation complète + rewrite historique)

**Justification** : la présence de secrets en clair dans un repo public rend la
rotation indispensable (sans elle, toute personne ayant cloné le repo conserve
un accès prod). Le rewrite historique élimine l'exposition future : une fois
les secrets rotés, l'historique public nettoyé ne laisse plus aucune trace
exploitable. Le coût (30-60s downtime coordonné, 6 users à re-login, force-push
unique) est négligeable comparé à l'exposition continue.

## Conséquences

### Positives

- 7 secrets/literals rotés en prod + retirés de l'historique public.
- Image academie-api rebuild → fail-fast `os.environ[...]` Phase 1 actif en
  runtime (commits `1ca28b5`, `ffa761e` enfin effectifs).
- `.sops.yaml` pattern étendu pour inclure `INTERNAL_API_TOKEN` dans
  `webapp/.env.sops` (gap repéré pendant 2F).

### Négatives / acceptées

- Force-push main → clones tiers résiduels divergent (impact pratique nul
  puisque les secrets sont morts).
- 6 sessions users invalidées → re-login nécessaire.
- Commits SHA1 changés : `ffa761e`→`b5cfb50`, `1ca28b5`→`ae2ab38`,
  `9226b74`→`f9d4662` (entre autres). Toute référence externe à ces SHA
  (docs, tickets, PRs) devient stale.

### Neutres (à surveiller)

- **`pg_hba.conf` de postgres-academie autorise `trust` sur 127.0.0.1/::1/socket.**
  Hors scope aujourd'hui mais représente un contournement du mot de passe pour
  tout process ayant shell dans le container postgres.
- **`POSTGRES_PASSWORD=26051993++Sinse`** (user postgres superuser) stocké en
  clair dans `/mnt/cosmos-data/cosmos-config/backup.cosmos-compose.json`
  (lisible par user `sinse`, pas commité ni pushé). À rotater si ce backup
  fuite.
- **`SECRET_KEY` Dify** (signing secret interne) surfacé dans le transcript de
  cette session mais jamais commité — à garder stable (rotation casserait les
  sessions Dify actives et potentiellement des données chiffrées).
- **Dify workflow "Détection profil" a une branche courte fragile** : quand
  `dify-profil-get` (n8n) retourne un body vide/erreur, le code Dify exécute
  un fallback qui retourne seulement 13/28 outputs déclarés, ce qui crash le
  node (`Output exam_resume_active is missing`). Découvert à chaud pendant
  la vérif Phase 4 après que n8n a failli silencieusement (voir §gotchas
  ci-dessous). Fix à prévoir : ajouter les 15 champs manquants (valeurs
  défaut `False` / `""` / `0`) à la branche `if not body`. Pas urgent tant
  que n8n reste up.

## Actions de mise en œuvre

- [x] Phase 1 (Session 30, commits `9226b74` + `1ca28b5` + `ffa761e`) — redact
      working tree + fail-fast routers + scripts paramétrés env-var
- [x] Phase 2A — Dify Teacher key rotated via Dify UI + sops update + restart
- [x] Phase 2B — LiteLLM master_key check (NOOP, aucun master_key configuré)
- [x] Phase 2D — Dify `ADMIN_API_KEY` rotated via Cosmos UI env → recreate
- [x] Phase 2E — `JWT_SECRET_KEY` + `JWT_REFRESH_SECRET` rotated (openssl rand)
      + sops + restart
- [x] Phase 2F — `INTERNAL_API_TOKEN` rotated + ajouté à `webapp/.env.sops` (gap)
      + n8n workflows patched (`workflow_entity` + `workflow_history`, gotcha
      Session 27) + rebuild academie-api pour activer fail-fast Phase 1
- [x] Phase 2C — Postgres `sinse` user password rotated (ALTER USER) + sops
      update 3 fichiers + 4 Cosmos containers + restart 5 services
- [x] Phase 3 — `git filter-repo --replace-text` + `--replace-message` (fichiers
      + commit messages), `git push --force` vers origin
- [x] Phase 4 — smoke deep 21/21 ALL CLEAR, 106 academie-core tests pass,
      live user flow (Sinse) re-login + chat OK
- [x] Phase 5 — ADR-012 (ce doc) + update runbook `rotate-secrets-sops.md`
      + CHANGELOG + SESSION 31 prepend

## Gotchas opérationnels découverts pendant l'exécution

Notés pour éviter de les re-découvrir à la prochaine rotation :

1. **`docker compose up -d` sans `--build` utilise l'image cachée** — découvert
   pendant 2F. Les 3 commits Phase 1 (fail-fast sur routers) n'étaient pas
   runtime-actifs avant le rebuild explicite `docker compose build academie-api`.
   Runtime tournait encore sur l'image de Sprint 4 qui avait les fallbacks.
2. **n8n `credentials_entity` stocke les creds PG chiffrés séparément des env
   vars** — 2C a rotaté le password côté `DB_POSTGRESDB_PASSWORD` (env n8n =
   connexion à sa propre DB interne), MAIS les **nodes SQL des workflows**
   utilisent un credential nommé `Postgres account` (id `NpF5tjOzvAWkHR2n`)
   chiffré avec `N8N_ENCRYPTION_KEY`. Oublier de rotater ce credential a causé
   `dify-profil-get` à retourner HTTP 200 avec body vide → cascade Dify
   "Output exam_resume_active is missing". Fix via n8n UI → Credentials →
   Postgres account → update password → Test + Save.
3. **`sops set` requiert `--input-type/--output-type` explicites** pour les
   fichiers dotenv et yaml, sinon `Error unmarshalling input json: invalid
   character 'g'`. Voir runbook pour syntaxe exacte.
4. **Cosmos UI "Save" recrée le container immédiatement** — si tu modifies
   env d'un container dans Cosmos UI AVANT de rotater côté PG, le container
   crash-loop jusqu'au ALTER USER. Inverser l'ordre (ALTER USER d'abord) évite
   le crash mais crée des failures sur les containers restant à old-creds.
5. **n8n `workflow_entity` + `workflow_history` doivent matcher** (Session 27
   gotcha confirmée). Ne patcher qu'un des deux laisse l'autre comme ground
   truth que n8n peut restaurer au prochain save UI.
6. **Terminal wrapping de commandes longues** — `sops ... --output-type yaml /path/long`
   splitté visuellement par le terminal a été interprété comme 2 commandes par
   bash → "Error: no file specified". Préférer commandes courtes via `cd` ou
   via script.

## Re-évaluation

À faire (follow-ups ouverts) :

- **Audit pre-commit gitleaks hook** — ajouter `gitleaks` en pre-commit pour
  éviter récurrence. Le commit Phase 2 actuel a bien passé `gitleaks` au
  commit — confirme que le tooling est disponible mais pas strictement
  appliqué à tous les commits historiquement.
- **Rotation POSTGRES_PASSWORD superuser** — dans les 7 jours si le backup
  Cosmos a été exposé ; sinon calendrier trimestriel.
- **Durcir `pg_hba.conf`** — retirer `trust` sur 127.0.0.1 au profit de
  `scram-sha-256` (impose password même pour loopback).
- **Fix Dify "Détection profil" short-branch** — ajouter les 15 outputs
  manquants (`exam_resume_active`, `exam_resume_mode`, …) avec valeurs défaut
  dans le `if not body` fallback. Trivial côté code, nécessite `DIFY_ADMIN_KEY`
  pour publish depuis script.

## Références

- Session 30 audit + Phase 1 commits : `9226b74`, `1ca28b5`, `ffa761e`
- Phase 2 commit post-rotation : `b5cfb50` (était `ffa761e` avant rewrite)
- `docs/99-runbooks/rotate-secrets-sops.md` (procédure opérationnelle)
- `/tmp/secrets-to-redact.txt` — redact list 7 entrées utilisée par filter-repo
- Session 27 gotcha n8n : patch `workflow_entity` + `workflow_history` (les
  deux tables doivent être update en cohérence, sinon n8n re-spawn l'ancienne
  valeur depuis history)
