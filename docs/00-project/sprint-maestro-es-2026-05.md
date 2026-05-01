---
title: Sprint Maestro ES Oracle — 2026-05
date: 2026-05-01
status: active
last_reviewed: 2026-05-01
session_origin: 55
owner: claude
---

# Sprint Maestro ES Oracle — 2026-05

**Context** : MVP Oracle EN cohérence COMPLETE Session 54 (20/26 panel certified). Architecture multi-judge panel + cache + κ Opus + AC2 réutilisable cross-langue tels quels. Maestro ES baseline mesurée S55 = 4/24 → 12/24 (post-judge cross-lang fix) → forecast 19/24 post Phase 0.H Lyster patch. Ce sprint documente le path vers MVP Maestro ES (DoD 18-22/24 stable).

**Plan** : sprint dédié post-S55 incident Dify max_length + cleanup docs sprawl. Phases 0 livrées en S55. Phases 1+ planifiées.

## DoD MVP Maestro ES

- [ ] Score panel cross-provider ≥ 18/24 (75%)
- [ ] AC2 ≥ 0.7 sur 3 dims (cf_move, register, semantic_fidelity)
- [ ] κ Opus super-judge in-chat ≥ 0.7 vs panel sur 3 dims (cross-lang κ établi)
- [ ] 0 stable structural fail (3 runs consécutifs sans régression)
- [ ] 0 over-correction A1-A2 (Lyster ban explicit_correction respected)
- [ ] 0 priority leak risk scenario (Maestro ne corrige pas réponses correctes)

## Phase 0 — Foundation (S55 LIVRÉE 2026-05-01)

### Phase 0.A-0.D ✅
- A : Audit prompts Dify Maestro ES — STRUCTURELLEMENT IDENTIQUES Teacher EN (juste traduction). Pb pas dans le prompt LLM.
- B : Diff prompts EN vs ES confirmé.
- C-D : OBSOLETED (audit révèle pb dans judge code, pas prompt)

### Phase 0.E ✅ — Fix judge code cross-lang (commits `d038dd9` + `1ccc53c`)
- `_l2_word_ratio` : default `l2_code='en'`, accent regex EN-only comptait tous accents ES comme FR
- `METALINGUISTIC_PATTERNS` + `EXPLICIT_CORRECTION_PATTERNS` : EN-only, ne détectaient pas patterns ES
- 3 dicts par-target lang ajoutés (en/es/it/de) + `_scenario_lang(scenario)` helper
- 2e gotcha cascadé : typo `scenario.key` au lieu de `scenario.scenario_key` (Pydantic schema field) — fallback silent à 'en' invisible. Fix `1ccc53c`.
- Smoke 1/6 → 3/6 (50%)
- 49/49 oracle tests green

### Phase 0.F ✅ — Full battery 24 baseline post-fix
- Score : **12/24 (50%)** vs 4/24 baseline (+200%)
- Fail breakdown : 9 cf_move + 7 semantic_fidelity + 2 cf_move_partial

### Phase 0.G ✅ — Re-record 24 goldens
- S51 goldens stales vs S53 changes (curriculum_es 51→98, hints 34→103, functions 42 entries)
- 24/24 re-recorded post-fix codebase

### Phase 0.H ✅ — Audit Lyster acceptable_set ES (commits `4c09654` + `c11ee25`)
- Audit doc : `webapp/backend/docs/audit/2026-05-01-maestro-es-acceptable-set-audit.md`
- 7/9 cf_move fails patched (cross-langue Lyster expansion) :
  - +`prompt_plus_remediation` A2/T2 (Doughty & Varela 1998)
  - +`full_recast` B1+/B2/T2-T3 L1-transfer (Lyster Ch4 §3.1)
  - +`explicit_correction` B2-C1/T3 (Lyster + Lira-Gonzales 2024 + Ellis & Sheen 2006)
- 2/9 KEEP forbidden = real Maestro pedagogy issues (defer Phase 1)
- Forecast post-patch : ~19/24 (79%)

### Phase 0.I (en cours) — Re-run battery measure
- Battery 24 × 5 votes single-judge cerebras-fast en cours

## Phase 1 — Maestro Dify prompt fix (à faire)

3 vrais signaux pédagogiques identifiés Phase 0 — fix Dify prompt Maestro `47b0529c` workflow `d3df0ef0` :

### Phase 1.A — Anti-over-correction A1-A2 (~1j)
- Add directive Dify prompt llm_session : "À A1-A2, JAMAIS d'`explicit_correction` ni de `metalinguistic`. Recast implicite uniquement (Lyster Ch 4 §3.1)."
- Cible scenarios : `a2_t2_preterite_001`, `b1_t2_quantifier_001`
- Test : smoke ≥ 4/6 + cf_move_partial = 0 fail explicit_correction A1-A2

### Phase 1.B — Anti-priority-leak (no-error → no recast) (~0.5j)
- Add directive : "Si le learner produit une phrase CORRECTE, ne recast PAS. Réponds au sens, pose une question follow-up."
- Cible scenario : `risk_priority_leak_b1_es_001`
- Test : risk_priority_leak passe en pass post-fix

### Phase 1.C — Apply panel + cache + κ Opus measurement (~1j)
- Run `--panel cross-provider --cache on` sur full battery
- κ Opus super-judge in-chat scoring 24 ES scenarios
- AC2 Gwet inter-run + per-dim
- DoD : κ Opus vs panel ≥ 0.7 sur 3 dims

## Phase 2 — Stable fails + scaffolding (post Phase 1)

### Phase 2.A — Scaffolding L2 ratio fix (~1j)
- Investigation pourquoi Maestro mixe trop de FR (L2 ratio 0.70-0.83 vs target 0.85-0.95)
- Hypothèses : `learner_profile_summary` injecte FR text qui leak ; `l1_watch` block en EN bias bot ; `rubrics_es.yaml` content
- Patch scaffolding policy ES strict (cf `packages/academie-core/academie_core/pedagogy/scaffolding_policy.py`)

### Phase 2.B — Re-record goldens + final E2E validation
- Battery 24 final post Phase 1+2
- 3 runs consécutifs sans régression (DoD)

## Phase 3 — Inject DELE corpus (P1, ~2.5j)

Books acquired pending extraction (cf vault inventaire books ES) :
- `cervantes-dele-suite` (DELE A1 Modelo) → `mini_exam/es_a1.yaml` + DELE rubric Adecuación/Coherencia/Corrección/Alcance
- `bech-tormo-2013-cronometro-dele-b2` (217p) → `mini_exam/es_b2.yaml` task bank
- `alzugaray-2013-preparacion-dele-b2-soluciones` (26p companion) → rubric calibration

## Phase 4 — PCIC Vol C C1-C2 (P1, ~3j)

WebFetch `cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/` (technique S53 Vol A+B). Extract → `extracted/cervantes-...c1-c2/`. Audit + patch :
- `curriculum_es.yaml` 98 → ~150 concepts
- `concept_hints/es.yaml` 103 → ~180 entries
- `functions/es.yaml` 42 → ~80 entries (A2 → C2)

DoD : ES flagship A1-C2 complete (gap actuel = C1-C2 underspecified).

## Phase 5 — DELE A2/B1/C1/C2 acquisition + injection (P1, ~2j)

- Sinse signup `dele.org` + DL 5 PDFs (~10 min × 5)
- Extract `mini_exam/es_a2.yaml` ... `es_c2.yaml`
- DoD : exam coverage A1-C2 complete

## Effort cumul

| Phase | Effort | Status |
|---|---|---|
| 0.A-0.H | ~3j | ✅ S55 LIVRÉE |
| 0.I | <1j | 🔄 en cours |
| 1.A-1.C | 2.5j | À faire |
| 2.A-2.B | 1.5j | À faire |
| 3 | 2.5j | À faire (books acquired) |
| 4 | 3j | À faire (WebFetch only) |
| 5 | 2j | À faire (Sinse 50min DL) |
| **TOTAL** | **~14.5j** | dont ~3j MVP critical (Phase 0+1) |

**Phase 0+1 = MVP Oracle Maestro ES** → switch authorize Wave 2 IT/DE.
**Phase 2-5 = enrichissement A1-C2 flagship** à étaler.

## Cross-references

- Audit doc Phase 0.H : [`webapp/backend/docs/audit/2026-05-01-maestro-es-acceptable-set-audit.md`](../../webapp/backend/docs/audit/2026-05-01-maestro-es-acceptable-set-audit.md)
- Audit doc Phase C ES (S53) : [`webapp/backend/docs/audit/2026-04-30-curriculum-es-vs-pcic.md`](../../webapp/backend/docs/audit/2026-04-30-curriculum-es-vs-pcic.md)
- Sprint EN parallèle (S54) : [`docs/01-pedagogy/sprint-oracle-en-coherence-2026-05.md`](../01-pedagogy/sprint-oracle-en-coherence-2026-05.md)
- ADR-013 language scope : [`docs/05-decisions/ADR-013-language-scope-by-tier.md`](../05-decisions/ADR-013-language-scope-by-tier.md)
- ADR-016 authority anchor : [`docs/05-decisions/ADR-016-authority-anchor-strategy-cross-lang.md`](../05-decisions/ADR-016-authority-anchor-strategy-cross-lang.md)
- Vault books ES inventory : `vault/knowledge/books/USAGE-MAP.md`
- Vault failures S55 : `vault/projects/academia-ia/failures.md`
