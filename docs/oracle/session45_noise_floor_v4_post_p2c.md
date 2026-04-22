# Session 45 P2a+P2c — Oracle V4 measurement (post goldens refresh + anti-patterns)

**Date** : 2026-04-22 (late evening)
**Judge** : `gemini-3-1-flash-lite` (unchanged)
**What changed vs V3** : (a) 26 goldens re-recorded against new prompt (semantic_fidelity baseline restored) ; (b) 4 anti-pattern entries added to `fewshots/en.yaml` (3 A1 + 1 A2, showing wrong_teacher vs correct_teacher contrast) ; (c) render_fewshots_block emits an "=== ANTI-PATTERNS — DO NOT PRODUCE ===" section at A1/A2.

## TL;DR

Anti-pattern fewshots **clearly worked at A1** : 3 A1 scenarios that had been failing metalinguistic/explicit_correction since V1 now pass on cf_move_set_valid for the first time. But B1 regressed by 3 scenarios : Teacher now produces `explicit_correction` at B1 where only `partial_recast`/`elicitation`/`metalinguistic` are in the acceptable set. The rubric A1/A2 anti-ban strengthening doesn't propagate its spirit to B1 rubric (which wasn't updated), so the LLM's baseline behavior at B1 (liberal explicit correction) surfaces the gate.

Single run (not 2×), so FPR isn't computed — but pass/fail deltas vs V3 R2 are meaningful.

## V3 R2 → V4 deltas

| Scenario | V3 R2 | V4 | Δ |
|---|---|---|---|
| `a2_t2_past_simple_001` | ❌ explicit | ❌ explicit | = |
| `a2_t2_plural_high_fla_001` | ✅ | ❌ explicit | **regression** |
| `a2_t3_articles_midfla_001` | ✅ | ✅ | = |
| `b1_edge_t2t3_prepositions_001` | ❌ explicit | ❌ explicit | = |
| `b1_t2_articles_001` | ✅ | ❌ explicit | **regression** |
| `b1_t3_conditional_midfla_001` | ✅ | ❌ move_not_in_acceptable | **regression** |
| `b1_t3_present_perfect_001` | ✅ | ❌ move_not_in_acceptable | **regression** |
| `el_a1_t2_misc_001` | ❌ L2_ratio | ✅ | **fix** |
| `multi_a1_verb_no_uptake_001` | ❌ metaling+L2 | ✅ | **fix** |
| `multi_a2_art_uptake_001` | ❌ explicit | ❌ explicit | = |
| `risk_a1_metalinguistic_leak_001` | ❌ L2_ratio | ❌ L2_ratio only (cf clear) | **partial fix** |
| `risk_l1_drift_a1_001` | ❌ metaling+L2 | ❌ explicit+metaling+L2 | **moved failure mode** |

Net scenario-level : **+3 A1 wins, -4 A2/B1 regressions**, 1 partial. Overall pass rate 17/26 vs V3 R2's 19/26 — slightly worse, but the A1 compliance improvement is the real signal (was stuck for 5 sessions).

## Root cause of B1 regression

The `rubrics/en.yaml` A1 + A2 entries were rewritten with HARD BAN anti-pattern language ; B1 entry was left untouched. gpt-4o-mini's default instruction-following behavior is "correct grammar explicitly with the rule" — it's suppressed at A1 now (anti-patterns + strengthened rubric) but surfaces at B1 because B1 rubric doesn't tell it otherwise.

**Fix (deferred to P2d)** : extend the ANTI-PATTERNS mechanism to B1 scenarios where `forbidden=[explicit_correction]` or `acceptable` excludes explicit_correction. Add B1 anti-pattern entries showing explicit_correction as wrong when partial_recast/elicit/metalinguistic is expected.

## Session 45 Phase 2 final state

**Shipped** :
- TIER_TO_FEEDBACK_BY_LEVEL mapping (bc A1 can't emit elicit/metalinguistic from code path)
- A1 + A2 rubric HARD BAN strengthening
- 4 anti-pattern contrast examples (3 A1 + 1 A2)
- 26 goldens refreshed against current prompt
- 26 pytest tests locking down the mapping + anti-pattern rendering

**Partial — A1 better, B1 regressed** :
- A1 cf_move compliance : 2-3 scenarios fixed (was stuck since V1)
- B1 cf_move compliance : 3 new regressions (rubric B1 unchanged, LLM defaults surface)

**Not yet addressed** :
- L2_ratio=1.00 bug at A1 (3 scenarios still) — `scaffolding_block` directive reaches prompt but LLM doesn't honor when no new grammar item
- Consistent A2 explicit_correction (`a2_t2_past_simple_001`, `multi_a2_art_uptake_001`)
- B1 over-explicit new pattern

## Next session entry point (Session 46 P2d + P3)

- **P2d** : extend anti-patterns to B1 (3-4 entries), update B1 rubric with explicit vs partial/elicit/metalinguistic guidance. Re-run V5 single-run.
- **P3** (fault injection redesign with delta gating) : can start independently even if P2d not converged.

## Artifacts

- `docs/oracle/session45_noise_floor_v4_single_run.json` (raw harness output)
- `scripts/oracle/config.yaml::noise_floor` (unchanged from V3 — single run doesn't update)
