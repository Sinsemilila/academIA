# Session 45 P2g+P2h+P2i — Negative finding (rolled back to V5)

**Date** : 2026-04-22 (late night)
**Prior baseline** : V5 (P2d+P2f) = 22/26 = 85%
**Goal** : push to 25-26/26 via prompt-engineering stack

## TL;DR

Applied three prompt-engineering techniques backed by 2024-2026 research. V6 measurement : **5/26 (19%)** — catastrophic regression vs V5. Isolated the failure mode (pink-elephant priming), reverted P2i, re-tested as V7 : **16/26 (62%)** — still 6 scenarios below V5. Rolled back all three changes to V5 state. Teacher EN sits back at 22/26.

**Core learning** : listing banned phrases verbatim in a prompt — even inside an "if you catch yourself typing X, don't do it" frame — primes the LLM to produce them. The pink-elephant / negation-priming effect (Jang et al. 2023, EMNLP 2024 NegationBench) dominates even when paired with positive reframing. Counter-intuitively, less specific text about the bans worked better than more specific.

## What was applied

### P2g — 4 new anti-pattern entries in `fewshots/en.yaml`
Targeting the 4 structural variants that V5 didn't handle :
- `a2-wrong-multi-error-bundling` (learner "I goed and I taked...")
- `a2-wrong-article-injection-prior` (2nd article-injection variant)
- `b1-wrong-post-recast-verdict` (recast THEN "You used X instead of Y")
- `a1-wrong-multi-turn-regression` (teach-harder on no-uptake)

### P2h — Positive reframing in rubrics/en.yaml
A1/A2/B1 : rewrote "NEVER X" bullet lists as "If you feel the urge to write 'X'... → ALWAYS Y instead" pattern. Kept HARD BAN list but coupled each ban with the positive replacement pattern.

### P2i — FINAL SELF-CHECK block in OUTPUT_SCHEMA_BLOCK
Enumerated banned openers verbatim at the end of the prompt (recency position), asking LLM to scan its planned output for these phrases and regenerate if found.

## What went wrong

### V6 (all three) : 5/26
21 scenarios failed, including B2 and C1 scenarios that had been PASSING for 5+ sessions. The regression was broad, not localized — every rubric level's compliance rate dropped. Pattern : scenarios that had no failure signature in V5 now failed on `cf_move_set_valid` with explicit_correction.

### V7 (P2i reverted, P2g + P2h kept) : 16/26
10 scenarios failed. Better than V6 but still 6 scenarios below V5.

### Root cause hypothesis
Pink-elephant priming :
- Each banned phrase ("It should be", "You should say", "Instead of", "You need") appears verbatim in the prompt 3-5× (anti-pattern wrong_teacher field + rubric ban list + self-check enumeration).
- LLMs activate every token they process. Banning a phrase in text causes it to enter the model's active representation.
- The bigger the prompt, the more activations compete — banned phrases win attention when the instruction is something the model is already trained to do (explicit grammar correction).
- V5 had a small number of banned-phrase mentions; V6-V7 dramatically multiplied them.

Research signal we ignored : option #8 in our prompt-engineering ranking (rank 8 of 8) was "negation reinforcement by repetition" — flagged "**generally counterproductive alone — repetition of the banned phrase increases its activation**". We thought positive reframing (#2) would neutralize this. It did not ; the compounding of repetitions across 3 interventions hit the priming threshold hard.

## What we kept and what we reverted

Rolled back to commit `5d7b246` (V5 ship state) for :
- `packages/academie-core/academie_core/data/rubrics/en.yaml` (P2h revert)
- `packages/academie-core/academie_core/data/fewshots/en.yaml` (P2g revert — anti-pattern count stays at 9)
- `packages/academie-core/academie_core/pedagogy/teacher_prompt.py` (P2i revert)
- `packages/academie-core/tests/test_teacher_prompt.py` (remove P2i self-check tests, restore 28 test count)
- 26 × `scripts/oracle/scenarios/teacher_en/golden/*.json` (V5 goldens restored)
- `scripts/oracle/config.yaml::modes.full.n_votes` restored 3

## What stays V5 (the working state)

- TIER_TO_FEEDBACK_BY_LEVEL (P2 core mapping) — code-level bug fix, unit-tested
- A1/A2/B1 rubric HARD BAN sections (P2d) — simpler bullet format, fewer verbatim phrase listings
- 9 anti-pattern entries (P2c+P2d : 3 A1 + 2 A2 + 3 B1 + 1 extra A2)
- L2_ratio_band [0.7, 1.0] on 7 A1 scenarios (P2f)
- Gemini-flash / gemini-3-1-flash-lite judge chain (κ=0.84)

## Lessons for Session 46

1. **Never repeat banned tokens more than ~2× total in a prompt**, no matter how you frame them. Pair with positive reframing means replacing, not adding alongside.

2. **Structured output enum constraints** (option #1 in our research — OpenAI Structured Outputs 100% schema adherence, Anthropic tool-use forcing) were NOT tried tonight. That's the next-session move : make `feedback_type` an enum that physically excludes `explicit_correction` — LLM can't emit what the schema forbids.

3. **Ablation over aggregation** : applying 3 changes together saved budget (single V6 run) but cost us the ability to isolate which technique helped and which hurt. Next time : one change, one measurement, then stack if positive. Ablation costs 150 more calls but saves a full rollback cycle.

4. **V5 22/26 is the gpt-4o-mini ceiling via prompt engineering** — beyond that either structured outputs (option #1) or model upgrade.

## Artifacts kept

- `docs/oracle/session45_noise_floor_v5_post_p2d_p2f.md` (V5 baseline, still valid)
- `docs/oracle/session45_noise_floor_v5_single_run.json` (raw V5)
- `/tmp/p2ghi_v6.log` (V6 raw, not committed)
- `/tmp/p2gh_v7.log` (V7 raw, not committed)
- This document

## No further measurement needed tonight

V5 working tree = commit `5d7b246`. We trust the V5 measurement directly. Budget Gemini : ~101 RPD remaining, preserved for Session 46 P3 (fault injection redesign) or an ablated P2-next attempt.
