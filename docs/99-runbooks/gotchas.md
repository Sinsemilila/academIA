---
title: Gotchas — known issues and workarounds
status: authoritative
last_reviewed: 2026-04-15
---

# Gotchas — known issues and workarounds

> Pièges connus, bugs récurrents, workarounds à se rappeler. À enrichir au fur et à mesure.

## Dify

- **dify-plugin-daemon** était instable au démarrage du projet (avril 2026), s'est auto-stabilisé. Ne pas restart sans raison.
- **dify-sandbox** requis pour Jinja2 dans les LLM code nodes. Déployé 2026-04-05.
- **sys.user_id** dans Chatflow Dify = UUID du compte Dify, **pas** un username. Pour résoudre vers notre `eleves.username`, utiliser `eleves.dify_user_id` mapping dans les workflows n8n.
- **var_assigner** : l'opération `set` ne supporte pas `input_type: "variable"`. Utiliser mode `over-write`. Bug connu Dify, workaround à retenir.
- **code_eval_check** : si LLM envoie `[EVAL_READY]` seul sans texte, `cleaned_text` devient "" → message vide chez l'user. Fallback FR implémenté Session 11 (2026-04-15), cf. `scripts/fix_eval_ready_fallback.py`.
- **Dify provider models** : utilise `openai_api_compatible` pour pointer vers LiteLLM, pas vers OpenAI direct. Tous les aliases (`gpt-4o-mini`, `groq-standard`, etc.) sont des aliases LiteLLM internes, pas des modèles OpenAI natifs.

## LiteLLM

- **Groq rate limits** : `groq-standard` (Llama 3.3 70B) peut 429 sous charge. Fallback configuré : `mistral-small`.
- **CJK** : `groq-standard` et `groq-snapshot` ne supportent pas CJK. Pour japonais/chinois futur, utiliser `groq-qwen` (Qwen 2.5).
- **SpendLogs batch** : LiteLLM logue les tokens en batch (~30-60s de délai), pas en temps réel. Pour décision sub-second (auto-switch quota), on garde un compteur tiktoken local en parallèle (cf. Session 12).
- **Config.yaml non-versionné** : `/opt/litellm/config.yaml` n'est pas dans un git repo. Les modifs sont manuelles. À migrer vers SOPS-encrypted dans repo (cf. [`04-infra/credentials.md`](../04-infra/credentials.md)).
- **Gemini free tier** : quota très limité (~10 req/jour sans billing). Pas utilisable en prod.

## PostgreSQL

- **Password** : stocké dans `/opt/academie-shared/secrets/pg-password` — JAMAIS commit en clair.
- **PG data** : sur `/mnt/cosmos-data/postgres/` (bind mount, 850G disk, séparé du boot).
- **Dump restore** : les erreurs "already exists" sur les constraints lors d'un restore sont normales, ignorer.
- **Multi-database** : même instance PG gère `academie_db` + `litellm_db` + `dify_plugin`. `academie-api` a 2 pools (1 pour chaque DB qu'il touche).

## n8n

- **Encryption key** : si perdue, TOUS les workflows deviennent illisibles. Stockée à 3 endroits (triple-backup) dans `/opt/academie-shared/secrets/`.
- **Access UI** : tunnel SSH requis : `ssh -L 5678:127.0.0.1:5678 cosmos`. Ou via `n8n.petit-pont.com` (Cloudflare Tunnel).
- **Webhooks** : les workflows expose des webhooks HTTP. Dify les appelle via `http://n8n-academie:5678/webhook/...`. Tester via `curl` depuis le container.

## Webapp

- **Cloudflare Zero Trust** : policy configurée Bypass + require WARP + France. Pas de login Cloudflare à afficher.
- **Restart `academie-api`** : si on modifie le code `webapp/backend/app/*.py`, docker **ne bind-mount pas** la source → il faut **rebuild** l'image (`docker compose build academie-api && docker compose up -d academie-api`). Piège fréquent lors des dev rapides (cf. Session 12).
- **`docker compose restart` ne relit PAS `env_file`** : ajouter une variable dans `webapp/.env` nécessite `docker compose -f docker-compose.webapp.yml up -d --force-recreate --no-deps academie-api`. Un simple `restart` garde les anciennes vars d'environnement dans le container (cf. Session 18).
- **Build frontend** : similaire — le code SvelteKit est baked dans l'image, rebuild requis pour changements.

## Infrastructure

- **Boot disk (50G)** : surveiller via `smoke-test --infra`. Était 83% plein avant S1 (avril 2026), libéré ~9.5 GB via `docker builder prune`.
- **cosmos-server `image: :latest` + `AutoUpdate=false`** : depuis Session 18 bis, cosmos ne pull plus automatiquement. Conséquence : **on maintient manuellement** — surveiller les CVEs et releases cosmos, décider quand pull. Le tag `:latest` reste fragile en DR (si le host se ré-provisionne, docker pull `:latest` récupère whatever est publié à ce moment, potentiellement une version incompatible avec la `cosmos.config.json` archivée). Pin digest à prévoir lors du bundle hardening L2/L3. Toggle AutoUpdate se fait via edit direct `/mnt/cosmos-data/cosmos-config/cosmos.config.json` (UI n'expose pas la clé) + `docker restart cosmos-server` (downtime ~10-15s sur les 5 routes edge).
- **cosmos privileged + docker.sock + `/:/mnt/host`** : ~~surface d'attaque énorme~~ → **drastiquement réduit Sessions 18 ter + 23** : Session 18 ter a posé L1-L3 (`privileged: false` + `cap_add: NET_ADMIN` + dbus retiré + `/:/mnt/host:ro` + image digest pinnée). **Session 23 (2026-04-16) applique L4** via `tecnativa/docker-socket-proxy:0.3.0` interposé sur `tcp://127.0.0.1:2375` (cf. [ADR-010](../05-decisions/ADR-010-cosmos-L4-docker-socket-proxy.md)). Cosmos n'a plus docker.sock mount — passe par le proxy qui bloque `/build`, `/commit`, `/services`, `/plugins`, `/secrets`, `/configs` + start d'exec instances (`/exec/{id}/start` → 403). Limitation connue : `POST /containers/{id}/exec` passe (création d'exec dormant — start bloqué). L5 (remplacement cosmos par traefik/caddy) reste backlog pour éliminer complètement le socket. Rollback script prêt : `/opt/academie-shared/secrets/cosmos-pre-L4-rollback.sh` (chmod +x, garder 7j jusqu'à 2026-04-23).
- **cosmos `--hostname cosmos-server` est OBLIGATOIRE** (découvert Session 18 ter le hard way) : sans hostname explicite, cosmos's `isInsideContainer` check fail → cosmos crée un nouveau config vide à `/var/lib/cosmos/cosmos.config.json` au lieu de lire `/config/cosmos.config.json` (bind mount) → routes redirigent toutes vers `/cosmos-ui/` setup wizard. Symptôme : 5/5 routes répondent HTTP 307 vers `/cosmos-ui/` au lieu de leur backend. Fix : `--hostname cosmos-server` dans `docker run` ET `hostname: cosmos-server` dans `cosmos.docker-compose.yaml`. Aussi `--cgroupns host` recommandé (default Docker récent = private). Script rollback : `/opt/academie-shared/secrets/cosmos-rollback.sh.bak` (contient `docker run` original avec `--privileged` + dbus + `/` RW + `--hostname` + `--cgroupns host`).
- **Cosmos rewrite `cosmos.docker-compose.yaml` proactivement** : tout edit manuel de ce fichier est susceptible d'être écrasé. Cosmos garde son own state via Docker daemon. Pour modifier la spec runtime de cosmos, utiliser `docker rm -f cosmos-server && docker run` (cf. session 18 ter), et accepter que le compose file diverge.

## Edge layer (Cosmos + CF Access + CF Tunnel) — patterns structurels

Ces 3 items ne sont **pas des bugs à fixer** mais des contraintes structurelles de la pile edge. Documentées ici pour que tout futur fix qui touche au traffic entrant part de la bonne hypothèse.

- **Cosmos hardcode CSP `'self'` sur toutes routes SERVAPP** (découvert Session 47 B4) — les directives `default-src 'self'; script-src 'self' 'unsafe-inline'; connect-src 'self'…` sont rajoutées systématiquement par Cosmos devant chaque route, même avec `DisableHeaderHardening: true` + `SmartShield: false` + `ExtraHeaders.Content-Security-Policy: ...` custom. Cosmos append son CSP par-dessus, ne remplace pas. **Pattern de workaround** : si un SDK/script externe doit POST vers un autre domain que le site (ex. GlitchTip envelope → glitchtip.petit-pont.com), tunneler via path **same-origin** déjà couvert par `'self'` (ex. `/api/sentry-tunnel` exposé par FastAPI qui fait le POST serveur-side). Jamais tenter de whitelister le domain cible dans connect-src en passant par Cosmos — ça ne prend pas.

- **CF Access path-precedence broken pour bypass paths** (découvert Session 47 B4) — la doc Cloudflare dit "more specific path wins", mais en pratique quand le browser envoie les cookies CF Access d'une app **A** (broad, ex. `academie.petit-pont.com/*`), CF priorise A sur une app **B** configurée `academie.petit-pont.com/api/sentry-tunnel` même si B est path-specific. Résultat : 403 silent sur le path censé être bypass. **Pattern de workaround** : soit (1) tunneler les requests via un path **déjà couvert par le cookie existant** (ex. `/api/*` couvert par l'app main academie → le tunnel s'exécute avec l'auth user existante), soit (2) restructurer l'app matière pour que B soit un sous-domain dédié (plus lourd). Option 1 est la bonne sur cette pile.

- **GlitchTip envelope ingest auth via query param obligatoire** (Session 47 B4) — le Sentry SDK ajoute auto `?sentry_version=7&sentry_key=<DSN.username>` sur le POST envelope. Un proxy custom (ex. `/api/sentry-tunnel`) qui forward l'envelope **DOIT** extraire le `sentry_key` de la première ligne JSON de l'envelope et le remettre en query param côté GlitchTip — sinon 403 silent. Le code est déjà en place dans `backend/app/routers/sentry_tunnel_router.py` (Session 47 PR #27). À ne jamais oublier si on réimplémente un proxy similaire.

## Sprint 3 — Teacher prompts

- **`scripts/update_teacher_chatflow.py` `if __name__` guard ajouté Session 21 Phase 4** : import du module ne déclenche plus le deploy. CLI `--target draft|published|both` (default both pour backward compat) + `--use-v2` flag (default False).
- **PROMPT_SESSION_V2 wired conditionnellement** via `--use-v2` flag dans `patch_graph()`. Sans `--use-v2`, le script déploie V1 (PROMPT_SESSION).
- **🟢 Sprint 3 V2 hang Session 21 = TRANSIENT (Phase 4-bis resolved Session 22)** : initial symptom (curl timeout 30s après swap draft V2 → published + restart dify-api) NON REPRODUCTIBLE. Preview draft = 2.14s OK. Repro contrôlé en published via chat_router réel (8 inputs populés par `build_dynamic_sections` avec contenu réel rubric/fewshots/l1_watch/output_schema) = 2.72s OK. **Les 4 hypothèses initiales** (paragraph vs text-input, placeholders, sandbox kwargs, `<output>` wrapping) sont toutes ÉLIMINÉES. Cause probable = outage LiteLLM/Groq transient ou race restart+1st chat au moment précis du test Session 21.
- **Rollback script** `/opt/academie/scripts/rollback_teacher_v2_to_v1.sh <backup.json>` : `pg_read_file` a besoin que le fichier soit **dans `/var/lib/postgresql/`** (pas `/tmp`) et owned par postgres user — sinon UPDATE silent no-op. Le script gère via `docker cp + chown postgres:postgres`.
- **Phase 5 battery** `scripts/sprint3/eval_live_battery.py` : hit chat_router → Dify V2 live, 4 personas × 10 turns + 6 edge cases. Pass rate 97.4% ≥ 95% threshold. **Detect onboarding automatiquement** (absence de `<output>` tags) et exempte ces turns des asserts V2 (PROMPT_ONBOARDING intouché par V2 donc pas de format JSON attendu).
- **Profile seeding via `profils_eleves` UPDATE ne suffit pas à forcer session flow** : seeder niveau_global + onboarding_completed_at n'empêche pas Dify de router vers onboarding pour les 2 premières personas de la battery. Le vrai switch onboarding→session est décidé par `code_profil_check` + `if_eval_ready` dans le graph Dify (logique interne non-trivial). La battery bypass le problème via auto-detect.

## Token tracking (gpt-4o-mini)

- **Le headline /admin shows `tokens × 1.10` (safety margin)** depuis Session 19 — display intentionnellement supérieur de 10% aux comptes bruts, pour rester ≥ OpenAI dashboard. La valeur brute est dans `tokens_raw`. La règle : "/admin légèrement plus haut OK, plus bas dangereux" (auto-switch quota).
- **`get_gpt4o_usage` combine 3 sources** = local tiktoken (sub-second) + LiteLLM SpendLogs (~30-60s lag, fine-tunes inclus) + OpenAI Usage API (lazy reconciliation toutes les 15 min). MAX gagne. Le compteur in-memory ne décroît jamais.
- **Le bg task de reconciliation dépend de l'admin key OpenAI** à `/run/academie-secrets/openai-admin-key` dans le container (bind RO depuis `/opt/academie-shared/secrets/`). Si `openai_tokens=0` dans `token_usage_daily`, soit la clé est absente, soit l'API a fail. Vérifier les logs `academie-api | grep openai_reconcile`.
- **Rotation admin key** : `sops secrets/shared.yaml.sops` → modifier `openai-admin-key:` → save → `./secrets/decrypt-shared.sh` → `docker compose up -d --force-recreate academie-api`. Pas de downtime apparent (env_file preservé, juste le file mount qui change).
- **Token usage backfill row** : il existe un row `request_id='backfill-2026-04-15-pre-litellm-activation'` dans `LiteLLM_SpendLogs` qui injecte 48,111 tokens fictifs daté `2026-04-15 00:00:00` (snapshot pre-LiteLLM Session 12). Inflate le total tracké LiteLLM mais reste cohérent avec OpenAI dashboard (qui sait aussi que ces tokens existent réellement). À garder.
- **Data disk (850G)** : `/mnt/cosmos-data/`, PG data + backups. Quasi vide.
- **Proxmox** : vzdump backups sur boot SSD (différent du disque data) = bonne pratique ✅

## Scalabilité / limites

- ⚠️ **`academie-net-bridge` est en /28 (14 IPs)** : 12 utilisées, 2 seulement dispos. Ajouter un container = galère (recréation du bridge en /27 nécessaire, donc downtime global).
- ⚠️ **Dify workflow_node_executions = 82 MB** (30K rows) + **workflow_runs = 55 MB** : **accumule sans purge**. Script de purge périodique à prévoir (rétention 30 jours ?).
- ⚠️ **`dify-plugin-daemon` image = 2.14 GB** + **dify-api = 3.99 GB** — gros images, à surveiller au boot disk.
- ⚠️ **Dangling volume 820 MB** (`16f29bdb9119…`) non attaché — `docker volume prune` pour nettoyer.
- ⚠️ **Qdrant référencé dans env dify-api** (`QDRANT_HOST=qdrant-server`) mais pas de container correspondant → dead pointer (ne casse rien tant qu'on ne touche pas le RAG).
- ⚠️ **`cosmos-server` privileged + host network + `/` bind-mount + docker.sock** : point d'entrée très sensible. Risque compromission élevé → **revue sécurité obligatoire avant SaaS public**.

## Workflows n8n

- **DOUBLON** : deux workflows nommés `dify-diagnostic` coexistent avec le même webhook path (`f79033231f7644` créé 2026-04-13, `58dd0014770a4c` créé 2026-04-06). n8n route aléatoirement vers l'un des deux → **bug à résoudre**. Un seul devrait être actif.
- **Fail rates élevés** :
  - `dify-snapshot` : **17%** (25 fails / 144 runs) ⚠️
  - `dify-diagnostic` : **28%** (9 fails / 32 runs) ⚠️
  À investiguer via `docker logs n8n-academie` + table `execution_entity`.

## LiteLLM

- **`mistral-small` rpm=2** : seulement 2 requêtes/minute autorisées. Si fallback chain cascade sur Mistral (gpt-4o-mini → groq-standard → mistral-small) et que Mistral est saturé → erreur 429 terminale. Goulot d'étranglement potentiel.
- **SpendLogs batch** : écriture en batch (~30-60s de lag). Pour décision sub-second (auto-switch), on garde compteur tiktoken local en parallèle.
- **Config.yaml non-versionné** : `/opt/litellm/config.yaml` pas dans git. Modifs manuelles uniquement. À migrer vers SOPS.
- **Tables `LiteLLM_*` en shadow dans `academie_db`** (toutes quasi-vides) + **vraies dans `litellm_db`** : artefact de migration Prisma. Toujours query `litellm_db` pour les vraies données.

## Backend / Frontend

- **Seul `DIFY_KEY_TEACHER` est configuré** dans `.env`. Les 6 autres agents (Maestro, Sensei, Lehrer, Professore, PyMentor, CyberMentor) ont des apps Dify créées en mode `chat` simple mais **leur key n'est pas dans le .env** → appel `/api/chat/send?agent=maestro` retournerait 404 via `get_dify_key()`.
- **Rebuild obligatoire** : changer du code Python dans `webapp/backend` ou Svelte dans `webapp/frontend` nécessite `docker compose build` + `up -d`. Pas de hot-reload (source bakée dans l'image).
- **Deux tables utilisateur** coexistent : `eleves` (origine Dify-seul) et `users` (ajoutée pour la webapp). Font double-emploi sur certaines colonnes. À rationaliser.
- **Table `curriculum_concepts` N'EXISTE PAS** : les concepts sont JSONB dans `curriculums.concept_keys/weights/groups`. Si tu cherches un script qui fait `SELECT * FROM curriculum_concepts`, c'est qu'il est obsolète ou à refactorer.

## Scripts d'admin

- **`update_teacher_chatflow.py`** : re-déploie le chatflow Dify Teacher entier. Idempotent mais touche la DB directement (pas d'API Dify).
- **`update_teacher_onboarding.py`** : **n'est pas idempotent** dans sa version actuelle — re-run créera des duplicats de nodes. Utiliser `fix_eval_ready_fallback.py` pour des modifs ciblées.
- **`fix_eval_ready_fallback.py`** : patch one-shot, idempotent via match sur node id.

## Secrets

- **Tous les secrets** dans `/opt/academie-shared/secrets/` avec chmod 600.
- **Migration** : historique, les secrets étaient dispersés. Migrés vers emplacement unique (S2.1, 2026-04-12).
- **Claude native memory** avait ADMIN_KEY en clair par le passé — remplacé par référence au fichier secret.

## Références

- [deployment.md](../04-infra/deployment.md) — stack complet
- [credentials.md](../04-infra/credentials.md) — gestion secrets
- [../_legacy/gotchas.md](../_legacy/gotchas.md) — version legacy (source de ce fichier)
