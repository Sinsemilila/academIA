# AcademIA — Documentation Index

> Point d'entrée unique. **À lire au début de chaque session** (`/pickup` ou `/project academia`).
> **À maintenir à jour à chaque changement structurel** (`/handoff`).

---

## 00 — Project

Vision, cap produit, glossaire, sprints actifs.

**Active** :
- [vision.md](00-project/vision.md) — SaaS freemium/B2B, multi-domaines, positionnement complément-à-cours [authoritative]
- [roadmap.md](00-project/roadmap.md) — sprints en cours + jalons architecture [authoritative]
- [glossary.md](00-project/glossary.md) — CECRL, tier, snapshot, domain, L1→L2, IRT, GRM, FSRS, etc. (60+ termes) [authoritative]
- [sprint-maestro-es-2026-05.md](00-project/sprint-maestro-es-2026-05.md) — sprint Maestro ES MVP-acceptable (Build avant Measure pivot S55) [active]
- [sprint-maitre-comptable-2026-05.md](00-project/sprint-maitre-comptable-2026-05.md) — **Sprint Maître Comptable Mode B livré S57 + roadmap P0-P5** ⭐ [active]

**Archived/superseded** (gardés pour traçabilité, NE PAS appliquer) :
- `roadmap_multilang.md` [superseded] — remplacé par execution roadmap multi-vagues post ADR-013
- `multilang-action-plan-2026-04-20.md` [superseded]
- `multilang_research_plan.md` [superseded]
- `multilang_execution_roadmap.md` [superseded]
- `multilang_maturity_research.md` [superseded] — remplacé par ADR-013 (scope tier EN+ES flagship A1-C2 vs IT+DE+JP+RU essential A1-B2)
- `sprint5_multilang_audit.md` + `sprint5_execution_plan.md` [superseded]
- `sprint4_preimpl_review.md` [superseded]
- `discovery_emails/` + `onboarding-research-2026-04-20/` (sous-dossiers research, ponctuels)

## 01 — Pedagogy

Fondations pédagogiques indépendantes du code. **Socle scientifique du produit.**

**Foundations** :
- [taxonomy-framework.md](01-pedagogy/taxonomy-framework.md) — framework abstrait domain-agnostic (5 tiers, gravity axes, interface Domain) [authoritative]
- [cefr-language-instance.md](01-pedagogy/cefr-language-instance.md) — instanciation langues (12 familles, 6 bandes, L1 transfer) [authoritative]
- [cefr-consolidation-policy.md](01-pedagogy/cefr-consolidation-policy.md) — politique consolidation CEFR cross-langues [needs-review : add status frontmatter]
- [error-gradation.md](01-pedagogy/error-gradation.md) — calibration empirique (GLMM, Cox PH, GRM), 5 étapes méthodologie [authoritative]
- [feedback-delivery.md](01-pedagogy/feedback-delivery.md) — Lyster prompts > recasts, dosage par niveau, timing, anti-drift [authoritative]
- [bibliography.md](01-pedagogy/bibliography.md) — ~80 sources (Corder, Selinker, Krashen, Hattie, Sweller, Samejima, Bryant, Yancey, Pak, …) [authoritative]
- [l1-l2-scaffolding-policy.md](01-pedagogy/l1-l2-scaffolding-policy.md) — politique scaffolding L1→L2 cross-langues [needs-review : add status frontmatter]

**Sprint reports** (immutable, archives empiriques) :
- [sprint1_report.md](01-pedagogy/sprint1_report.md) — tier map empirique sur W&I (2671 learners) + matrice v2_draft [authoritative]
- [matrix_v2_review.md](01-pedagogy/matrix_v2_review.md) — Sprint 2A : review adversariale 21 cellules (19 ACCEPT / 1 FLAG / 1 OVERRIDE) [authoritative]
- [sprint3_design.md](01-pedagogy/sprint3_design.md) + [sprint3_baseline_prompt.md](01-pedagogy/sprint3_baseline_prompt.md) + [sprint3_fewshots.md](01-pedagogy/sprint3_fewshots.md) [authoritative]
- [v1_vs_v2_personas_report.md](01-pedagogy/v1_vs_v2_personas_report.md) [authoritative]
- [sprint-oracle-en-coherence-2026-05.md](01-pedagogy/sprint-oracle-en-coherence-2026-05.md) — Sprint Oracle EN, Phase 0-6 LIVRÉE S53-S54 [authoritative]

**Oracle V1 design + investigations** :
- [corpus-oracle-v1-design.md](01-pedagogy/corpus-oracle-v1-design.md) [shipped-v1-alpha-2026-04-23]
- `oracle-v1-fault-injection-findings-2026-04-23.md` [needs-review : add status]
- `oracle-v1-goldens-onboarding-flow-issue-2026-04-23.md` [needs-review : add status]
- `phase-c-regression-oracle-report-2026-04-22.md` [needs-review : add status]
- [cf-taxonomy-gap-2026-04-29.md](01-pedagogy/cf-taxonomy-gap-2026-04-29.md) [draft]

## 02 — Architecture

Comment le système est construit (état actuel + cible).

- [overview.md](02-architecture/overview.md) — diagramme macro stack [authoritative]
- [data-model.md](02-architecture/data-model.md) — tables actuelles + extensions v2 (l1_transfer_observations, domain_catalog, spaced_retrieval_queue) [authoritative]
- [agent-topology.md](02-architecture/agent-topology.md) — architecture hybride orchestrée (ADR-004) [accepted]
- [shared-core.md](02-architecture/shared-core.md) — package `academie-core` détaillé [authoritative]
- [api-surface.md](02-architecture/api-surface.md) — surface REST + payloads [authoritative]
- [integrations.md](02-architecture/integrations.md) — Dify, LiteLLM, n8n, Cloudflare, intégrations externes [authoritative]

## 03 — Domain

Spécificités par domaine instancié.

- [comptabilite.md](03-domain/comptabilite.md) — **AccountingDomain (FR) — Studi RNCP41653 tuteur dual-mode** [active S57, ADR-017 accepted, table consolidée knowledge base 45 sources] ⭐ premier domaine non-linguistique
- [languages/en.md](03-domain/languages/en.md) — Teacher EN reference architecture, MVP shipped [authoritative]
- `languages/es.md` — Maestro ES, **MVP-acceptable shipped S56** (battery 23/31 = 74.2%, κ Opus 0.93/0.81/0.93). **Doc à créer** : SoT [reference architecture S55 + execution roadmap S55 dans `webapp/backend/docs/`]
- `languages/it.md` — Wave 2 IT, AUTHORIZED S56, kickoff pending
- `languages/de.md` — Wave 2 DE, AUTHORIZED S56, kickoff pending
- `languages/jp.md` — Wave 3 JP (ADR-015 productive eval), pending Wave 2 closure
- `languages/ru.md` — Wave 4 RU, pending
- `code/python.md` — PyMentor (futur, domaine non-linguistique)
- `cybersec.md` — CyberMentor (futur, NICE framework)

## 04 — Infra

Opérationnel : déploiement, backup, monitoring, credentials.

- [deployment.md](04-infra/deployment.md) — Docker stack (13 containers), nginx host, Cloudflare Tunnel, PG, Redis, LiteLLM [authoritative]
- [backup.md](04-infra/backup.md) — stratégie 4 niveaux (gaps réels identifiés) [authoritative]
- [monitoring.md](04-infra/monitoring.md) — état actuel (smoke-test + widget admin) + cible Grafana/Prometheus [draft]
- [credentials.md](04-infra/credentials.md) — état dette + cible SOPS/Vault [authoritative]
- [filesystem-scan.md](04-infra/filesystem-scan.md) — snapshot ponctuel 2026-04-15 (référence non-temps-réel) [snapshot]

## 05 — Decisions (ADRs)

**Le journal des décisions architecturales.** Chaque changement structurel = un ADR. Immutables (on ne modifie pas, on `Supersede` un ADR).

- [ADR-template.md](05-decisions/ADR-template.md) — template à copier
- [ADR-001-monolith-vs-microservices.md](05-decisions/ADR-001-monolith-vs-microservices.md) [accepted]
- [ADR-001-refactor-complete-2026-H2.md](05-decisions/ADR-001-refactor-complete-2026-H2.md) — refactor complet H2 2026 [check : numérotation duplicate à clarifier]
- [ADR-002-schema-from-day-1.md](05-decisions/ADR-002-schema-from-day-1.md) [accepted]
- [ADR-003-5-tiers-taxonomy.md](05-decisions/ADR-003-5-tiers-taxonomy.md) [accepted]
- [ADR-004-hybrid-orchestrated-agent-topology.md](05-decisions/ADR-004-hybrid-orchestrated-agent-topology.md) [accepted, ré-analyse Sprint 4 complétée 2026-04-16]
- [ADR-005-academie-core-shared-library.md](05-decisions/ADR-005-academie-core-shared-library.md) [accepted]
- [ADR-006-litellm-byok-familial.md](05-decisions/ADR-006-litellm-byok-familial.md) [accepted]
- [ADR-007-snapshot-versioning-cutoff.md](05-decisions/ADR-007-snapshot-versioning-cutoff.md) [accepted]
- [ADR-008-errant-mapping-later.md](05-decisions/ADR-008-errant-mapping-later.md) [accepted]
- [ADR-009-gravity-axes-schema.md](05-decisions/ADR-009-gravity-axes-schema.md) [accepted]
- [ADR-010-cosmos-L4-docker-socket-proxy.md](05-decisions/ADR-010-cosmos-L4-docker-socket-proxy.md) [accepted]
- [ADR-011-native-level-systems-jlpt-torfl.md](05-decisions/ADR-011-native-level-systems-jlpt-torfl.md) [accepted]
- [ADR-012-security-remediation-2026-04-19.md](05-decisions/ADR-012-security-remediation-2026-04-19.md) [accepted]
- [ADR-013-language-scope-by-tier.md](05-decisions/ADR-013-language-scope-by-tier.md) — EN+ES flagship A1-C2 vs IT/DE/JP/RU essential A1-B2 [accepted, S51]
- [ADR-014-structured-knowledge-extraction.md](05-decisions/ADR-014-structured-knowledge-extraction.md) — Layer 1.5 authority anchor extraction [accepted, S52]
- [ADR-015-jp-productive-evaluation-strategy.md](05-decisions/ADR-015-jp-productive-evaluation-strategy.md) — JFS Standard productive eval strategy [accepted, S52]
- [ADR-016-authority-anchor-strategy-cross-lang.md](05-decisions/ADR-016-authority-anchor-strategy-cross-lang.md) — 5-layer pipeline EN/ES/IT/DE/JP/RU [accepted, S52]
- [ADR-017-accounting-domain-scope.md](05-decisions/ADR-017-accounting-domain-scope.md) — AccountingDomain Studi RNCP41653 tuteur dual-mode (Lessons + Assistant), rules-first 80%/LLM 20%, Mode B FIRST [accepted, S57]

## 99 — Runbooks

Procédures opérationnelles concrètes.

**Core ops** :
- [gotchas.md](99-runbooks/gotchas.md) — pièges connus et workarounds (Dify, LiteLLM, PG, n8n, webapp, secrets) [authoritative]
- [add-new-agent.md](99-runbooks/add-new-agent.md) — ajouter un nouvel agent/domaine [authoritative]
- [restore-backup.md](99-runbooks/restore-backup.md) — restauration par niveau de backup
- [migrate-taxonomy-v2.md](99-runbooks/migrate-taxonomy-v2.md) — migration Sprint 2 Phase A (forward + rollback)
- [dify-prompt-patch.md](99-runbooks/dify-prompt-patch.md) — 6-step dual-patch procedure Dify (S56) [authoritative]

**Secrets & secrets rotation** :
- [rotate-litellm-keys.md](99-runbooks/rotate-litellm-keys.md) — rotation clés API LLM
- [rotate-secrets-sops.md](99-runbooks/rotate-secrets-sops.md) — édition/rotation/DR secrets SOPS (age)

**Sécu hardening sprints (a-series + b-series)** :
- [a1-redis-aof.md](99-runbooks/a1-redis-aof.md) + [a1-sessions-redis.md](99-runbooks/a1-sessions-redis.md)
- [a2-argon2id-migration.md](99-runbooks/a2-argon2id-migration.md)
- [a3-csp-report-only.md](99-runbooks/a3-csp-report-only.md) [needs-review : add status]
- [a4-mfa-totp.md](99-runbooks/a4-mfa-totp.md)
- [a7-infra-hardening.md](99-runbooks/a7-infra-hardening.md) [needs-review : add status]
- [b1-design-tokens.md](99-runbooks/b1-design-tokens.md) — OKLCH design tokens
- [b4-glitchtip-observability.md](99-runbooks/b4-glitchtip-observability.md) [needs-review : add status]

**Onboarding / pédago activation** :
- [onboarding-qcm-activation.md](99-runbooks/onboarding-qcm-activation.md) [authoritative]
- [phase7-activation.md](99-runbooks/phase7-activation.md) [authoritative]
- [minors-flow-roadmap.md](99-runbooks/minors-flow-roadmap.md) [needs-review : add status]

**RGPD & compliance** :
- [dpia.md](99-runbooks/dpia.md) — Data Protection Impact Assessment
- [rgpd-registre.md](99-runbooks/rgpd-registre.md) — registre traitements
- [transfert-impact-assessment.md](99-runbooks/transfert-impact-assessment.md) — TIA international transfers

## Audit trail

Audits empiriques `webapp/backend/docs/audit/` (per-session, immutable) :
- `2026-04-30-curriculum-en-vs-authority.md` (Hawkins criterial)
- `2026-04-30-curriculum-es-vs-pcic.md` + `2026-05-01-curriculum-es-vs-pcic-c1c2.md`
- `2026-04-30-oracle-battery-v1-acceptable-set-audit.md` (Lyster + Doughty & Varela 1998)
- `2026-05-01-maestro-es-acceptable-set-audit.md`
- `2026-05-01-maestro-es-tier1-battery-postmortem.md` + `tier1-v3-postmortem.md`
- `2026-05-01-maestro-es-mvp-complete-final.md` ⭐ — MVP-acceptable acted S56

## Build references (Wave 2-4 templates)

Cross-langue build templates dans `webapp/backend/docs/` :
- `teacher-en-reference-architecture.md` (S55, 799L) — template Wave 2-4 IT/DE/RU/JP
- `maestro-es-build-gap-audit.md` (S55) — 18 dims, 16 items P0-P3
- `maestro-es-execution-roadmap.md` (S55) — 5 tiers chronologiques

## Legacy (à retraiter)

Anciens docs sous [`_legacy/`](_legacy/) — status `needs-review`. À supprimer après validation migration (voir `_legacy/README.md`).

---

## Conventions

### Header de chaque fichier

```yaml
---
title: <Titre>
status: authoritative | draft | needs-review | stale | superseded | accepted | snapshot
last_reviewed: YYYY-MM-DD
owner: claude | sinse
supersedes: (optionnel, pour ADRs)
---
```

### Statuts

- **`authoritative`** : fait foi, à respecter
- **`accepted`** : décision actée (ADR ou doc architecture)
- **`accepted-in-principle`** : décision prise mais ré-analyse avant implémentation (ADR spécifique)
- **`active`** : sprint en cours
- **`draft`** : en cours, ne pas se baser dessus
- **`needs-review`** : probablement obsolète OU sans frontmatter, à valider avant usage
- **`stale`** : confirmé obsolète, à retraiter ou supprimer
- **`superseded`** : remplacé par un autre doc (ADRs)
- **`snapshot`** : photo ponctuelle, pas vérité temps-réel
- **`shipped-vN-...`** : design doc lié à une version livrée

### Workflow obligatoire

1. **Avant d'implémenter quelque chose de structurel** : lire INDEX.md + les docs pertinentes + ADRs concernés
2. **Si décision architecturale** : créer un nouvel ADR (copier template, numéroter, remplir)
3. **Après implémentation** : mettre à jour les docs impactées (même commit), bumper `last_reviewed`

### Anti-resprawl (S55 convention live)

Avant créer un nouveau `.md`, lire `~/.claude/CLAUDE.md` section DOC PLACEMENT + `~/sinse-vault/meta/conventions.md` decision tree 12 règles. Whitelist racine projet : `TODO|SESSION|SESSION_ARCHIVE|CHANGELOG|CLAUDE|README|HISTORY|PROJECT.md`.

### Maintenance automatique

- `/pickup` ouvre INDEX.md (forcé)
- `/handoff` check que les docs impactées par les changements de code ont été mises à jour

---

*Documentation structurée mise en place : 2026-04-15 (Session 13)*
*Scan exhaustif infrastructure : 2026-04-15 (4 agents parallèles — Docker, filesystem, DB, app surface)*
*Dernière révision INDEX : 2026-05-01 (Session 56 — audit complet post-S13 drift, +12 ADRs/runbooks ajoutés, archived multilang plans, audit trail section, ES MVP-acceptable acted)*
