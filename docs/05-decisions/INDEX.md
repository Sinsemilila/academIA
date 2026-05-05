---
status: authoritative
last_reviewed: 2026-05-01
tags: [reference, architecture]
session_origin: 55
---

# ADRs index — AcademIA architecture decisions

**Source-of-truth pour toutes les décisions d'architecture**. Cleanup S55 a archivé les sources concurrentes (`/opt/academia/DECISIONS.md` historique chronologique + `/opt/academia/docs/decisions.md` table flat) → `_archive/`. Nouvelles décisions = nouveau ADR-NNN-`<slug>`.md via skill `/decision`.

## Active ADRs (20)

| # | Title | Status | Date | Slug |
|---|---|---|---|---|
| 0001 | Adopt MADR-lite for architecture decisions | accepted | 2026-04-13 | [`0001-adr-format`](0001-adr-format.md) |
| 0002 | Exam system as advisor, not gatekeeper | accepted | 2026-04-13 | [`0002-exam-advisor-not-gatekeeper`](0002-exam-advisor-not-gatekeeper.md) |
| 0003 | Behavior detection via prompt, not backend ML | accepted | 2026-04-13 | [`0003-behavior-detection-prompt-first`](0003-behavior-detection-prompt-first.md) |
| 001 | Architecture monolithe FastAPI (microservices envisagés) | accepted | — | [`ADR-001-monolith-vs-microservices`](ADR-001-monolith-vs-microservices.md) |
| 001b | Refactor complet academia.petit-pont.com (2026-H2) | — | — | [`ADR-001-refactor-complete-2026-H2`](ADR-001-refactor-complete-2026-H2.md) |
| 002 | Schéma taxonomie multi-langue + multi-domaine dès départ | accepted | — | [`ADR-002-schema-from-day-1`](ADR-002-schema-from-day-1.md) |
| 003 | 5 tiers gravité erreur (T0-T4) | accepted | — | [`ADR-003-5-tiers-taxonomy`](ADR-003-5-tiers-taxonomy.md) |
| 004 | Architecture hybride orchestrée topologie agents | accepted | — | [`ADR-004-hybrid-orchestrated-agent-topology`](ADR-004-hybrid-orchestrated-agent-topology.md) |
| 005 | Package Python `academie-core` shared library | accepted | — | [`ADR-005-academie-core-shared-library`](ADR-005-academie-core-shared-library.md) |
| 006 | LiteLLM BYOK familial pour coûts LLM | accepted | — | [`ADR-006-litellm-byok-familial`](ADR-006-litellm-byok-familial.md) |
| 007 | Versioning snapshots — migration cut-off propre (option C) | accepted | — | [`ADR-007-snapshot-versioning-cutoff`](ADR-007-snapshot-versioning-cutoff.md) |
| 008 | ERRANT mapping reporté Sprint 5+ (table traduction non-natif) | accepted | — | [`ADR-008-errant-mapping-later`](ADR-008-errant-mapping-later.md) |
| 009 | Gravity axes colonnes dénormalisées sur `error_log` | accepted | — | [`ADR-009-gravity-axes-schema`](ADR-009-gravity-axes-schema.md) |
| 010 | Cosmos L4 hardening via `tecnativa/docker-socket-proxy` | accepted | — | [`ADR-010-cosmos-L4-docker-socket-proxy`](ADR-010-cosmos-L4-docker-socket-proxy.md) |
| 011 | Systèmes niveau natifs JLPT (JP) + TORFL (RU) | accepted | — | [`ADR-011-native-level-systems-jlpt-torfl`](ADR-011-native-level-systems-jlpt-torfl.md) |
| 012 | Remédiation sécurité repo public (secrets leakés) | accepted | 2026-04-19 | [`ADR-012-security-remediation-2026-04-19`](ADR-012-security-remediation-2026-04-19.md) |
| 013 | Language scope by tier (EN+ES flagship A1-C2 / IT+DE+JP+RU A1-B2) | accepted | 2026-04-29 | [`ADR-013-language-scope-by-tier`](ADR-013-language-scope-by-tier.md) |
| 014 | Structured knowledge extraction from canonical books | accepted | 2026-04-29 | [`ADR-014-structured-knowledge-extraction`](ADR-014-structured-knowledge-extraction.md) |
| 015 | Wave 3 JP productive evaluation strategy | proposed | 2026-04-29 | [`ADR-015-jp-productive-evaluation-strategy`](ADR-015-jp-productive-evaluation-strategy.md) |
| 016 | Authority anchor strategy cross-lang (5-layer pipeline) | proposed | 2026-04-29 | [`ADR-016-authority-anchor-strategy-cross-lang`](ADR-016-authority-anchor-strategy-cross-lang.md) |

## Création nouveau ADR

```bash
# skill /decision auto-incrémente NNN suivant
/decision <slug-court>
```

Template : [`ADR-template.md`](ADR-template.md). Format MADR-lite (cf ADR-0001).

**Status workflow** : `proposed` → Sinse review → `accepted` (immutable). Si décision révisée : nouveau ADR `supersedes: ADR-NNN`.

## Archive (sources concurrentes pre-S55 cleanup)

- `_archive/HISTORICAL-DECISIONS-2026-04.md` — chronologique pointers (anciennement `/opt/academia/DECISIONS.md` racine, 2026-04-13 stale)
- `_archive/decisions-flat-table-2026-04.md` — table 18 entries (anciennement `/opt/academia/docs/decisions.md`, 2026-04-23 stale)

Conservés pour traçabilité historique. Pas de nouvelle entrée — tout va dans `ADR-NNN-<slug>.md` désormais.

## Numbering convention

- `0001-` à `0003-` : seed initial Sprint 1 (avant adoption MADR-lite formal). Format conservé.
- `ADR-001` à `ADR-016` : depuis Sprint 4 (post-refactor 2026-04-13), format MADR-lite avec `ADR-NNN-<slug-en-anglais>.md`.
- Ambiguïté `ADR-001` × 2 (monolith-vs-microservices + refactor-complete-2026-H2) : différents scope, conservés tels quels (pre-S55). Future ADR évite collision.
