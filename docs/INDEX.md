# AcademIA — Documentation Index

> Point d'entrée unique. **À lire au début de chaque session** (`/pickup`).
> **À maintenir à jour à chaque changement structurel** (`/handoff`).

---

## 00 — Project

Vision, cap produit, glossaire.

- [vision.md](00-project/vision.md) — SaaS freemium/B2B, multi-domaines, positionnement complément-à-cours
- [roadmap.md](00-project/roadmap.md) — sprints en cours + jalons architecture
- [roadmap_multilang.md](00-project/roadmap_multilang.md) — chiffrage ES/IT/DE/JP + infra one-time
- [sprint5_multilang_audit.md](00-project/sprint5_multilang_audit.md) — audit 5 surfaces post-Sprint 5 infra, analyse fine-tune v3, stratégie CEFR, plan P0→P4
- [sprint5_execution_plan.md](00-project/sprint5_execution_plan.md) — plan d'exécution long-term (D1-D6 validés), 4 phases, checkpoints, rollback, suivi
- [multilang_research_plan.md](00-project/multilang_research_plan.md) — plan de recherche ES/IT/DE/JP/RU avec équivalents par étape pipeline Teacher EN + effort par langue + priorités roadmap
- [multilang_execution_roadmap.md](00-project/multilang_execution_roadmap.md) — roadmap chronologique d'exécution (séquentiel vs parallèle vs hybride), 4 vagues + Phase 0 infra, décisions strat, critical path
- [multilang_maturity_research.md](00-project/multilang_maturity_research.md) — **Session 28** recherche 6 agents maturité IT/DE/JP/RU : IT+DE atteignables EN/ES, JP plafond B1-B2, RU viable B1 via synthetic+transfer ou full €33-59K
- [glossary.md](00-project/glossary.md) — CECRL, tier, snapshot, domain, L1→L2, IRT, GRM, FSRS, etc. (60+ termes)

## 01 — Pedagogy

Fondations pédagogiques indépendantes du code. **Socle scientifique du produit.**

- [taxonomy-framework.md](01-pedagogy/taxonomy-framework.md) — framework abstrait domain-agnostic (5 tiers, gravity axes, interface Domain)
- [cefr-language-instance.md](01-pedagogy/cefr-language-instance.md) — instanciation langues (12 familles, 6 bandes, L1 transfer)
- [error-gradation.md](01-pedagogy/error-gradation.md) — calibration empirique (GLMM, Cox PH, GRM), 5 étapes méthodologie
- [sprint1_report.md](01-pedagogy/sprint1_report.md) — **résultats Sprint 1** : tier map empirique sur W&I (2671 learners) + matrice v2_draft
- [matrix_v2_review.md](01-pedagogy/matrix_v2_review.md) — **Sprint 2A** : review adversariale 21 cellules changées (19 ACCEPT / 1 FLAG / 1 OVERRIDE)
- [feedback-delivery.md](01-pedagogy/feedback-delivery.md) — Lyster prompts > recasts, dosage par niveau, timing, anti-drift
- [bibliography.md](01-pedagogy/bibliography.md) — ~80 sources (Corder, Selinker, Krashen, Hattie, Sweller, Samejima, Bryant, Yancey, Pak, …)

## 02 — Architecture

Comment le système est construit (état actuel + cible).

- [overview.md](02-architecture/overview.md) — diagramme macro stack
- [data-model.md](02-architecture/data-model.md) — tables actuelles + extensions v2 (l1_transfer_observations, domain_catalog, spaced_retrieval_queue)
- [agent-topology.md](02-architecture/agent-topology.md) — architecture hybride orchestrée (ADR-004)
- [shared-core.md](02-architecture/shared-core.md) — package `academie-core` détaillé (interface Domain, organisation, tests)

## 03 — Domain

Spécificités par domaine instancié.

- [languages/en.md](03-domain/languages/en.md) — Teacher EN actuel + cible v2
- `languages/es.md` — Maestro Spanish (futur, après Sprint 5)
- `languages/jp.md` — Sensei Japanese (futur)
- `languages/de.md` — Lehrer German (futur)
- `languages/it.md` — Professore Italian (futur)
- `code/python.md` — PyMentor (futur, domaine non-linguistique)
- `cybersec.md` — CyberMentor (futur, NICE framework)

## 04 — Infra

Opérationnel : déploiement, backup, monitoring, credentials.

- [deployment.md](04-infra/deployment.md) — Docker stack (13 containers), nginx host, Cloudflare Tunnel, PG, Redis, LiteLLM
- [backup.md](04-infra/backup.md) — stratégie 4 niveaux (avec gaps réels identifiés)
- [monitoring.md](04-infra/monitoring.md) — état actuel (smoke-test + widget admin) + cible (Grafana, Prometheus, KPIs)
- [credentials.md](04-infra/credentials.md) — état dette + cible SOPS/Vault
- [filesystem-scan.md](04-infra/filesystem-scan.md) — ⚠️ snapshot ponctuel 2026-04-15 (à utiliser comme référence, pas comme vérité temps-réel)

## 05 — Decisions (ADRs)

**Le journal des décisions architecturales.** Chaque changement structurel = un ADR. Immutables (on ne modifie pas, on `Supersede` un ADR).

- [ADR-template.md](05-decisions/ADR-template.md) — template à copier
- [ADR-001-monolith-vs-microservices.md](05-decisions/ADR-001-monolith-vs-microservices.md) — monolithe maintenu, microservices envisagés [accepted]
- [ADR-002-schema-from-day-1.md](05-decisions/ADR-002-schema-from-day-1.md) — schéma multi-lang + multi-domaine dès le départ [accepted]
- [ADR-003-5-tiers-taxonomy.md](05-decisions/ADR-003-5-tiers-taxonomy.md) — T0 pre_acquisition + T1-T4 visibles [accepted]
- [ADR-004-hybrid-orchestrated-agent-topology.md](05-decisions/ADR-004-hybrid-orchestrated-agent-topology.md) — architecture hybride orchestrée [**accepted** — ré-analyse Sprint 4 complétée 2026-04-16, impl ~8-11 jours]
- [ADR-005-academie-core-shared-library.md](05-decisions/ADR-005-academie-core-shared-library.md) — package Python partagé [accepted]
- [ADR-006-litellm-byok-familial.md](05-decisions/ADR-006-litellm-byok-familial.md) — pool de clés familial via LiteLLM [accepted]
- [ADR-007-snapshot-versioning-cutoff.md](05-decisions/ADR-007-snapshot-versioning-cutoff.md) — option C cut-off à la migration taxonomie v2 [accepted]
- [ADR-008-errant-mapping-later.md](05-decisions/ADR-008-errant-mapping-later.md) — table de traduction ERRANT en Sprint 5+ [accepted]
- [ADR-009-gravity-axes-schema.md](05-decisions/ADR-009-gravity-axes-schema.md) — gravity axes comme colonnes dénormalisées sur error_log [accepted]
- [ADR-011-native-level-systems-jlpt-torfl.md](05-decisions/ADR-011-native-level-systems-jlpt-torfl.md) — JP utilise JLPT N5-N1, RU utilise TORFL TEU-IV, mapping transparent vers storage interne CEFR unifié [accepted]
- [ADR-012-security-remediation-2026-04-19.md](05-decisions/ADR-012-security-remediation-2026-04-19.md) — rotation 7 secrets leakés + git filter-repo rewrite historique public [accepted]

## 99 — Runbooks

Procédures opérationnelles concrètes.

- [gotchas.md](99-runbooks/gotchas.md) — pièges connus et workarounds (Dify, LiteLLM, PG, n8n, webapp, secrets)
- [add-new-agent.md](99-runbooks/add-new-agent.md) — ajouter un nouvel agent/domaine (langue ou non-linguistique)
- [rotate-litellm-keys.md](99-runbooks/rotate-litellm-keys.md) — rotation de clés API LLM
- [restore-backup.md](99-runbooks/restore-backup.md) — restauration par niveau de backup
- [migrate-taxonomy-v2.md](99-runbooks/migrate-taxonomy-v2.md) — migration Sprint 2 Phase A (forward + rollback 3 niveaux)
- [rotate-secrets-sops.md](99-runbooks/rotate-secrets-sops.md) — édition/rotation/DR des secrets SOPS (age), setup Session 18

## Legacy (à retraiter)

Les anciens docs sont sous [`_legacy/`](_legacy/) — status `needs-review`. À supprimer après validation de la migration (voir `_legacy/README.md`).

---

## Conventions

### Header de chaque fichier

```
---
title: <Titre>
status: authoritative | draft | needs-review | stale | superseded
last_reviewed: YYYY-MM-DD
owner: claude | sinse
supersedes: (optionnel, pour ADRs)
---
```

### Statuts

- **`authoritative`** : fait foi, à respecter
- **`accepted-in-principle`** : décision prise mais ré-analyse avant implémentation (ADR spécifique)
- **`draft`** : en cours, ne pas se baser dessus
- **`needs-review`** : probablement obsolète, à valider avant usage
- **`stale`** : confirmé obsolète, à retraiter ou supprimer
- **`superseded`** : remplacé par un autre doc (ADRs)

### Workflow obligatoire

1. **Avant d'implémenter quelque chose de structurel** : lire INDEX.md + les docs pertinentes + ADRs concernés
2. **Si décision architecturale** : créer un nouvel ADR (copier template, numéroter, remplir)
3. **Après implémentation** : mettre à jour les docs impactées (même commit), bumper `last_reviewed`

### Maintenance automatique

- `/pickup` ouvre INDEX.md (forcé)
- `/handoff` check que les docs impactées par les changements de code ont été mises à jour

---

*Documentation structurée mise en place : 2026-04-15 (Session 13)*
*Scan exhaustif infrastructure : 2026-04-15 (4 agents parallèles — Docker, filesystem, DB, app surface)*
*Dernière révision INDEX : 2026-04-15*
