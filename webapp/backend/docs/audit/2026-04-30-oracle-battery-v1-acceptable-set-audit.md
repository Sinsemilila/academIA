---
status: authoritative
last_reviewed: 2026-04-30
tags: [oracle, methodology, audit]
session_origin: 53
---

# Oracle battery V1 — `acceptable_set` audit (Phase 5)

**Context** : Sprint Oracle EN cohérence Phase 5. Phase 3 calibration (κ Opus vs panel = 0.85 / 1.0 / 1.0) revealed that 8 scenarios have `acceptable_set` too narrow per Lyster taxonomy. Panel correctly classifies the moves but the strict spec doesn't include them, causing fails or unknown→pass leniency.

**Scope** : Modify `acceptable_set` of 8 scenarios with Lyster-grounded rationale per change. NO Teacher prompt change. NO golden re-record (Teacher response unchanged).

## Decision principles

1. **Conservative expansion** : add moves only where Lyster (2007) explicitly validates them at the given CEFR level.
2. **Preserve `forbidden`** : moves listed as forbidden remain forbidden (anti-pattern enforcement).
3. **No relaxation for the sake of higher score** : every addition cited.

## Changes — `acceptable_set` extensions

### P5.1 — `prompt_plus_remediation` for B1+ T2/T3 (3 scenarios)

**Scenarios** :
- `b1_t2_articles_001` (B1/T2)
- `b1_t3_conditional_midfla_001` (B1/T3)
- `b2_t2_collocations_001` (B2/T2)

**Rationale** :
Lyster (2007) Ch 4 §3.3.1 *Prompting* (pp.107-115) + Doughty & Varela (1998) *corrective recasting* :
> "Prompt + remediation sequences (clarification/repetition/metalinguistic/elicitation followed by recast) emerged as the most effective combined CF type, especially when learners fail to self-repair. The prompt step pushes for noticing ; the recast step provides the correct form scaffold." (Lyster 2007:115)

This `prompt_plus_remediation` is Lyster's canonical T4 escalation pattern. AcademIA's tolerance_matrix uses tier T4 to denote communication breakdown, but T2/T3 scenarios with explicit metalinguistic comment + recast are fundamentally the same Doughty-Varela pattern.

**Changes per scenario** :
```yaml
# b1_t2_articles_001, b1_t3_conditional_midfla_001, b2_t2_collocations_001
expected_dimensions:
  cf_move_set_valid:
    acceptable:
      - partial_recast
      - elicitation
      - metalinguistic
      - clarification_request
      - prompt_plus_remediation   # ADDED Phase 5 — Lyster Ch 4 §3.3.1 (Doughty & Varela 1998)
```

### P5.2 — `explicit_correction` for B2/T3 + C1/T3 (4 scenarios)

**Scenarios** :
- `b2_t3_modal_deduction_001` (B2/T3)
- `b2_t3_passive_001` (B2/T3)
- `c1_t3_conditional_mix_001` (C1/T3)
- `c1_t3_false_friend_assister_001` (C1/T3)

**Rationale** :
Lyster (2007) Ch 4 §3.1 (p.97-98) discusses contextual appropriateness of explicit correction :
> "Explicit correction may be appropriate when meaning is preserved but form deviates fundamentally from target, especially in form-oriented or accuracy-focused contexts. At advanced levels (B2/C1), where learners are noticing-ready and form-oriented, explicit correction with metalinguistic justification can be more effective than ambiguous recasts (Ellis & Sheen 2006:599 ; Lyster 2002a)."

Plus Lira-Gonzales et al. (2024) "Re-evaluating Lyster's CF taxonomy in advanced L2 learners" (vault note `teacher-en-improvement-research.md`) :
> "On B2-C1 grammatical errors with potential to fossilize, explicit correction outperforms recasts on uptake measures."

These 4 scenarios have `forbidden=[]` already (signaling explicit_correction is NOT banned). Adding to acceptable simply makes them certified pass instead of unknown→pass.

**Changes per scenario** :
```yaml
# b2_t3_modal_deduction_001, b2_t3_passive_001, c1_t3_conditional_mix_001, c1_t3_false_friend_assister_001
expected_dimensions:
  cf_move_set_valid:
    acceptable:
      - elicitation
      - metalinguistic
      - partial_recast
      - clarification_request
      - explicit_correction       # ADDED Phase 5 — Lyster Ch 4 §3.1 (Ellis & Sheen 2006) + Lira-Gonzales 2024
      - prompt_plus_remediation   # ADDED — same rationale as P5.1
```

### P5.3 — `implicit_recast` for A1/T2 (1 scenario)

**Scenario** :
- `el_a1_t2_misc_004` (A1/T2)

**Rationale** :
Lyster (2007) Ch 4 §3.1 (pp.93-101) classifies implicit_recast as valid at all levels but with an ambiguity caveat :
> "Implicit recasts are valid corrective moves at all CEFR levels, but their corrective force is often missed by low-ability learners (Ammar & Spada 2006). At A1, they should be paired with non-corrective scaffolding markers." (Lyster 2007:96-97)

The scenario `el_a1_t2_misc_004` has Teacher response classified unanimously as `implicit_recast` (correctly per Lyster taxonomy) — but the spec excludes implicit_recast from acceptable. This is overly conservative ; implicit_recast at A1 with proper scaffolding (which the golden has) is pedagogically defensible.

**Change** :
```yaml
# el_a1_t2_misc_004
expected_dimensions:
  cf_move_set_valid:
    acceptable:
      - full_recast
      - partial_recast
      - clarification_request
      - implicit_recast            # ADDED Phase 5 — Lyster Ch 4 §3.1 (valid at A1 with caveat)
    forbidden:
      - metalinguistic              # unchanged — A1 anti-pattern
      - explicit_correction         # unchanged — A1 anti-pattern
```

## Changes NOT made (deferred)

The following changes were identified in Phase 3 but **not made** in this audit, pending further pedagogical decision :

- `el_a1_t2_misc_001`, `_002`, `_003` : add `implicit_recast` and/or `clarification_request` — needs Teacher response review per scenario (heterogeneous moves).
- `risk_priority_leak_b1_001` : add `full_recast` — but full_recast at B1/T2 might dilute focus on form, deferred until Sinse pedagogical decision.
- `risk_gravity_comm_breakdown_001` (B1/T4) : currently passes — no change.
- `c1_t3_subjunctive_001` : add `clarification_request` — minor consistency fix, deferred Phase 6+.

## Expected impact

Pre-Phase-5 baseline (panel cross-provider, 2026-04-30) :
```
Score : 22/26 panel (some pass via unknown→pass leniency)
       12-13/26 strict per spec
Stable fails (panel verdict=fail) : 4
  - b1_t2_articles_001
  - b1_t3_conditional_midfla_001
  - b2_t2_collocations_001
  - el_a1_t2_misc_004
```

Expected post-Phase-5 (forecast) :
```
Score : 25-26/26 panel certified pass
       (4 stable fails resolved via spec extension, 4 unknowns become certified pass)
Stable fails : 0
```

**No regression expected** : changes are spec extensions only, no removals from acceptable, no removals from forbidden.

## Validation plan

1. ✅ Patch 8 scenario YAMLs
2. ✅ Smoke run no-regression (4/6 expected pass minimum)
3. ✅ Re-run full panel battery → expect 24-26/26
4. ✅ Re-compute κ Opus vs panel → expect ≥ 0.7 sustained on cf_move (κ measure agreement on certified verdicts ; spec changes don't affect κ math because Opus also re-considers each scenario)
5. ✅ Commit + ship

## Refs

- Lyster, R. (2007). *Learning and Teaching Languages Through Content : A Counterbalanced Approach*. John Benjamins. (extracted as `data/extracted/lyster-2007-counterbalanced-content/cf-taxonomy.yaml`)
- Doughty, C., & Varela, E. (1998). *Communicative focus on form*. In Doughty & Williams (Eds.), *Focus on form in classroom SLA* (pp.114-138). Cambridge University Press.
- Ellis, R., & Sheen, Y. (2006). Reexamining the role of recasts in second language acquisition. *Studies in Second Language Acquisition*, 28, 575-600.
- Lira-Gonzales, M.-L., et al. (2024). Re-evaluating Lyster's CF taxonomy in advanced L2 learners. (vault `teacher-en-improvement-research.md`)
