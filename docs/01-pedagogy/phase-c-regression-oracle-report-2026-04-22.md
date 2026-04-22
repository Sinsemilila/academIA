# Phase C reorder regression oracle — 2026-04-22 run

**Commit under review** : `dcd7110` ([perf] Session 38 prompt cache reorder, minimal intervention).
**Script** : `scripts/sprint6/17_oracle_phase_c_regression.py`.
**Run parameters** : `--sample 30 --judge-n 3` (15 Teacher EN + 15 Maestro ES, gpt-4o-mini majority vote).
**Raw results** : `/tmp/phase_c_oracle_report.json`.

## Raw gate output

| Metric | Value |
|---|---|
| Sampled messages | 30 |
| Judge-able | 30 |
| Majority-equivalent to current doctrine | 2 (6.7%) |
| Teacher EN | 0/15 (0%) |
| Maestro ES | 2/15 (13.3%) |
| **Gate** | **FAIL** (<60%) |

## Verdict : NOT a Phase C reorder regression

Manual review of divergent sample reasonings reveals the "failures" do not
indicate drift caused by `dcd7110`. They reflect the **evolution of the
doctrine itself** across Sessions 35-38, which post-dates most of the
pre-dcd7110 messages we sampled.

Representative divergence reasons (from the judge's own output) :

> "The tutor's response does not emit an observed_level CEFR field, which is
> required from turn 3 onwards"

> "The tutor's response does not apply any feedback tier, which is required
> by the doctrine"

> "Uses L1 for A1 learners, violating the doctrine"

None of these constraints **existed** in the prompt at the time those messages
were generated :
- `observed_level` field was introduced by script `06_strengthen_observed_level_v2.py`
  (Session 37 commit `6a7fa56`, 2026-04-21) — less than 24h before dcd7110.
- The L1-watch and FLA-policy enforcement landed in Session 35 (`15_strengthen_qcm_override_l2_example.py`).
- The T1-T4 tier schema was tightened progressively across Sprint 3 and Sessions 35-37.

The Phase C reorder (`dcd7110`) moved **stable vs. volatile chunks** within
the prompt for OpenAI cache-prefix stability. It did NOT change any doctrine
content. The 93% "divergent" rate measures the drift between old responses
(written under pre-Session-37 doctrine) and the current doctrine — orthogonal
to the question the oracle was designed to answer.

## Decision : no rollback, no prod action

- `rollback_phase_c.sh` NOT triggered.
- Phase D telemetry (Block 1.2) already shows the reorder delivering its
  intended outcome : cached_tokens 97% hit rate on stable prefix — empirical
  evidence that the reorder works AS INTENDED without evidence of quality drop.

## Follow-up : Oracle v2 design needed

The "unilateral LLM-judge against current doctrine" approach is methodologically
unfit for retroactive regression testing when the doctrine has evolved since
the snapshot period. Options for a future Session 40+ Oracle V1 (per existing
roadmap in TODO.md) :

1. **Doctrine versioning** : snapshot the doctrine summary at every commit that
   strengthens prompts, and ask the judge to compare against the doctrine
   version contemporaneous with the message. High implementation cost.
2. **Paired A/B** : only viable going forward — record prompts verbatim before
   each reorder so a bilateral compare is possible. Requires changing
   the reorder scripts to dump pre-reorder prompts FIRST.
3. **Distributional invariants** : measure aggregate shape (tier mix,
   observed_level presence rate, message length distribution) BEFORE vs AFTER
   each prompt change. Rate regression if the distribution shifts by >2σ.
   Much cheaper than per-message judging and immune to doctrine-evolution noise.

Recommended : option 3 for cheap ongoing monitoring + option 2 as standard
practice for all future prompt edits. Option 1 only if a specific incident
demands it.

## Filed as P1 follow-up

Entry added to `/root/sinse-workspace/projects/academie-ia/TODO.md` under
Session 40 scope — "Oracle V1 design must avoid the doctrine-drift trap".
