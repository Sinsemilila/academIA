# Session 45 — Oracle noise floor V2 post judge migration

**Date** : 2026-04-22 (late evening)
**Judge** : `gemini-3-1-flash-lite` (direct, 500 RPD free tier, κ=0.84 vs majority per Session 44 calibration)
**Scenarios** : 26 Teacher EN, full-mode, N=3 votes per dim
**Runs** : 2 back-to-back (K=2 per Session 40 design doc)

## TL;DR

Switching from `gpt-4o-mini` (κ=0.33, Session 40-43 judge) to `gemini-3-1-flash-lite` (κ=0.84) made the Teacher EN pedagogical bug **visible and reproducible** for the first time. **6 A1/A2 scenarios consistently fail** across both runs on `cf_move_set_valid` — Teacher produces forbidden CF moves (`explicit_correction`, `metalinguistic`) at levels where they are explicitly banned by the rubric. A secondary `L2_ratio=1.00` bug surfaces on 3 A1 scenarios (100% English with no L1 FR scaffolding).

## Noise floor per dim (V2 baseline)

| Dim | V1 (gpt-4o-mini, Session 43 O4) | V2 (gemini-3-1-flash-lite, today) | Direction |
|---|---|---|---|
| `cf_move_set_valid` | 0.154 (15.4%) | **0.000** | 16× better ★ |
| `cf_move_set_valid_partial` | 0.077 | 0.115 | slightly noisier |
| `register_cefr_alignment` | 0.192 | **0.000** | 19× better ★ |
| `recast_saliency_and_dosage` | 0.000 | 0.000 | stable (deterministic) |
| `scaffolding_flags_honored` | 0.000 | 0.000 | stable (deterministic) |
| `scaffolding_flags_l2_ratio` | 0.154 | 0.038 | 4× better ★ |
| `semantic_fidelity_pairwise` | 0.077 | 0.038 | 2× better ★ |

**Interpretation** : the LLM-judged dims (`cf_move_set_valid`, `register_cefr_alignment`, `cf_move_set_valid_partial`, `semantic_fidelity_pairwise`) collapsed their between-run disagreement with the better judge. `cf_move_set_valid_partial` is a slight exception — likely real Teacher-output variance hitting a softer threshold.

Note : FPR=0.0 does NOT mean "all scenarios pass" — it means "the judge is consistent between runs". Many scenarios consistently FAIL on both runs ; that's signal, not noise.

## Consistently-failing scenarios (bug confirmed)

| Scenario | CEFR / Tier | Failure dim | Detail |
|---|---|---|---|
| `a2_t2_past_simple_001` | A2 / T2 | `cf_move_set_valid` | move=explicit_correction (forbidden at A2) |
| `a2_t2_plural_high_fla_001` | A2 / T2, FLA high | `cf_move_set_valid` | move=explicit_correction (forbidden) |
| `el_a1_t2_misc_001` | A1 / T2 | `scaffolding_flags_l2_ratio` | L2_ratio=1.00 (no L1 FR scaffolding) |
| `multi_a1_verb_no_uptake_001` | A1 / T2 | `cf_move_set_valid_partial` + `l2_ratio` | metalinguistic forbidden + 100% L2 |
| `multi_a2_art_uptake_001` | A2 / T2 mid | `cf_move_set_valid_partial` | move=explicit_correction |
| `risk_l1_drift_a1_001` | A1 / T2 mid | `cf_move_set_valid_partial` + `l2_ratio` | explicit_correction + 100% L2 |

**Pattern** : all 6 confirmed fails are A1/A2. The Teacher prompt's `TIER_TO_FEEDBACK_DEFAULT` mapping is level-agnostic ([teacher_prompt.py:70-79]) — it produces `metalinguistic` / `explicit_correction` at tiers where the per-level rubric ([rubrics/en.yaml:5-24]) explicitly bans them.

**Secondary L2-ratio bug** : at A1, Teacher EN currently emits 100% English. The rubric + L1/L2 mix policy requires ~70-85% L2 mixed with L1 French glosses (Butzkamm sandwich technique) for A1 beginners. Root cause likely the scaffolding_block not reaching the LLM nodes correctly, or the prompt ignoring the L2_ratio_band directive.

## Between-run volatility (4 scenarios flipped)

| Scenario | Run 1 | Run 2 | Hypothesis |
|---|---|---|---|
| `b1_edge_t2t3_prepositions_001` | ❌ | ✅ | Teacher stochastic response borderline |
| `b1_t2_articles_001` | ✅ | ❌ | ditto |
| `el_a1_t2_misc_002` | ❌ | ✅ | ditto |
| `risk_a1_metalinguistic_leak_001` | ❌ | ✅ | ditto |

These 4 flip between runs because the live Dify response varies across sessions (same prompt, different conversation_id). Judge is consistent ; the Teacher is borderline on these. Not a judge problem.

## Next steps (per plan /root/.claude/plans/soft-sparking-ocean.md)

→ **Phase 2** : refactor `TIER_TO_FEEDBACK_DEFAULT` → `TIER_TO_FEEDBACK_BY_LEVEL[level][tier]` in
`packages/academie-core/academie_core/pedagogy/teacher_prompt.py`. A1 : no metalinguistic, no explicit_correction at any tier ; A2 : metalinguistic only after recurrence (T3+).

→ **Also address L2_ratio bug** separately : check whether `scaffolding_block` reaches the llm_onboarding + llm_session nodes correctly and the prompt enforces the L2_ratio_band.

→ Re-record affected goldens after fix → re-run noise_floor V3 → expect cf_move_set_valid_partial FPR to drop + L2_ratio scenarios to pass.

## Replay

```
docker exec academie-api env | grep DIFY_KEY_TEACHER || (
  export DIFY_KEY_TEACHER=$(cat /opt/academie-shared/secrets/dify-teacher-key)
)
python3 scripts/oracle/preflight_gemini.py --mode full       # verify budget
python3 scripts/oracle/noise_floor.py --runs 2 --mode full --agent teacher_en
# Results in config.yaml::noise_floor + /tmp/oracle_noise_floor.json
```

Total cost ~520 LLM calls (Gemini 3.1 Flash Lite, free tier).
Wall time ~15 min at 15 RPM steady state.
