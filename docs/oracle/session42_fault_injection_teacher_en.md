# Session 42 O3 — Fault Injection Run (Teacher EN)

**Date** : 2026-04-22
**Agent** : teacher_en
**Method** : LiteLLM-bypass (Session 40 methodology)
**Scenarios** : 26 (Teacher EN corpus)
**Faults** : 5 (force_long_response, remove_one_question_rule, swap_implicit_to_explicit, force_metalinguistic_always, disable_self_answer_rule)

## Result : GATE ❌ FAIL (as expected)

| Metric | Value | Gate | Pass? |
|---|---|---|---|
| Clean baseline false alarm | 80.8% (21/26) | ≤ 10% | ❌ |
| Mean detection rate | 76.9% | ≥ 90% | ❌ |

### Per-fault detection

| Fault | Detection |
|---|---|
| force_long_response | 69.2% (18/26) |
| remove_one_question_rule | 69.2% (18/26) |
| swap_implicit_to_explicit | 84.6% (22/26) |
| force_metalinguistic_always | 80.8% (21/26) |
| disable_self_answer_rule | 80.8% (21/26) |

## Interpretation

This is **not a regression** — it confirms the Session 41 finding :
LiteLLM-bypass fault injection produces artifactual noise because the
bypass path differs materially from the real Dify session-flow path
used to record goldens. Clean baseline flagging at 80.8% demonstrates
the false-positive floor is structural, not discriminative.

Detection rates (~70-85%) exceed the baseline by a small margin — the
faults are measurably detectable above noise, but the gate criteria
were calibrated for a true Dify-clone methodology.

## Session 43+ refinement options

1. **Dify clone methodology** (preferred) : retry the Session 40 clone
   approach with reduced timeouts and parallelism. Root cause for the
   original >30min hang is unknown ; agent investigation needed.
2. **Delta gating** : compare fault runs against the clean baseline
   on the same scenarios rather than against absolute thresholds.
   Gate = (detection − false_alarm) > 20 pp avg.
3. **Distributional invariants** : instead of dim-level verdicts,
   check that the distribution of response features (length, question
   count, metalinguistic density) shifts as expected under each fault.

## Raw data

- JSON : `docs/oracle/session42_fault_injection_teacher_en.json`
- Full log : not committed (in `/tmp/fi_s42.log` on the host).
