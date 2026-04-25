---
title: Corpus Oracle V1 — Regression Testing Harness for Conversational Pedagogy
status: shipped-v1-alpha-2026-04-23
owner: Sinse
last_reviewed: 2026-04-23
author: Claude (Session 38 handoff, multi-agent critique ML evals + SLA pedagogy)
supersedes: none
shipped_commits:
  - main:0c0e336..b5d7181 (Session 40 Phases 0, A, B1, B2, C, D infra, E)
---

# Corpus Oracle V1 — Regression Testing Harness

> **TL;DR** — An automated regression harness that validates LLM prompt changes don't silently regress the tutor's pedagogical behavior. Built around snapshot-as-oracle (not aspirational), cross-vendor LLM judge (Claude Haiku), pairwise scoring against golden responses from a frozen prod SHA, 3-axis aggregation, stratified 24-scenario corpus seeded 60% from real `error_log` + 40% handcrafted for coverage. V1 scope is **Teacher EN only**, ~1 day dev budget. This is the foundational tool that unblocks Phase C-deep prompt refactor, Wave 2+ multilang, and any ambitious pedagogical feature change.

## 1. Problem statement

AcademIA runs on prompt-engineered LLMs (Dify workflows). We make frequent prompt changes (Session 37-38 livered 3 mutations). Code-level tests (`RUN_RECENT_BATTERY.sh`, 285 pytest, E2E) confirm the pipelines don't crash but **don't measure pedagogical quality drift** when prompts are edited.

Memory project `project_no_native_reviewers.md` acté : zéro reviewer humain C2 pour ES/IT/DE/JP/RU. Validation stratégie = corpus oracle + LLM consensus + télémétrie alpha. **This doc designs the first leg.**

## 2. Philosophy — regression snapshot, not evaluation

The single most important framing decision : **the oracle is a regression detector, not a pedagogical truth-teller**. Golden responses are produced by the *current prod bot on a frozen commit* (snapshot), not handwritten by Sinse as "ideal".

Implication : the oracle answers *"is behavior stable vs. ref SHA ?"*, not *"is this pedagogically optimal ?"*. This is what we actually want for regression CI.

**Exception** : a small set of scenarios marked `aspirational: true` can encode aspirations beyond current prod behavior, but they are tracked separately and **do not gate** release. Progress tracker, not regression tracker.

## 3. Scope V1

- **Single agent** : Teacher EN (`app_id = 39565197-...`)
- **Scenarios** : **24 total**, stratified :
  - 4 from `error_log` (A1-T2 real FR-learner errors — all the distributional realism `error_log` actually provides today, see §3a)
  - 16 handcrafted covering CEFR × tier cells absent from error_log
  - 4 multi-turn (turn-1 error → turn-2 uptake check)
- **Dimensions** : 5 (see §5), each scored against golden
- **Judge** : gpt-4o-mini via LiteLLM proxy (self-vendor V1, see §3b)
- **Execution** : CLI with tiered modes (`--mode lint|smoke|full`, see §3c)
- **Budget** : ~1 day solo dev (Session 40)

## 3a. Phase 0 pre-flight findings (2026-04-23)

SQL census revealed the original plan of "12 from error_log stratified across 3 CEFR × 2 tier × 2 FLA" is **not feasible today** :
- Total EN error_log rows : 160
- T2 : 18 / T3 : 1 / all at niveau_global=A1
- Distribution is too concentrated for stratified 12-cell sampling

Pivot retained : use the 4 most informative A1-T2 error_log rows + author 16 handcrafted scenarios covering A2/B1/B2 × T2/T3 cells. Handcrafted dominance is acceptable for V1 because :
- Handcrafted scenarios can be explicit about expected dimensions
- error_log realism matters more as corpus grows ; V1 is a harness, not a corpus release
- Future sessions can re-seed from error_log once traffic accumulates (target : 300+ rows per CEFR band before re-doing this census)

Dify public API + `clone_app.py` both validated working during pre-flight.

## 3b. Self-vendor judge caveat (V1 only)

Claude Haiku (the design's original cross-vendor judge) requires an Anthropic API key not currently configured in `litellm/config.yaml`. V1 ships with **gpt-4o-mini** as judge — same model family as the bot.

**Why this is acceptable for regression testing** : the bias addressed by cross-vendor judges (AlpacaEval 2, MT-Bench) is self-preference when comparing responses across model families. V1 setup compares two same-family responses (current bot vs frozen-SHA bot) — there is no "team A vs team B" asymmetry for the judge to exploit. Pairwise prompting + N=3 majority + empirical fault-injection gate (§9.2) provide the validation.

V2 upgrade path : swap `scripts/oracle/config.yaml::judge_model` to `groq-standard` (Llama 3.3 70B, cross-vendor, free) or `claude-haiku-4-5` (requires Anthropic key). 30 min change, no code refactor.

## 3c. Tiered trigger modes (V1 ship requirement)

Full run costs ~108K tokens (24 scenarios × 3 LLM dims × N=3 judges) = ~7% of daily 1.5M quota. Running on every `RUN_RECENT_BATTERY.sh` invocation would burn quota. Oracle ships with 3 modes :

| Mode | Tokens | Trigger |
|---|---|---|
| `--mode lint` | ~0 | `RUN_RECENT_BATTERY.sh` block 8 (every run) |
| `--mode smoke` | ~9K | optional cron nightly 03:00, or on commits touching `workflows.graph` |
| `--mode full` | ~108K | on-demand manual only, reserved for major prompt change validation |

Phase C calibration (noise floor ×5) + Phase D fault injection (5 faults) = ~1.08M tokens one-shot during Session 40 — peak ponctuel, done during low-traffic window.

## 4. Scenario schema

Each scenario is a YAML file under `scripts/oracle/scenarios/teacher_en/`:

```yaml
# scripts/oracle/scenarios/teacher_en/a1_t2_verbtense_lowfla.yaml
id: a1_t2_verbtense_lowfla_001
source: handcrafted        # or: error_log_row_{id} with archive date
scenario_key:
  agent: teacher_en
  cefr: A1
  target_tier: T2
  error_category: verb_tense
  fla: low                  # low | mid | high — impacts expected CF set
  style_profile: direct     # matches profils_eleves.style
multi_turn: false
turns:
  - role: learner
    text: "yesterday I go to school and I eat pizza"
    expected_errors: ["V:TENSE", "V:TENSE"]
expected_dimensions:
  # Each dimension has {mode, assertion}
  cf_move_set_valid:
    mode: set_membership
    acceptable: [full_recast, partial_recast, clarification_request]
    forbidden: [metalinguistic, explicit_correction]  # banned at A1 + low FLA
  scaffolding_flags_honored:
    mode: all_required
    flags: [sandwich_optional, reassurance_off, no_explicit_correction_low_prio]
    l2_ratio_band: [0.85, 0.95]
  register_cefr_alignment:
    mode: within_sublevel
    target: A1
    tolerance: 1             # ±1 sublevel accepted
  recast_saliency_and_dosage:
    mode: structural
    max_lines: 5
    max_questions: 1
    error_form_isolated: true  # corrected form in its own phrase or stressed
    mini_lesson_allowed: false
  semantic_fidelity_pairwise:
    mode: llm_pairwise
    vs_golden: true
    min_score: 4              # ≥ 4/5
golden:
  sha: dcd7110             # prompt SHA used to record golden
  recorded_at: 2026-04-23T09:15:00Z
  response: |
    Ah, you went to school yesterday! And what kind of pizza did you eat?
```

## 5. Dimensions (the 5 that matter)

Derived from SLA pedagogy critique + ML evals aggregation. **Dropped** the original 10 dims ; kept only what's pedagogically load-bearing AND non-redundant.

### 5.1 `cf_move_set_valid` (Lyster 7-move taxonomy)

Check that the bot's corrective feedback move is in the **acceptable set** for `(CEFR, tier, category, FLA)` and **not in forbidden set**.

Lyster 7 moves : `explicit_correction | full_recast | partial_recast | clarification_request | metalinguistic | elicitation | repetition`

Mode : **LLM classifier** with narrow prompt ("which move did the bot use ?") + set membership check.

**Critical enrichment vs original design** : expected value is a **set** because multiple moves can be valid for the same error. And FLA is in the scenario key because Sheen 2008 says high-FLA + metalinguistic = regression.

### 5.2 `scaffolding_flags_honored` (policy vector, not L2 scalar)

Replaces original `L2_ratio` scalar. Check **each active flag** from `scaffolding_policy.resolve_policy(CEFR, distance, FLA, ...)` :
- `sandwich_applied` (bool) — Butzkamm L2→L1→L2 pattern present when policy says `sandwich=true`
- `reassurance_present` (bool) — L1 affective reassurance when `reassurance_l1=true`
- `no_explicit_correction_honored` (bool) — zero "the correct form is…" patterns when flag is on
- `l2_ratio_in_band` (bool) — L2 word ratio within ±10pp of target
- `l1_function_tags_valid` (set ⊆ {meta, gloss, reassurance, none}) — L1 used appropriately

Mode : **mix deterministic** (regex L2/L1 word count, policy lookup) + **LLM classifier** (L1 function tagging).

### 5.3 `register_cefr_alignment` (catch over/under-challenge)

Bot's own turn's apparent CEFR level classified independently, assert within ±1 sublevel of the learner's CEFR. Catches both :
- Over-challenge : bot at B2 register when learner is A1
- Under-challenge : bot infantilizing B1 learner with A1 phrasing

Mode : **LLM judge** (CEFR-SP-style classifier, or narrow Haiku prompt with CEFR descriptors).

### 5.4 `recast_saliency_and_dosage`

Structural constraints + uptake proxy :
- `max_lines` (typically 5, 8 if micro-lesson triggered)
- `max_questions` (1 per turn)
- `error_form_isolated` (bool) — corrected form stressed/contrastive, not buried mid-sentence. This is the **uptake proxy** (surrogate for Lyster's actual "learner uptake" which requires multi-turn).
- `mini_lesson_allowed` (bool) — only `true` for 3-strikes trigger scenarios

Mode : **deterministic** (line count, `?` count) + **LLM judge** for `error_form_isolated`.

### 5.5 `semantic_fidelity_pairwise`

Overall response equivalent in meaning + pedagogical intent to the golden (frozen SHA reference).

Mode : **Claude Haiku pairwise** ("is response A pedagogically equivalent to response B for this scenario ?") → score 1-5. Min 4/5.

Pairwise > absolute : LLMs are notoriously uncalibrated on absolute 1-5, but stable on "is A ≥ B ?".

---

## 6. What's dropped from the original 10-dim design

| Original dim | Fate | Reason |
|---|---|---|
| `tier_correctness` | ABSORBED into `cf_move_set_valid` | CF move implies tier |
| `feedback_type` | ABSORBED into `cf_move_set_valid` | Same |
| `dosage` | ABSORBED into `recast_saliency_and_dosage` | Merge related |
| `L2_ratio` scalar | REPLACED by `scaffolding_flags_honored` vector | Scalar is lossy per SLA critique |
| `observed_level_emitted` | MOVED to **lint layer** | JSON schema check, not pedagogical |
| `anti_pattern_A1` | MOVED to **lint layer** | Simple regex blocklist |
| `priority_concepts_leak` | MOVED to **lint layer** | Simple string-match check |
| `tone_style` | ABSORBED into `semantic_fidelity_pairwise` | Hard to score, low signal |
| `question_invite` | ABSORBED into `recast_saliency_and_dosage` | Regex `\?$` is structural |
| `semantic_fidelity` | KEPT as `_pairwise` | Upgraded methodology |

**Lint layer** (separate from pedagogical oracle) : fast deterministic checks on every scenario for basic correctness (JSON valid, observed_level emitted, A1 jargon absent, priority list not leaked). If lint fails → immediate fail, don't bother scoring pedagogical dims.

## 7. Judge architecture

### 7.1 Model choice — cross-vendor

**Primary** : Claude Haiku 4.5 (not gpt-4.1-mini). Eliminates self-preference bias (the bot uses gpt-4o-mini ; judge must be different family).

**Consensus option** (optional, V2) : 2-of-3 jury = Haiku + Gemini Flash + gpt-4.1-mini, majority vote.

### 7.2 Pairwise, not absolute

Each LLM-judged dim : prompt the judge with *both* the bot response AND the golden reference, ask for pairwise comparison. This is 3-4× more reliable than absolute 1-5 scoring (AlpacaEval 2, MT-Bench literature).

### 7.3 Reproducibility

- Temperature = 0
- Fixed seed if API supports
- **N=3 runs per scenario**, majority vote for pass/fail, median for numeric
- **Noise floor measurement** on Day 1 : run the full oracle against unchanged prompt 5 times, compute expected false-positive rate per dim. If noise floor > 10% → that dim isn't production-ready, needs prompt refinement

## 8. Aggregation — 3 axes, not flat

Group 5 dimensions into 3 axes (following ML-evals critique §3) :

| Axis | Dimensions | What it catches |
|---|---|---|
| **Policy compliance** | `cf_move_set_valid`, `scaffolding_flags_honored` | Scaffolding regression, wrong CF move |
| **Output shape** | `recast_saliency_and_dosage`, lint layer | Broken dosage, missing fields, leaks |
| **Pedagogy quality** | `register_cefr_alignment`, `semantic_fidelity_pairwise` | Drift in overall pedagogical character |

**Scenario pass** : `min(axis_score)` ≥ 4/5 for all 3 axes.
**Release gate** : pass_rate ≥ (100% − noise_floor − 5pt tolerance). Set empirically after noise floor measurement.

Not "18/20 green" — that was arbitrary.

## 9. Calibration protocol (non-negotiable)

Before trusting the oracle in CI :

### 9.1 Manual calibration (Session 40 afternoon, ~2h)
- Sinse scores all 24 scenarios manually on the 5 dims
- Oracle scores the same 24 scenarios automated
- Compute **Cohen's kappa** (or simple agreement rate) per dim
- **Dim with κ < 0.6 → drop or rewrite prompt** before shipping

### 9.2 Fault injection (Session 40 afternoon, ~1h)
- Inject 5 known-bad prompts (remove priority_concepts directive, force metalinguistic at A1, swap tier mapping, force response length 20 lines, disable FLA scaffolding)
- Run oracle on each
- **Required detection rate** : ≥ 90% of injected faults flagged
- **Required false alarm rate** : ≤ 10% on unchanged prompt

If either fails → oracle isn't a gate, it's decoration. Fix before shipping.

### 9.3 Ongoing audit (post-ship)
- Every oracle-green commit gets tagged
- Quarterly : human sample 10% of dialogs for pedagogical quality rating, compute correlation with oracle verdict
- If correlation < 0.5 → oracle broken, re-calibrate

## 10. Data sources — scenarios

### 10.1 Error-log seeding (12 scenarios)
```sql
-- Pick diverse real learner turns
SELECT el.original_text, el.error_code, el.tier, pe.niveau_global, lp.domain_motivation
FROM error_log el
JOIN profils_eleves pe ON pe.eleve_id = el.eleve_id AND pe.domain = el.domain
LEFT JOIN learner_profiles lp ON lp.eleve_id = el.eleve_id AND lp.domain = el.domain
WHERE el.domain = 'en'
  AND el.tier IN ('T2', 'T3')
  AND pe.niveau_global IS NOT NULL
ORDER BY RANDOM()
LIMIT 50;
```
Then Sinse picks 12 stratified across CEFR (A1/A2/B1/B2/C1) × tier × 2 FLA bands.

### 10.2 Handcrafted (8 scenarios)
For coverage of :
- T2↔T3 boundary at B1 (highest-risk rubric zone per ML critique §6)
- High-risk failure : priority_concept leak attempt
- High-risk failure : A1 metalinguistic leak attempt
- High-risk failure : L1 drift during recast
- T4 regression (learner regresses on acquired A1 form)
- Tier override : gravity_communicative ≥ 0.7 + tier T1 upgrade
- Tier override : gravity_social ≥ 0.6 + tier T2 upgrade
- Style contrast : same error, direct vs encourageant profile

### 10.3 Multi-turn (4 scenarios)
Each multi-turn has 2 turns :
- Turn 1 : learner error → bot CF move
- Turn 2 : learner (scripted via persona-LLM) responds with OR without uptake
- Oracle checks bot's turn-2 follow-up appropriate (re-elicit if no uptake, progress if uptake)

V1 uses scripted turn-2 (no runtime learner simulator). V2 adds simulated learner.

## 11. Architecture

```
scripts/oracle/
├── scenarios/
│   └── teacher_en/
│       ├── a1_t2_verbtense_lowfla_001.yaml      # 12 error-log seeded
│       ├── a2_t3_articles_midfla_001.yaml
│       ├── ...
│       ├── edge_T2T3_boundary_B1_001.yaml       # 8 handcrafted
│       ├── ...
│       └── multi_a1_verb_followup_001.yaml      # 4 multi-turn
├── judges/
│   ├── deterministic.py         # line count, regex, JSON schema, policy lookup
│   └── llm_pairwise.py          # Claude Haiku pairwise judge
├── lint.py                      # fast deterministic pre-check (fail fast)
├── harness.py                   # scenario runner, N=3, aggregation
├── calibration.py               # Cohen's kappa vs Sinse manual scores
├── fault_injection.py           # 5 known-bad prompts, detection test
├── report.py                    # markdown + JSON output
└── config.yaml                  # judge model, thresholds, N

Usage :
  # Run full oracle
  python3 scripts/oracle/harness.py --agent teacher_en

  # Calibration (Session 40)
  python3 scripts/oracle/calibration.py --manual-scores /tmp/sinse_scores.yaml

  # Fault injection (Session 40)
  python3 scripts/oracle/fault_injection.py --agent teacher_en
```

Integration to `RUN_RECENT_BATTERY.sh` as block 8 (after smoke).

## 12. Corpus drift management

- Versioned : `scripts/oracle/scenarios/v1/teacher_en/`, `v2/`, etc.
- Every golden-response update = commit with reason code in message :
  - `doctrine_change` — legitimate pedagogical evolution (requires short ADR)
  - `bug_fix` — old golden was wrong (rare, document what was wrong)
  - `judge_recalibration` — threshold or prompt changed
  - `flake` — LLM determinism drift, re-record golden
- Quarterly review : if >30% of goldens churned, oracle isn't detecting regressions, it's rubber-stamping edits → re-design

## 13. Session 40 execution plan (hour-by-hour)

**09:00-09:15** Warm-up, re-read this doc.

**09:15-10:30 (1h15) — Block A : Harness skeleton + scenarios**
- `scenarios/` layout + 4 example YAML files (1 error-log + 1 handcrafted + 1 edge + 1 multi-turn stub)
- `harness.py` CLI runner
- `lint.py` deterministic pre-check

**10:30-10:45** Break.

**10:45-12:45 (2h) — Block B : Judge implementations**
- `deterministic.py` (5 dims where possible)
- `llm_pairwise.py` (Claude Haiku integration, N=3 majority vote)
- Fill remaining 20 scenarios (12 error-log via SQL pick + 7 handcrafted + 3 multi-turn-stub)
- First full run on unchanged prompt → record baseline

**12:45-13:30** Lunch hors écran.

**13:30-15:00 (1h30) — Block C : Noise floor + calibration**
- Run oracle 5× on unchanged prompt → compute noise floor per dim
- Sinse scores 24 scenarios manually in `/tmp/sinse_scores.yaml`
- `calibration.py` computes κ per dim → drop/rewrite dims with κ < 0.6

**15:00-15:15** Break.

**15:15-16:30 (1h15) — Block D : Fault injection validation**
- Inject 5 known-bad prompts via Dify workflow DSL
- Run oracle on each → measure detection rate
- Assert ≥ 90% detection, ≤ 10% false alarm
- If fails → iterate dim prompts until gates met

**16:30-17:30 (1h) — Block E : Integration + docs**
- Add oracle to `RUN_RECENT_BATTERY.sh` as block 8
- Update `docs/01-pedagogy/corpus-oracle-v1-design.md` with measured noise floor, κ, detection rates (flip `status: design-approved` → `status: shipped-v1`)
- Commit `scripts/oracle/` + docs + workspace updates

**17:30** HARD STOP. Session 41 extends to Maestro ES.

## 14. Out of V1 scope (defer to V2+)

- Maestro ES + per-language scenario packs (Session 41)
- Simulated learner LLM for multi-turn uptake (Session 42+)
- Hallucination factuality judge (grammar rule correctness)
- CEFR self-calibration judge (was the `observed_level` emission accurate ?)
- Ecological audit process (monthly learner panel, requires users)
- Latency/token budget regression (bolt-on, not dim)
- Cross-vendor 3-judge jury (current V1 uses Haiku single)
- Corpus expansion from archived prod sessions (pure handcrafted + error-log seeded in V1)

## 15. References

- Lyster & Ranta (1997) — 6 CF move taxonomy
- Sheen (2008), Rassaei (2023) — FLA × feedback interaction
- Panickssery et al. (2024) — LLM judge self-preference
- MT-Bench, AlpacaEval 2 — LLM-as-judge best practices
- TSCC (Caines et al. 2020) — reference corpus for CF move distributions
- CEFR-SP (Arase et al. 2022) — CEFR classifier usable for dim 5.3
- MemoryLab / Pavlik — adaptive scheduling literature (tangential)
- Internal : `docs/01-pedagogy/l1-l2-scaffolding-policy.md`, `docs/01-pedagogy/cefr-consolidation-policy.md`, `memory/project_no_native_reviewers.md`

## 16. Success criteria — Session 40 ship

- [x] All 5 dimensions defined and implementable
- [x] 24 scenarios authored (4 from error_log + 16 handcrafted + 4 multi-turn — pivot from original 12/8/4 split documented in §3a)
- [x] Pairwise judge integrated (gpt-4o-mini self-vendor, §3b caveat) ; Haiku upgrade is a 1-line config swap (V2)
- [x] Noise floor measured per dim (2 runs, §7 table below) — written to `scripts/oracle/config.yaml::noise_floor`
- [ ] **Deferred to Session 41** : Cohen's κ per LLM dim — requires Sinse manual scoring (`export_for_manual.py` + `calibration.py` ready)
- [ ] **Deferred to Session 41** : full 5-fault × 24-scenario detection rate — infrastructure shipped (`fault_injection.py`) + from_strs validated but live run deferred (est. 25-40 min wall time)
- [x] Integration to `RUN_RECENT_BATTERY.sh` working (block 8, lint-mode, strict gate)
- [x] Report format validated (markdown + JSON output from `harness.py`)
- [x] Documented in this file with partial calibration measurements

Status : **`shipped-v1-alpha`**. Oracle gates lint-layer regressions today ; full-mode gate activation depends on κ calibration + fault-injection detection rate completion in Session 41.

### §16a — Measured noise floor (Session 40, 2-run baseline)

| Dim | FPR |
|---|---|
| recast_saliency_and_dosage (det) | 0% |
| scaffolding_flags_honored (det) | 0% |
| cf_move_set_valid_partial (det) | 0% |
| scaffolding_flags_l2_ratio (det) | 12.5% |
| cf_move_set_valid (LLM) | 12.5% |
| register_cefr_alignment (LLM) | 20.8% |
| semantic_fidelity_pairwise (LLM) | 33.3% |

Higher FPR on `semantic_fidelity_pairwise` is expected : pairwise judgment on sibling responses from stochastic LLMs is intrinsically noisy. Mitigations : N=3 majority vote + pairwise (not absolute) prompting. Full-mode gate threshold will be `1 - (noise_floor + 5pt)` per dim after κ calibration flips some to DROP/KEEP.
