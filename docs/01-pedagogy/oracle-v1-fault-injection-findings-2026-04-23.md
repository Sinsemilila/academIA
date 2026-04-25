# Oracle V1 fault injection — findings 2026-04-23

**Status** : methodology empirically invalidated, alternatives documented.

## Run attempted

Single fault (force_long_response) + clean baseline via LiteLLM bypass with
placeholder stubbing. All 5 LLM-judged dims active, with pairwise dropped
per Session 41 methodology fix.

## Results

| Condition | Flagged | Total | Rate |
|---|---|---|---|
| Clean baseline (no fault) | 18 | 24 | 75.0% |
| force_long_response | 20 | 24 | 83.3% |
| **Delta** | +2 | 0 | +8.3pp |

Gate requires ≥90% detection AND ≤10% false alarm. **FAIL** on both.

## Root cause

The LiteLLM-bypass bot (called directly with stubbed Dify placeholders)
behaves materially differently from the real Dify-served Teacher EN bot :

- Lacks real conversation context (no profile, no prior errors, no priority concepts block)
- Operates in a "fresh onboarding" posture even with CEFR-stubbed prompt
- Occasionally outputs verbose explanations even on plain prompt (our stub
  can't fully replace the scaffolding_block's dosage constraints)

As a result, the deterministic dims (`recast_saliency`, `scaffolding_flags_l2_ratio`,
`cf_move_set_valid_partial`) legitimately flag many clean-baseline responses
as over-long / French-leaning / metalinguistic — but these "flags" reflect
**bot degradation under bypass**, not prompt regressions.

Adding a fault (`force_long_response`) makes things slightly worse (+8pp
flag rate) but not detectably so beyond the bypass noise.

## What this does NOT mean

- **Not** that the oracle is broken — the dims themselves work (see Phase
  C noise floor measurement where deterministic dims showed 0% drift run-to-run).
- **Not** that the Teacher EN prompt is regressing — we're testing a
  simulated bot in degraded conditions, not the real deployed one.
- **Not** that fault injection is abandoned — just that LiteLLM bypass
  isn't the right call-path.

## Alternative approaches — ranked

### A. Dify-workflow-based fault injection (proper, ~4-8h effort)

Apply the fault to a cloned Teacher EN app's `workflows.graph` JSONB
via `scripts/dify/clone_app.py --prompts-override`, run scenarios against
the clone's API key, compare golden responses (also recorded from Dify).
The original V1 plan.

**Status** : blocked by clone hang on Session 40 (investigation postponed).
Recent `delete_legacy_app.py` fix + addition of `sites` table may help.
Worth retrying in Session 42.

### B. Delta gating (pragmatic, ~2h effort)

Replace absolute gate (detect ≥90%, FA ≤10%) with **delta gate** :
`detection_rate - false_alarm_rate > threshold`. Tuned empirically from
noise floor. Keeps LiteLLM bypass, just changes interpretation.

Caveat : delta gating is less intuitive and harder to defend when a
reviewer asks "is 8pp enough?". But it's directionally correct — a real
regression should produce a much bigger delta than noise.

Estimate : 2h to redesign + validate against the 5 faults.

### C. Distributional invariants (cheapest, ~3h effort)

Don't try to judge individual responses. Measure aggregate shape across
24 scenarios : mean response length, L2 ratio distribution, CF move
histogram, observed_level emission rate. If aggregate shape shifts by
>2σ vs baseline, flag.

Robust to individual-response noise. But slower to deploy + requires
historical baseline data.

Estimate : 3h for minimal viable implementation.

## Recommendation for Session 42

Try option A first (Dify clone retry with fresh code). If still hangs,
fall back to B (delta gating) which is cheapest. C stays as a nice-to-have
for continuous monitoring (separate from CI gate).

## What shipped from this attempt

- `scripts/oracle/fault_injection.py` : agent-agnostic, improved stub
  with L2-forcing directives, N=1 concurrent judge calls
- `scripts/oracle/record_golden_litellm.py` : parallel golden recorder
  via LiteLLM bypass (unused until we commit to path B or similar)
- `scripts/dify/delete_legacy_app.py` : fixed `apps.id` bug + `sites`
  table missing (unlocks cleaner clone lifecycle)

Infrastructure is sound. Methodology for fault injection needs Session 42
revisit.
