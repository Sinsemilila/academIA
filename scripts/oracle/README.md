# Corpus Oracle V1 — Regression testing harness

> **Status** : shipped-v1-alpha-2026-04-23. Lint-gate active in `RUN_RECENT_BATTERY.sh`. Full-mode + κ calibration + fault-injection validation available on-demand, not yet blocking CI.

Regression detector for the Dify Teacher EN tutoring bot. See design doc : [`docs/01-pedagogy/corpus-oracle-v1-design.md`](../../../sinse-workspace/projects/academie-ia/docs/01-pedagogy/corpus-oracle-v1-design.md) in the workspace repo.

## The 3 modes (tiered trigger)

| Mode | Cost | When to trigger |
|---|---|---|
| `--mode lint` | ~0 tokens | every `RUN_RECENT_BATTERY.sh` run (block 8) |
| `--mode smoke` | ~9K tokens | cron nightly OR on prompt-touching commits |
| `--mode full` | ~108K tokens (7% daily quota) | **on-demand only**, before major prompt changes |

Never run `--mode full` in a loop. It eats the OpenAI quota fast.

## Usage

```bash
# Lint only — fast, no LLM calls
python3 scripts/oracle/harness.py --agent teacher_en --mode lint

# Smoke — 6 high-signal scenarios, N=1 per dim
python3 scripts/oracle/harness.py --agent teacher_en --mode smoke

# Full — 24 scenarios × 3 LLM dims × N=3 majority
python3 scripts/oracle/harness.py --agent teacher_en --mode full
```

## Directory layout

```
scripts/oracle/
├── schemas.py              # pydantic v2 Scenario/Golden/DimVerdict models
├── lint.py                 # 4 deterministic structural checks
├── harness.py              # CLI runner — mode=lint|smoke|full
├── config.yaml             # judge model + thresholds + noise_floor
├── judges/
│   ├── deterministic.py    # recast_saliency + cf_move_partial + l2_ratio
│   ├── llm_pairwise.py     # cf_move + cefr_register + semantic_fidelity
│   └── dify_client.py      # calls Dify public API for live bot response
├── scenarios/teacher_en/   # 24 .yaml scenarios + golden/*.json snapshots
├── build_scenarios.py      # one-shot scenario generator (error_log SQL + handcrafted)
├── record_golden.py        # capture golden responses via Dify API
├── noise_floor.py          # K runs on unchanged prompt → FPR per dim
├── export_for_manual.py    # emit markdown template for Sinse manual scoring
├── calibration.py          # Cohen's κ vs Sinse manual scores
├── fault_injection.py      # 5 known-bad prompt patches → oracle detection gate
└── tests/                  # pytest — scenarios + deterministic judges
```

## Operational playbook

### Adding a new scenario

1. Drop a YAML in `scenarios/teacher_en/` following the schema in `schemas.py`.
2. Run `pytest scripts/oracle/tests/test_schemas.py` — must pass.
3. Record its golden : `python3 scripts/oracle/record_golden.py --only <id> --apply`.
4. Commit the YAML + golden together.

### Updating a golden (legit prompt evolution)

Golden updates = explicit commit with reason. Follow the taxonomy in design doc §12 :
- `doctrine_change` — legitimate pedagogical evolution (requires short ADR in `docs/01-pedagogy/`)
- `bug_fix` — old golden was wrong
- `judge_recalibration` — threshold or prompt changed
- `flake` — LLM determinism drift, re-record

### Running calibration (needs Sinse)

```bash
# 1. Produce the manual scoring template
python3 scripts/oracle/export_for_manual.py > /tmp/oracle_manual_scoring.md

# 2. Sinse fills verdicts in /tmp/oracle_sinse_scores.yaml (30-45 min)

# 3. Compute Cohen's κ vs oracle verdicts
python3 scripts/oracle/calibration.py \
  --manual /tmp/oracle_sinse_scores.yaml \
  --oracle /tmp/oracle_nf_run_1.json
```

Gates : κ ≥ 0.6 = KEEP, κ ∈ [0.4, 0.6) = BORDERLINE (alert Sinse), κ < 0.4 = DROP.

### Running fault injection (validation)

```bash
# 5 known-bad patches × 24 scenarios
python3 scripts/oracle/fault_injection.py --apply
```

Gates : ≥90% detection mean, ≤10% false alarm rate on clean baseline.

Uses LiteLLM bypass (not Dify clone) — calls gpt-4o-mini directly with the patched Teacher EN prompt + scenario learner turn. See fault_injection.py header comment for rationale.

## Current noise floor (Session 40)

Measured on 2 full runs of unchanged prompt :

| Dim | Noise floor (FPR) |
|---|---|
| recast_saliency_and_dosage | 0.0% |
| scaffolding_flags_honored | 0.0% |
| cf_move_set_valid_partial | 0.0% |
| scaffolding_flags_l2_ratio | 12.5% |
| cf_move_set_valid (LLM) | 12.5% |
| register_cefr_alignment (LLM) | 20.8% |
| semantic_fidelity_pairwise (LLM) | 33.3% |

Stored in `config.yaml::noise_floor`. Release gate threshold (when fully adopted) = `1 - (noise_floor + 0.05 tolerance)`.

## Self-vendor judge note

V1 ships with `gpt-4o-mini` as judge (same family as bot). Cross-vendor Haiku judge requires Anthropic API key, not configured. Pairwise-vs-golden setup minimizes self-preference risk. Swap to Groq Llama 3.3 70B or Claude Haiku by editing `config.yaml::judge.model` — no code change.
