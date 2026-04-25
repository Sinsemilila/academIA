---
title: ADR-007 — Versioning snapshots : migration cut-off propre (option C)
status: accepted
last_reviewed: 2026-04-15
decision_date: 2026-04-15
authors: [sinse, claude]
---

# ADR-007 — Versioning snapshots : migration cut-off propre (option C)

## Contexte

La refonte de la taxonomie v2 (5 tiers, gravity axes, L1 transfer, schema multi-langue + multi-domaine, cf. ADR-002, ADR-003) va modifier la structure des snapshots existants dans `snapshots_session` (PostgreSQL JSONB).

Que faire des snapshots pré-v2 ?

## Options envisagées

### Option A — Script de migration SQL v1 → v2

- Pour : historique intégralement préservé, conversion automatique
- Contre : complexité élevée (formats mixtes, cas edge), risque de perte/corruption, effort dev

### Option B — Cohabitation de versions avec champ `schema_version`

- Pour : rétrocompatibilité totale
- Contre : complexité code (lire v1 ET v2), dette permanente

### Option C — Cut-off propre : archiver v1, générer v2 à partir de maintenant

- Pour : simple, propre, code futur ne gère qu'un format
- Contre : perte partielle d'historique granulaire (seules les données agrégées restent consultables)

## Décision

**Option C — Cut-off propre**.

**Justification** :
- Échelle actuelle : ~20 users familiaux, majorité avec peu d'historique significatif (< 30 jours)
- Complexité de l'option A (migration automatique) disproportionnée par rapport à la valeur d'un historique limité
- Option B ajoute une dette code permanente pour un bénéfice limité
- Les **données agrégées de progression** (scores_confiance, niveau_global, points_forts/lacunes) restent dans `profils_eleves` indépendamment du format snapshot → continuité utilisateur préservée

## Procédure de cut-off

1. **Backup complet** : snapshot vzdump de la VM cosmos + dump PostgreSQL dédié pré-migration
2. **Archiver** les snapshots v1 dans une table `snapshots_session_v1_archive` (même structure, simple `INSERT INTO ... SELECT ...`)
3. **Vider** `snapshots_session` ou ajouter une colonne `schema_version` avec DEFAULT 2 pour futurs inserts
4. **Les nouveaux snapshots v2** sont générés par le nouveau code taxonomy
5. **Communication aux users** : note dans le changelog "historique détaillé remis à zéro, données agrégées préservées"

## Conséquences

- Positives : simplicité code, déploiement net, pas de dette
- Acceptées : perte de granularité historique pour ~20 users, principalement anecdotique (famille + amis proches)
- Neutres : archive SQL consultable en cas de besoin forensique

## Actions de mise en œuvre

**Avant migration** :
- [ ] Backup vzdump complet cosmos
- [ ] Dump `pg_dump academie_db` avec flag --clean
- [ ] Vérifier restauration fonctionnelle du backup (test dans un PG secondaire)

**Jour de migration** :
- [ ] Créer `snapshots_session_v1_archive`
- [ ] `INSERT INTO snapshots_session_v1_archive SELECT * FROM snapshots_session;`
- [ ] Vérifier count = count
- [ ] TRUNCATE `snapshots_session` OU ajouter column `schema_version` DEFAULT 2
- [ ] Déployer le nouveau code taxonomy v2
- [ ] Vérifier premier snapshot v2 généré

## Re-évaluation

À l'ouverture SaaS publique (> 100 users réels), prévoir une stratégie migration plus fine (Option A) plutôt que cut-off propre.

## Références

- [ADR-002-schema-from-day-1.md](ADR-002-schema-from-day-1.md)
- [ADR-003-5-tiers-taxonomy.md](ADR-003-5-tiers-taxonomy.md)
- [99-runbooks/restore-backup.md](../99-runbooks/restore-backup.md) (à écrire)
