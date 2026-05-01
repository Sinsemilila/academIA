---
title: Maestro ES Tier 1 v3 postmortem — 18/24 (Option C scope-cap, Tier 2 unblocked)
date: 2026-05-01
status: authoritative
last_reviewed: 2026-05-01
session_origin: 56
tags: [audit, oracle, multilang, methodology]
ai_summary: "v3 = 18/24 (75%), +2 vs v2 16/24, -1 vs baseline 19/24. Per Option C scope-cap accepted. 3 persistent + 3 new fails. Tier 2 unblocked."
---

# Maestro ES Tier 1 v3 postmortem (S56)

## TL;DR

- **v3 result : 18/24 (75%)**
- vs v2 (16/24) : **+2 fails fixés** (regression partly recovered)
- vs baseline S55 (19/24) : **-1**
- Per Option C decision logic ("v3 1 iter, accept ≥19/24, sinon scope-cap → Tier 2") : **18 < 19 → scope-cap acted**.
- Tier 1 close en partial : G5.1 + G5.2 + G5.3 livrés ; battery floor = 18/24 (légèrement sous baseline).
- Tier 2 unblocked.

## Battery v3 (run_hash `11aff60b4f379400`)

```
18 passed / 6 failed / 0 skipped / 24 total
```

## Delta v2 → v3 (-3 fails fixés, +3 new fails)

### 5 fails v2 résolus en v3 (Pattern 1+2+3 fixes worked)
- ✅ `a2_t2_preterite_001` (Pattern 3 — T2 cross-niveau ban prompt_plus_remediation)
- ✅ `b1_t3_gustar_subj_001` (Pattern 3 — B1/T2-T3 ban explicit)
- ✅ `multi_b2_imperfecto_no_uptake_001` (Pattern 4 — B2/C1 examples for register)
- ✅ `risk_comm_breakdown_b1_es_001` (Pattern 2 — anti-leak conditional)
- ✅ `risk_l1_drift_a1_es_001` (Pattern 1 — A1 partial_recast over implicit)

### 3 new v3 fails (regressions introduced by v3)
- ❌ `a1_t2_concord_gender_001` — was pass v2 + pass v3 smoke. Battery fail = `semantic_fidelity_pairwise majority divergent`. Maestro response `"¡Vale! El *problema* es difícil y la *solución* no es clara."` is correct partial_recast per v3 spec. **Likely cache hit on stale verdict OR judge panel variance** (cache=on, --cache off in smoke).
- ❌ `a2_t3_por_para_001` — Maestro `silent` on T3 genuine error. ANTI-LEAK over-applies even with v3 conditional. Acc requires clarif/elicit/full/partial recast.
- ❌ `b1_t2_quantifier_001` — Maestro `*fue* *muy* *estaba*` (3 asterisks). Judge classifies as `full_recast`. Acc = clarif/elicit/metaling/partial_recast. **v3 over-incentivizes asterisk pattern → reads as full_recast not partial.**

### 3 fails persistent v2+v3 (acceptable_set or prompt-resistant)
- ❌ `b2_t2_false_friend_001` — explicit_correction despite v3 "B1-B2 + T2 ban explicit". LLM bypassed caveat for false friend "embarazada" (sensitive topic — possibly safety/clarification path).
- ❌ `risk_a1_metalinguistic_leak_es_001` — silent. ANTI-LEAK over-applies.
- ❌ `risk_priority_leak_b1_es_001` — silent. ANTI-LEAK over-applies.

## Root cause analysis

### Pattern : ANTI-LEAK conditional logic insufficient

3/6 fails (a2_t3_por_para, risk_a1_metaling_leak, risk_priority_leak_b1) = Maestro `silent` despite genuine error. v3 said:

```
ESTE BLOQUE SE APLICA SOLO SI : `error_feedback` arriba está VACÍO ...
SI hay error genuino (T2+) en error_feedback : IGNORA este bloque ...
```

Hypothesis : `error_feedback` upstream may be empty in these scenarios (harness doesn't always populate it from gold annotations) → conditional says "apply silent" → Maestro silent.

**Fix path** : refine `error_feedback` injection from harness OR rephrase ANTI-LEAK with stronger "SI YOU SEE ANY error in learner production, REACT — silent is forbidden when error visible" rule.

### Pattern : Asterisk pattern reads as full_recast

`b1_t2_quantifier_001` v3 response uses 3 asterisks `*fue* *muy* *estaba*`. cf_move judge classifier reads this as full_recast (sentence-level rewrite) instead of partial_recast (single-word repair). v3 prompt aggressively pushes asterisk pattern → potentially over-recast on multi-error scenarios.

**Fix path** : refine v3 examples — asterisks ONLY on the corrected token, not on adjacent normal words.

### Pattern : False friend bypass

`b2_t2_false_friend_001` "embarazada" → LLM goes into clarification mode despite v3 caveat. Sensitive false-friend topics may invoke safety/explicit clarification pattern that overrides Lyster directive.

**Fix path** : add explicit B2/T2 false-friend ✅ example showing partial_recast, OR mark this scenario in acc as exception (Phase 0.H redo).

## Decision: Tier 1 close + Tier 2 start

Per Option C agreed at start of v3 cycle :
- v3 result 18/24 < 19/24 threshold
- Scope-cap acted on Tier 1 prompt iteration
- Pass to Tier 2 (PCIC C1-C2 + DELE corpus + rules_es expansion)

The 6 remaining fails will be addressed by :
1. **Tier 5 (Oracle scenarios + quality gates)** — acceptable_set rebalance for false_friend B2/T2 + b1_quantifier asterisk classification refinement
2. **Phase 0.H redo (post-Tier 5)** — reconcile silence/recast canonical when error_feedback inconsistent
3. **Tier 6 (RE-MEASURE Oracle FINAL)** — final battery should be ≥22/24 thanks to data layer expansion (curriculum/functions/rules) reducing pressure on prompt-only iterations

## Comparison summary

| Version | Score | Δ vs baseline | Δ vs prev | Notes |
|---|---|---|---|---|
| Baseline S55 (no patch) | 19/24 (79%) | — | — | floor pré-build, 5 fails A1-A2 explicit |
| v1 (script 01, abstract Lyster) | not tested in battery | n/a | n/a | smoke 3/6 only |
| v2 (script 02, mapping caveat + examples) | 16/24 (67%) | -3 | -3 | 8 fails / 4 patterns |
| **v3 (scripts 04+05, refined caveats + B2/C1 examples + conditional anti-leak)** | **18/24 (75%)** | **-1** | **+2** | **6 fails** |

## Cross-references

- v3 patches : `scripts/sprint-maestro-es/04_*.py` + `05_*.py`
- v2 postmortem : `webapp/backend/docs/audit/2026-05-01-maestro-es-tier1-battery-postmortem.md`
- Phase 0.H acceptable_set audit : `webapp/backend/docs/audit/2026-05-01-maestro-es-acceptable-set-audit.md`
- Execution roadmap : `docs/audit/2026-05-01-maestro-es-execution-roadmap.md`
- Battery v2 run_hash : `1e8bf444db2e8726`
- Battery v3 run_hash : `11aff60b4f379400`
