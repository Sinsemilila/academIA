---
title: Data Model
status: authoritative
last_reviewed: 2026-04-16
---

# Data Model

> Schéma PostgreSQL actuel (`academie_db`) + cible avec la refonte taxonomie v2 et l'extension multi-domaine.

## Vue d'ensemble (état 2026-04-15)

**PostgreSQL 16.13** via container `postgres-academie`. 4 databases :

| Database | Taille | Rôle |
|---|---|---|
| `academie_db` | **198 MB** | Mégabase — mix de 5 systèmes : AcademIA natif + Dify + n8n + LiteLLM shadow + chat_hub |
| `litellm_db` | 11 MB | LiteLLM spend logs (source de vérité tracking, cf. Session 12) |
| `dify_plugin` | 8.3 MB | Dify plugin daemon state |
| `postgres` | 7.5 MB | Maintenance |

**`academie_db` contient 250 tables** dans le schéma `public` (184 MB, 642 indexes, 121 foreign keys, 51 unique constraints). Cette mixité est héritée de choix d'origine (Dify + n8n configurés pour utiliser la même DB que l'app). Une séparation future est envisageable mais non prioritaire.

**Observation importante** : les tables `LiteLLM_*` existent **en doublon** (shadow dans `academie_db`, réelles dans `litellm_db`). Les shadows sont vides — artefact de migration Prisma. La source active est `litellm_db`.

## Tables AcademIA natives (état 2026-04-15)

### `eleves` — 38 rows
Table simple. Colonnes : `id` (serial PK), `username` (varchar 100 unique), `created_at`. FKs entrantes depuis : `error_log`, `users`, `historique_sessions`, `profils_eleves`, `snapshots_session`.

### `users` — 6 rows (table séparée !)
Colonnes : `id`, `username`, `display_name`, `email`, `password_hash`, `eleve_id` FK, `avatar_color`, `exam_access`, `is_admin`, `dify_user_id`, `daily_goal_minutes` (default 15), `theme`, `last_seen_at`.

**Attention** : deux tables utilisateur coexistent (`eleves` pour le pédagogique, `users` pour l'auth/webapp). Historique lié à l'évolution du projet (eleves venait de la phase Dify seule). À rationaliser dans une future refonte data model.

### `profils_eleves` — 12 rows — profils pédagogiques
```sql
eleve_id              INT REFERENCES eleves(id)
domaine               VARCHAR     -- 'anglais', 'espagnol', 'python', 'cybersec', ...
niveau_global         VARCHAR     -- 'A1' → 'C2' (langues) ou 'débutant' → 'expert' (autres)
scores_confiance      JSONB       -- {concept_key: 0-100}
details_par_competence JSONB      -- {skill: {score, notes, ...}}
points_forts          JSONB
lacunes               JSONB
plan_sessions         JSONB
mode_apprentissage    VARCHAR     -- 'libre' | 'guidé' | 'examen'
personnalite          JSONB       -- copie pour le Domain
diagnostic_justification TEXT
diagnostic_exchange_count INT
auto_eval_level       VARCHAR
onboarding_completed_at TIMESTAMP
derniere_session      TIMESTAMP
l1                    VARCHAR(2) DEFAULT 'fr'   -- ISO-639-1 (Sprint 3 Phase 6, 2026-04-16)
l1_watch_enabled      BOOLEAN NOT NULL DEFAULT TRUE   -- toggle Teacher L1_WATCH block
UNIQUE (eleve_id, domaine)
```

**Observation** : colonne `domaine` = partition par domaine déjà en place ✅. Bon pour le multi-domaine.

### `snapshots_session` — 8 rows
Colonnes (après Sprint 2 Phase A, 2026-04-15) :
- `id`, `eleve_id`, `domaine`, `contenu` (text), `created_at`
- **Nouvelle Sprint 2 Phase A** : `schema_version INTEGER NOT NULL DEFAULT 2`
  - Les 8 existants ont été backfillés à `schema_version=1`
  - Les nouveaux auront `schema_version=2` par défaut (cut-off ADR-007 option C)

Archive v1 : table **`snapshots_session_v1_archive`** (8 rows copiées). Structure identique à v1 (sans `schema_version`). Référence historique.

⚠️ `contenu` reste TEXT libre pour l'instant. La structuration JSONB typée viendra en Phase B du Sprint 2 (refactor code snapshot generator + JSON Schema validation).

### `error_log` — 9 rows (en accumulation)
Colonnes (après Sprint 2 Phase A, 2026-04-15) :
- Original : `id` (bigint), `eleve_id`, `session_id`, `turn_number`, `error_code` (varchar 20), `original_text`, `suggested_correction`, `llm_reasoning`, `analysis_model` (default `gpt-4o-mini`), `snapshot_id` FK, `created_at`
- **Nouvelles Sprint 2 Phase A** (nullable, populées progressivement par Phase B) :
  - `tier VARCHAR(3)` — T0..T4 (CHECK contraint), indexé
  - `gravity_linguistic FLOAT` — 0.0..1.0
  - `gravity_communicative FLOAT` — 0.0..1.0
  - `gravity_social FLOAT` — 0.0..1.0
  - `criterial_level_emergence VARCHAR(3)` — A1..C2 (CHECK)
  - `criterial_level_mastery VARCHAR(3)` — A1..C2 (CHECK)

Indexes : 5 original + `idx_error_log_tier` (Sprint 2). Total 6 indexes.

Distribution actuelle (error_code) : V:FORM (2), N:COUNT (2), PREP:CALQUE (1), REG:LEVEL (1), V:INFL (1), SENT:SUBORD (1), ORTH:CASE (1).

Cf. [ADR-009](../05-decisions/ADR-009-gravity-axes-schema.md) pour le choix colonnes dénormalisées vs table séparée.

### `historique_sessions` — 0 rows
Définie mais vide actuellement. Colonnes : `id`, `eleve_id`, `domaine`, `resume_session`, `date_session`.

### `user_sessions` — 1 row (session active tracking)
Colonnes : `id`, `user_id`, `agent_name`, `dify_conversation_id`, `started_at`, `last_message_at`, `message_count`, `is_active`, `duration_seconds`, `last_snapshot_at`.

### `token_usage_daily` — 2 rows
PK `usage_date`. Colonnes : `tokens_used` (bigint), `model` (default `gpt-4o-mini`). Utilisé pour décision auto-switch sub-second (cf. chat_router.py).

### `curriculums` — 6 rows (1 par niveau CECRL)
Colonnes : `id`, `domaine`, `niveau`, `description`, `points_cles` (jsonb), `concept_keys` (jsonb array), `concept_weights` (jsonb), `concept_groups` (jsonb). Unique (domaine, niveau).

**Distribution actuelle** : 1 seul domaine (`anglais`), 6 niveaux, **98 concepts totaux** (A1=18, A2=18, B1=20, B2=18, C1=14, C2=10).

### ⚠️ `curriculum_concepts` N'EXISTE PAS

Il n'y a **pas** de table dédiée par concept. Les concepts sont stockés en **JSONB dans `curriculums`** :
- `concept_keys` : array des concept_key
- `concept_weights` : {concept_key: poids}
- `concept_groups` : {module: [concept_key]}

La refonte taxonomie v2 pourrait introduire cette table dédiée pour mieux tracker `emergence_level`/`mastery_level`/`family` par concept — à décider en Sprint 2.

### Autres tables AcademIA
- `streaks` (2 rows) : PK user_id, current/longest streak, last_active_date, total_sessions, freeze count
- `xp_log` (1 row) : id, user_id, amount, reason, agent_name, created_at
- `active_sessions` (0 rows) : tracking fine-grained sessions
- `accounts` (2 rows) : comptes webapp (OAuth-ready structure, inutilisée actuellement)
- `invitation_codes`, `whitelists`, `saved_messages`, `user_api_keys` : placeholder features (0 rows)

## Tables Dify (dans academie_db — héritage configuration)

Dify utilise la même base `academie_db` que l'app. Tables volumineuses :

| Table Dify | Rows | Size | Notes |
|---|---|---|---|
| `workflow_node_executions` | **29 922** | **82 MB** | ⚠️ Plus grosse table — accumule sans purge |
| `workflow_runs` | 1 982 | 55 MB | Idem, growing |
| `messages` | 1 731 | 2.8 MB | 97.8% du trafic = Teacher EN |
| `conversations` | 152 | 368 kB | |
| `workflow_conversation_variables` | — | 824 kB | Variables Dify conv |
| `workflows` | 14 | 568 kB | Chatflows (Teacher = l'un d'eux) |
| `apps` | 8 | 80 kB | 7 agents + 1 app test `cccccccc` à cleanup |
| `end_users` | 59 | 96 kB | Dify end-user mapping |
| `provider_models` | 5 | 64 kB | Les 5 modèles exposés via LiteLLM |

**Action à prévoir** : script de purge périodique sur `workflow_node_executions` et `workflow_runs` (rétention 30 jours ?).

## Tables n8n (dans academie_db — même pattern)

| Table n8n | Rows | Size |
|---|---|---|
| `execution_data` | 3 189 | 32 MB |
| `execution_entity` | 3 189 | 1 MB |
| `workflow_entity` | 7 | 304 kB |
| `workflow_history` | 8 | 408 kB |
| `webhook_entity` | 6 | 80 kB |

**7 workflows actifs** (détail dans [integrations.md](integrations.md)).

## Cible v2 — refonte taxonomie + multi-domaine + cross-agent

### Extensions `eleves`
Pas de changement majeur. `personnalite` reste JSONB extensible.

### Extension `profils_eleves`
- Le champ `domaine` reste la partition principale (permet multi-domaines par user : `sinse + domaine='anglais'` et `sinse + domaine='python'` = 2 rows)
- `scores_confiance` devient typé : `{concept_key: {p_mastery: 0-1, tier_history: [...], n_attempts: int, last_seen: ts}}`
- Nouveau champ optionnel : `theta_logit FLOAT` (cf. [error-gradation.md](../01-pedagogy/error-gradation.md) — IRT continu)
- Nouveau champ : `prerequisite_profile JSONB` — pour L1 (langues) ou prior knowledge (code/cybersec)

### Table : `l1_transfer_observations` ✅ créée Sprint 2 Phase A (2026-04-15), seedée Phase 6 (2026-04-16)
5 rows seed fr→en (articles ×1.5, prepositions ×1.4, false_friends ×1.3, modals ×1.2, word_order_questions ×1.1). `n_observations=0` pour toutes — multiplicateurs initialisés depuis `teacher_prompt.L1_TRANSFER_SEED`. Empirique recalibration prévue quand on aura ≥100 observations par paire (source, target, family). Schema :
```sql
source_profile       VARCHAR     -- ex: 'fr' (L1 francophone)
target_profile       VARCHAR     -- ex: 'en' (L2 anglais)
error_family         VARCHAR
n_observations       BIGINT
n_expected           BIGINT      -- baseline sans transfer
multiplier           FLOAT       -- observed/expected
last_updated         TIMESTAMP
PRIMARY KEY (source_profile, target_profile, error_family)
```

### Table : `domain_catalog` ✅ créée Sprint 2 Phase A (2026-04-15)
1 row seed : `lang:en` (domain_type=language, proficiency_scale=CEFR, active=true). Pour enregistrer les domaines instanciés et leur métadonnées :
```sql
domain_id      VARCHAR PRIMARY KEY   -- 'lang:en', 'lang:es', 'code:python', ...
domain_type    VARCHAR               -- 'language' | 'code' | 'cybersec' | 'accounting'
proficiency_scale VARCHAR            -- 'CEFR' | 'Bloom' | 'NICE' | 'custom'
active         BOOLEAN
metadata       JSONB
```

### Modification `snapshots_session`
- `schema_version` DEFAULT 2 pour futurs snapshots (cf. [ADR-007](../05-decisions/ADR-007-snapshot-versioning-cutoff.md))
- Nouvelle table `snapshots_session_v1_archive` pour historique pré-migration

### Modification `error_log`
- `tier` VARCHAR ('T0'..'T4') — déjà prévu
- `gravity_linguistic FLOAT`, `gravity_communicative FLOAT`, `gravity_social FLOAT` (dénormalisées pour perfs)
- `criterial_level_emergence VARCHAR` et `criterial_level_mastery VARCHAR` (cached depuis curriculum_concepts)

### Table : `spaced_retrieval_queue` ✅ créée Sprint 2 Phase A (2026-04-15), wiring Phase 7 MVP (2026-04-16)
Index partiel `idx_srq_eleve_schedule WHERE completed_at IS NULL`. Phase 7 MVP câble `chat_router._persist_spaced_retrieval` pour enqueue à J+1 sur silenced + complete sur addressed ; `outcome` utilisé = `'addressed'` (MVP — regression ladder J+3/J+7 post-MVP). Flag `SPACED_RETRIEVAL_ENABLED` env var (default OFF). Pour la revisite programmée d'erreurs (cf. [feedback-delivery.md](../01-pedagogy/feedback-delivery.md)) :
```sql
id               SERIAL
eleve_id         INT
domaine          VARCHAR
concept_key      VARCHAR
error_code       VARCHAR
scheduled_at     TIMESTAMP
completed_at     TIMESTAMP
outcome          VARCHAR   -- 'correct', 'still_wrong', 'skipped'
```

## Cross-agent progress (Dimension 4)

L'utilisateur `sinse` peut avoir :
- `(eleve_id=1, domaine='anglais')` avec niveau B1
- `(eleve_id=1, domaine='espagnol')` avec niveau A1
- `(eleve_id=1, domaine='python')` avec niveau 'intermédiaire'

Le dashboard unifié fait un `JOIN` sur `eleves.id → profils_eleves.eleve_id` pour afficher la progression par domaine côte-à-côte.

**Transfer learning inter-domaines** (futur hypothétique) : utiliser la `prerequisite_profile` pour informer un domaine des connaissances acquises dans un autre. Exemple : un user B2 anglais commence l'espagnol → multiplicateur de transfer appliqué (`en_to_es` multipliers). Pas implémenté en v2, à prévoir en v3+.

## Partitioning

**Décision court terme** : pas de partition physique des tables par domaine. Tables uniques avec colonne `domaine` = partition logique.

**À re-évaluer** :
- Si une table (`error_log` notamment) dépasse 10M rows → considérer partitionnement PG par `domaine` ou par range de `created_at`
- Si performances de query dégradent sur un domaine lourd → partition physique

## Versioning des snapshots (cf. ADR-007)

Option C retenue : **cut-off propre** à la migration v2.

Procédure :
1. Backup complet (vzdump + pg_dump)
2. Copier `snapshots_session` → `snapshots_session_v1_archive`
3. Purger ou ajouter `schema_version=2` DEFAULT
4. Déployer nouveau code
5. Nouveaux snapshots auto-incrémentés en v2

## Conventions

- **Nommage tables** : snake_case, pluriel quand applicable (`eleves`, `profils_eleves`, `error_log`)
- **Timestamps** : toujours `TIMESTAMPTZ` (timezone-aware)
- **JSONB** : pour les structures évolutives (profils, snapshots, personnalité), sinon colonnes typées
- **Soft-delete** : pas utilisé actuellement ; à introduire si besoin GDPR futur (colonne `deleted_at`)

## Références
- [overview.md](overview.md) — schéma général
- [ADR-002](../05-decisions/ADR-002-schema-from-day-1.md) — multi-domaine
- [ADR-007](../05-decisions/ADR-007-snapshot-versioning-cutoff.md) — versioning snapshots
- Code : `webapp/backend/app/database.py`, migrations SQL (à créer — aujourd'hui schéma évolue ad-hoc)
