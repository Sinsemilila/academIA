---
title: Roadmap AcademIA
status: authoritative
last_reviewed: 2026-04-15
---

# Roadmap AcademIA

> Sprints concrets du chantier taxonomie v2 + jalons architecture. Mis à jour à chaque fin de sprint.

## Vision long terme

Cf. [vision.md](vision.md). TL;DR : SaaS freemium/B2B multi-domaines, positionné comme complément à un cours, gratuit côté familial tant que possible.

---

## Chantier en cours : **Taxonomie v2** (avril-juin 2026)

### Sprint 1 — Calibration empirique (✅ Path A livré Session 15, 2026-04-15)

**Status** : Path A exécuté — calibration sur corpus externes (W&I + LOCNESS BEA 2019) faute de volume AcademIA interne suffisant (`error_log` = 9 rows, pipeline neuve). Voir [`sprint1_report.md`](../01-pedagogy/sprint1_report.md).

**Livrables livrés** :
- ✅ Scripts `/opt/academie/scripts/sprint1/` (venv, mapping ERRANT, normalize, EDA, generate draft)
- ✅ `errant_to_academie.yaml` — 18 tags → 9 familles AcademIA (84.7% coverage instances W&I)
- ✅ Parquet : 2 671 learners × 70 489 error annotations sur CEFR A1-C2 + N
- ✅ Tier map empirique `tier_assignments_external.parquet` + figures
- ✅ **`tolerance_matrix_v2_draft.yaml`** (44% des cellules changent vs v1) — à valider par Sinse avant Sprint 2
- ⚠️ GLMM (NumPyro) : **reporté à Sprint 1.5** (raffinement numérique β_tier)
- ⚠️ Cox PH : **skippé** (pas de data longitudinale sans EFCAMDAT)

**Insight majeur** : les "bar-raising" de v1 ne sont pas empiriquement fondés. Beaucoup de familles (noun_det, verb_tense, surface, preposition) restent T1_ignored à tous les niveaux — pénaliser à C1/C2 = pénaliser la normalité.

### Sprint 1.5 — Raffinement GLMM (✅ livré Session 15, 2026-04-15)

**Status** : livré. NumPyro hierarchical logistic GLMM fitté sur W&I — β_tier posterior monotone T1 → T4, R-hat 1.01, ESS_min 329. Voir [`sprint1_report.md` § 9](../01-pedagogy/sprint1_report.md#9-sprint-15-results--glmm-posterior-2026-04-15).

**Livrables livrés** :
- ✅ `04b_glmm_data_prep.py` + `05_glmm_fit.py` + `06_posterior_to_weights.py`
- ✅ `glmm_posterior.nc` + `glmm_summary.json` + `weights_from_posterior.json`
- ✅ `tolerance_matrix_v2_draft.yaml` mis à jour avec `weights:` calibrés :
  - `ignored`=0.00, `noted`=0.196, `penalized`=0.394, `regressive`=0.538
  - CI 95% et diagnostics GLMM inclus
- ⚠️ EFCAMDAT + Cox PH : pas tentés dans ce sprint (optionnel, reporté à Sprint 1.6)

**Insight majeur** : v1 sur-pénalisait T3 (0.80 vs empirique 0.39). Le gradient réel est plus plat que la matrice actuelle. Implication Sprint 2 : les valeurs GLMM devraient être activées (ou A/B testées).

### Sprint 1.6 — EFCAMDAT + Cox PH (optionnel, backlog)

**Objectif** : si registration EFCAMDAT obtenue, calibrer half-life par famille × niveau.

**Livrables** :
- Cox PH via `lifelines` sur data longitudinale
- Dashboard admin : half-life par famille × niveau
- Extension GLMM avec β_level interaction

**Dépendances** : registration EFCAMDAT (≥ 1 semaine typiquement).

### Sprint 2 Phase A — Schema DB + docs + tests (✅ livré Session 15, 2026-04-15)

**Status** : livré. Schéma DB prêt à recevoir les nouveaux champs, migrations appliquées et idempotentes, tests régression verts. Activation scoring v2 = Phase B.

**Livrables livrés** :
- ✅ `tolerance_matrix_v2.yaml` avec structure v1-compatible + weights GLMM + matrix calibrée (Sprint 1/1.5)
- ✅ Extension `error_log` : 6 nouvelles colonnes (`tier`, `gravity_linguistic/communicative/social`, `criterial_level_emergence/mastery`) + CHECK contraints + index sur `tier`
- ✅ Tables `l1_transfer_observations`, `domain_catalog` (seed `lang:en`), `spaced_retrieval_queue` créées
- ✅ Snapshot cut-off ADR-007 option C : 8 snapshots archivés dans `snapshots_session_v1_archive`, `schema_version` ajouté (existants=1, nouveaux=2)
- ✅ Script `/opt/academie/scripts/migrate_sprint2_schema.py` idempotent
- ✅ Runbook [`99-runbooks/migrate-taxonomy-v2.md`](../99-runbooks/migrate-taxonomy-v2.md) avec procédure forward + 3 rollback layers
- ✅ ADR-009 [`gravity-axes-schema.md`](../05-decisions/ADR-009-gravity-axes-schema.md)
- ✅ Review matrix v2 adversariale [`matrix_v2_review.md`](../01-pedagogy/matrix_v2_review.md) : 19 ACCEPT / 1 FLAG / 1 OVERRIDE (sentence × beginner)
- ✅ Override déclaré dans `tolerance_matrix_v2_overrides.yaml` (à appliquer Phase B)
- ✅ Tests régression `/opt/academie/scripts/sprint2/tests/` : 14 tests, tous PASS

**Impact prod** : nul. Les 6 nouvelles colonnes sont nullable, restent NULL jusqu'à Phase B.

### Sprint 2 Phase B — Intégration scoring v2 (✅ livré Sessions 17-18)

**Status** : livré. Scoring lit `error_log.tier` quand `USE_V2_SCORING=true`, override loader actif, 38/38 tests régression + property-based.

**Livrables livrés** :
- ✅ B1 (Session 17) : override loader `tolerance_matrix_v2_overrides.yaml` dans `scoring.py` + `chat_router.py` ; override `sentence × beginner = noted` actif en prod
- ✅ B2 (Session 17) : sections `gravity_per_family` + `criterial_per_family` dans yaml v2, helper `enrich_error_fields()`, INSERT router étendu 15 cols, backfill 9 rows, flag `USE_V2_SCORING` skeleton
- ✅ B3 (Session 18) : `compute_error_profile` lit `row["tier"]` via majority vote + fallback matrix, flag `USE_V2_SCORING=true` actif en prod, retrospective 25 rows v1=2.60 → v2=0.788 (−70%, confirme empiriquement la sur-pénalisation T3 v1)
- ✅ B+ (Session 18) : 10 property-based tests pytest-hypothesis (round-trip, monotonicity, band norm, permutation stability, family isolation, majority vote, enrich determinism, progress bounds)

**Livrables reportés (Sprint 6+ Approach C)** :
- ⚠️ Refactor prompt `llm.py` pour sortir `tier`/`gravity`/`criterial` en JSON — reporté car refactor fine-tuned prompt risqué, enrichment déterministique Approach B suffit tant que priors SLA stables
- ⚠️ Re-run phase1b battery complet — à faire si bascule Approach C décidée

### Sprint 3 — Refonte prompt Teacher + anti-drift (1 semaine)

**Objectif** : implémenter la pédagogie Lyster (prompts > recasts), dosage par niveau, anti-drift Pak 2025.

**Livrables** :
- Nouveau prompt Teacher système avec rubric CECRL + 3-5 few-shot par niveau + JSON schema strict + CoT dans `<reasoning>` block
- Mapping tier → type de feedback (recast/elicitation/metalinguistic/prompt)
- Dosage par niveau (max corrections/tour selon A1..C2)
- Re-injection rubric + level toutes les 5 interactions (anti-drift)
- Tests E2E sur 4 profils user différents

**Dépendances** : Sprint 2 (pour avoir les tiers calibrés).

**Effort** : 3-5 jours (surtout prompt engineering + tests).

**Docs à créer/update** : [`01-pedagogy/feedback-delivery.md`](../01-pedagogy/feedback-delivery.md) (done), [`03-domain/languages/en.md`](../03-domain/languages/en.md).

### Sprint 4 — Analyse risques agent topology (2-3 jours)

**Objectif** : avant d'implémenter l'architecture hybride orchestrée ([ADR-004](../05-decisions/ADR-004-hybrid-orchestrated-agent-topology.md)), réévaluer les risques à la lumière de l'expérience Sprints 1-3.

**Livrables** :
- Document de risques mis à jour dans ADR-004
- Estimation chiffrée coût migration Teacher EN → `LanguageDomain + language-tutor` paramétré
- Plan de rollback détaillé
- GO / NO-GO décision (Sinse) pour Sprint 5

**Dépendances** : Sprints 1-3 complétés.

### Sprint 5 — Implémentation agent-topology (2-3 semaines) — **SOUS RÉSERVE**

**Objectif** : bascule `LanguageDomain` + chatflow `language-tutor` paramétré.

**Livrables** (si GO à Sprint 4) :
- Package `academie-core` v1.0 scaffoldé et testé
- Nouveau chatflow Dify `language-tutor` minimaliste
- `LanguageDomain(lang="en")` instantié dans webapp
- `/api/chat/send` route vers `LanguageDomain` au lieu de call Dify direct
- Bascule progressive avec fallback vers Teacher EN actuel

**Dépendances** : Sprint 4 + validation Sinse.

**Effort** : 10-15 jours.

**Docs à créer/update** : [`02-architecture/agent-topology.md`](../02-architecture/agent-topology.md) (done), [`02-architecture/shared-core.md`](../02-architecture/shared-core.md) (done), runbook migration.

### Sprint 6 — Graded Response Model + self-consistency (2 semaines)

**Objectif** : remplacer les tiers discrets par un modèle psychométrique polytomique.

**Livrables** :
- `academie-core/psychometrics/irt.py` avec `girth` wrapper GRM
- Priors bayésiens depuis matrice v2, calibration MLE
- Nouveau champ `theta_logit` dans `profils_eleves`
- Self-consistency n=3 confidence-gated dans `error_analysis_router.py` (pas Teacher chat real-time)

**Dépendances** : Sprint 5.

**Effort** : 10-15 jours.

**Data minimum** : ~25-30k interactions (à surveiller).

### Sprint 7 — CAT diagnostic + URIEL L1 priors (2-3 semaines)

**Objectif** : diagnostic onboarding adaptatif + priors typologiques pour futures langues.

**Livrables** :
- CAT sur diagnostic (5-7 questions devient adaptatif via Fisher info)
- lang2vec/URIEL intégré pour priors L1-L2 transfer
- Préparation data pour Maestro (ES)

**Effort** : 10 jours.

---

## Jalons architecture parallèles

Ces jalons ne bloquent pas le chantier taxonomie mais sont importants pour la vision long terme.

### J-1 — Credentials management (fondation livrée Session 18, 🟡 partiel)
Fondation SOPS+age livrée Session 18 : `webapp/.env.sops` chiffré dotenv per-var, workflow `decrypt-secrets.sh` + runbook rotation/DR. **Reste** : migrer `/opt/litellm/config.yaml` (OpenAI key + DB password) — session dédiée en bas usage requise car downtime LiteLLM = chat cassé. Optionnel : basculer les 9 fichiers `/opt/academie-shared/secrets/*` vers SOPS.

### J-2 — Monitoring complet
Priorité moyenne. Aujourd'hui `smoke-test` + widget admin. Ajouter Prometheus/Grafana quand la complexité le justifie (probablement après Sprint 5-6).

### J-3 — Staging environment
Priorité basse tant que < 30 users. À mettre en place avant tout changement de prompt/taxonomie impactant en prod avec vrais users payants.

### J-4 — Authentication sérieuse
Priorité haute pour SaaS public. OIDC / magic links / 2FA. Préparer architecture mais pas implémenter tant que familial.

### J-5 — Extension multi-domaine Maestro (ES)
Priorité basse tant que Teacher v2 pas stabilisé. Première instance réelle du multi-langue, validera l'architecture.

### J-6 — PyMentor (Python)
Priorité basse. Premier domaine non-linguistique, validera le framework abstrait vraiment.

---

## Rythme et cadence

- **Handoff systématique** (fin de session) avec mise à jour SESSION.md, CHANGELOG, TODO, docs impactées
- **ADR obligatoire** pour toute décision architecturale (nouveau ADR numéroté)
- **Re-évaluation** de la roadmap en fin de Sprint 3 (puis Sprint 5, puis Sprint 7) avec Sinse
- Pas de date ferme — le projet reste familial / sans pression de delivery

## Ce qui n'est PAS dans la roadmap (explicitement)

- ❌ Deep Knowledge Tracing (AKT/SAINT) — skippé, > 500k interactions nécessaires
- ❌ RL adaptive curriculum — overkill à l'échelle actuelle
- ❌ App mobile native — PWA suffit
- ❌ Self-hosting LLM GPU — pas de budget/hardware
- ❌ Communauté / social / peer — pas prioritaire

---

## Historique (sessions précédentes)

Les sessions réalisées sont tracées dans [`../../SESSION.md`](../../SESSION.md) (cumulatif depuis session 1).

Sessions 1-12 = infrastructure + backfill + fixes + taxonomie préliminaire. Session 13 (2026-04-15) = mise en place docs + analyse pré-refonte taxonomie v2.
