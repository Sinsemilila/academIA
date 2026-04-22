# Session 45 P2 — Oracle noise floor V3 post TIER_TO_FEEDBACK_BY_LEVEL fix

**Date** : 2026-04-22 (late evening)
**Judge** : `gemini-3-1-flash-lite` (unchanged from V2)
**What changed vs V2** : rubric `en.yaml` A1 + A2 rewritten with HARD BAN anti-patterns ; `TIER_TO_FEEDBACK_BY_LEVEL` replaces level-agnostic default ; `tier_to_feedback_type()` + callers now pass `level` ; A1 T3 collapses to `implicit_recast` (was `elicitation` / `metalinguistic` via diversity rule).

## TL;DR

The code fix is correct (20 pytest parametric tests green, A1 unit tests confirm implicit_recast-only), but **gpt-4o-mini (the Teacher LLM) still ignores the A1 rubric bans in ~3 scenarios per run**. We resolved 2 A2/B1 scenarios that were failing explicit_correction in V2, but gained 1 B1 regression and flipped the failure mode on one A1 scenario from explicit_correction → metalinguistic. Net : marginal improvement on the underlying scenarios, no structural win yet.

The raw FPR numbers SPIKED (cf_move_set_valid 0.0 → 0.308) because the Teacher now produces materially different responses per session — the between-run variance is real, not judge noise. Goldens are stale (recorded pre-fix), causing `semantic_fidelity_pairwise` FPR to spike too (0.038 → 0.269).

## V2 → V3 pass comparison

| Scenario | V2 R2 | V3 R2 | Change |
|---|---|---|---|
| `a2_t2_past_simple_001` | ❌ explicit | ❌ explicit | no change (A2 LLM non-compliant) |
| `a2_t2_plural_high_fla_001` | ❌ explicit | ✅ | **fixed** |
| `b1_t2_articles_001` | ❌ explicit | ✅ | **fixed** |
| `b1_edge_t2t3_prepositions_001` | ✅ | ❌ explicit | **regressed** |
| `el_a1_t2_misc_001` | ❌ L2_ratio | ❌ L2_ratio | unchanged |
| `multi_a1_verb_no_uptake_001` | ❌ metaling + L2 | ❌ metaling + L2 | unchanged |
| `multi_a2_art_uptake_001` | ❌ explicit | ❌ explicit | unchanged |
| `risk_a1_metalinguistic_leak_001` | ✅ | ❌ L2_ratio only | flipped (cf_move clear, L2 fail) |
| `risk_l1_drift_a1_001` | ❌ explicit + L2 | ❌ metaling + L2 | failure mode flipped |

## Noise floor FPR — V2 vs V3

| Dim | V2 | V3 | Interpretation |
|---|---|---|---|
| cf_move_set_valid | 0.000 | 0.308 | Teacher output variance increased (different responses per run) |
| cf_move_set_valid_partial | 0.115 | 0.077 | slightly better |
| register_cefr_alignment | 0.000 | 0.269 | variance from new prompt |
| recast_saliency_and_dosage | 0.000 | 0.000 | deterministic, unaffected |
| scaffolding_flags_l2_ratio | 0.038 | 0.000 | better (consistent fail) |
| semantic_fidelity_pairwise | 0.038 | 0.269 | **goldens now stale vs new prompt output** |

## Findings

1. **Code fix works** : A1 unit tests prove `tier_to_feedback_type` no longer returns metalinguistic / elicitation. Mapping is CEFR-correct.

2. **LLM compliance remains partial** : even with HARD BAN rubric + level-specific feedback_type directive, gpt-4o-mini still chooses `metalinguistic` / `explicit_correction` on ~30% of A1/A2 turns. The model has strong training priors for "correct grammar explicitly" that our prompt can't fully override at this size.

3. **Goldens are now stale** : the recorded goldens (pre-fix) differ meaningfully from current responses → `semantic_fidelity_pairwise` will stay elevated until they're re-recorded.

4. **L2_ratio=100% persists** : 3 A1 scenarios still show 100% English with no L1 FR gloss. The `scaffolding_block` directive is reaching the prompt but the LLM doesn't honor it for simple turns (nothing to gloss → uses all L2). May need band relaxation [0.7, 1.0] OR stronger directive in the rubric.

## Next (Session 45 P2a + P2b + P2c)

- **P2a** : re-record goldens for all 7 affected scenarios with new prompt. Restores semantic_fidelity_pairwise baseline. ~7 Dify calls, ~10 min.
- **P2b** : add anti-pattern fewshots to `fewshots/en.yaml` — explicit "WRONG at A1" examples so the LLM learns by contrast. ~2-3 examples.
- **P2c (deferred)** : if P2a + P2b don't bring A1 fails to 0, consider Phase 7 (surface `scaffolding_block` as dedicated Dify input) or upgrade Teacher LLM (gpt-4o-mini → gpt-4o or claude-haiku, ~2-3× cost but better instruction-following).

## Artifacts

- `docs/oracle/session45_noise_floor_v3_run1.json` (raw V3 run 1)
- `docs/oracle/session45_noise_floor_v3_run2.json` (raw V3 run 2)
- `scripts/oracle/config.yaml::noise_floor` (V3 persisted baseline)
