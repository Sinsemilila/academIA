---
title: ADR-009 — Gravity axes comme colonnes dénormalisées sur error_log
status: accepted
last_reviewed: 2026-04-15
decision_date: 2026-04-15
authors: [claude, sinse]
---

# ADR-009 — Gravity axes comme colonnes dénormalisées sur error_log

## Contexte

La taxonomie v2 introduit la notion de **gravity axes** pour graduer l'impact
d'une erreur selon 3 dimensions indépendantes (cf.
[error-gradation.md](../01-pedagogy/error-gradation.md) et
[taxonomy-framework.md](../01-pedagogy/taxonomy-framework.md)) :

- **linguistic** : sévérité grammaticale pure (0.0 = tolérable, 1.0 = faute franche)
- **communicative** : impact sur la compréhension du message (0.0 = intelligible, 1.0 = rupture de sens)
- **social** : impact relationnel / registre / politesse (0.0 = OK, 1.0 = inapproprié dans le contexte)

Le tier (T0..T4) reste la clé principale du scoring ; les gravity axes
permettent une pondération secondaire et une UI plus informative (« cette
erreur est grammaticalement mineure mais communicativement bloquante »).

La question est : **où stocker ces 3 valeurs ?**

## Options envisagées

### Option A — Colonnes dénormalisées sur `error_log`

- Pour :
  - 1 seule table pour lire score + tier + gravity (pas de JOIN)
  - Perfs queries (COUNT, AVG, GROUP BY) sur les aggrégats directs
  - Indexable (ex: `WHERE gravity_communicative > 0.7` pour flagger les erreurs bloquantes)
  - Schema clair et explicite
- Contre :
  - 3 colonnes FLOAT supplémentaires (12 bytes/row × 9+ rows = négligeable)
  - Couplage structurel avec le tier : si demain on ajoute un 4ème axis, ALTER TABLE
  - Pas de versioning par axe

### Option B — Table séparée `error_gravity (error_log_id, axis, value)`

- Pour :
  - Extensibilité : ajouter des axes sans ALTER TABLE
  - Versioning par axe possible (ajouter `assessed_at`, `assessor`)
- Contre :
  - JOIN systématique sur toutes les queries de scoring
  - 3 rows par erreur (triplier la taille du stockage gravity)
  - Complexité UI pour afficher les 3 valeurs

### Option C — Single JSONB column `gravity_axes`

- Pour :
  - Extensibilité extrême (n'importe quelle structure)
  - Zero ALTER TABLE pour ajouter des axes
- Contre :
  - Pas de CHECK constraint numérique facile (FLOAT 0-1)
  - Index GIN plus coûteux que btree
  - Pas de columnar aggregation (analytics ralentis)
  - Sémantiquement flou (convention de clés non forcée)

## Décision

**Option retenue** : **A — Colonnes dénormalisées**.

**Justification** :

Le nombre d'axes (3) est fixe et justifié théoriquement (cf. Hartshorn 2013
pour multi-axis error gravity, James 1998 pour distinction linguistic /
communicative / social). On n'anticipe pas d'évolution dans le temps proche.

L'usage dominant sera des queries analytiques (AVG par axe × niveau,
distribution de gravity par famille). Option A bat B et C sur ces patterns.

Les 3 FLOAT nullable ne pèsent rien côté stockage (~24 bytes/row incluant
NULL bitmap) et n'imposent aucun défaut à la lecture.

Si un 4ème axe émerge (ex: `pragmatic` pour les erreurs d'implicature), on
traitera ça comme un ADR de refonte (migration schema), pas un cas d'usage
à anticiper spéculativement.

## Conséquences

**Positives** :
- Schema simple, explicite, queryable sans JOIN
- CHECK constraint possible sur chaque colonne (`0.0 <= gravity_X <= 1.0`)
- Perfs analytics optimales
- UI facile : 3 champs à afficher par erreur
- Pas de surcoût de maintenance par rapport à v1

**Négatives (acceptées)** :
- Ajout d'un axe = ALTER TABLE (coût 1 migration)
- Couplage avec tier : tier et gravity doivent être cohérents (pas enforced par DB)

**Neutres (à surveiller)** :
- Qualité des valeurs produites par le LLM (Phase B) : à valider par
  replay phase1b et spot-checks humains

## Actions de mise en œuvre

- [x] Migration DB `migrate_sprint2_schema.py` ajoute les 3 colonnes FLOAT nullable + CHECK constraints (Sprint 2 Phase A, 2026-04-15)
- [x] Phase B2 (2026-04-15, Session 17) : `enrich_error_fields()` populate gravity_axes via priors statiques `gravity_per_family` dans `tolerance_matrix_v2.yaml`. INSERT étendu à 15 colonnes (`error_analysis_router.py`). 9 rows backfillées via script idempotent.
- [ ] Sprint 6+ : rubric LLM pour produire gravity_axes contextuels (Approach C — touche au prompt fine-tuned, déféré). Pour l'instant priors SLA-based.
- [ ] Phase B3 ou Sprint 3 : UI `chat_router` expose les 3 axes pour l'affichage feedback
- [ ] Phase B3 ou Sprint 3 : scoring.py pondère le tier par gravity_communicative dans certains cas edge (à définir)

## Re-évaluation

- Si volume `error_log` > 1M rows et qu'une analytique par axe devient trop lente → considérer matérialiser des vues agrégées (pas changer le schema)
- Si un axe supplémentaire devient nécessaire (ex: `pragmatic` pour C1/C2) → ADR séparé
- Si le LLM produit de manière fiable les valeurs → supprimer les CHECK constraints nulls (forcer NOT NULL progressivement)

## Références

- `/opt/academie/scripts/migrate_sprint2_schema.py` — DDL appliquée
- [taxonomy-framework.md](../01-pedagogy/taxonomy-framework.md) § Gravity axes
- [error-gradation.md](../01-pedagogy/error-gradation.md) — méthodologie globale
- [data-model.md](../02-architecture/data-model.md) — schéma `error_log` extensions
- Hartshorn et al. 2013 — "Error gravity and EFL writing assessment" (concept multi-axis)
- James 1998 — *Errors in Language Learning and Use* (linguistic vs communicative distinction)
- ADR-003 — 5 tiers taxonomy (tier reste clé principale, gravity = secondaire)
