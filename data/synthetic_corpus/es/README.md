# Spanish synthetic corpus — Wave 1 archive

**Not used for production fine-tune.** Kept as reference + for comparison when we re-fit from real `error_log` data post-alpha.

## Context

Wave 1 decision (2026-04-20) : **skip fine-tune for Maestro ES v1 launch**. Quality spot-check of generated synthetic corpus revealed ~50% label noise, concentrated in pragmatic/register/stylistic codes (B2-C2). Mechanical codes (A1-A2) validated by `rules_es.py` post-filter had good quality.

Rather than train gpt-4o-mini on mixed-quality labels (risk teaching incorrect patterns on subtle B2-C2 errors), we use:
- base `gpt-4o-mini` via LiteLLM
- `fewshots/es.yaml` (14 handcrafted A1-C2 examples, high quality)
- `SYSTEM_PROMPT_ES` + `USER_PROMPT_TEMPLATE_ES` (40+ native ES codes)

Re-fit planned when ~500 real learner messages accumulate in `error_log` post-Maestro activation. That signal will be 10× cleaner than synthetic.

## Files

- `test_v1_a1_noisy.jsonl` — first run, original prompt (~20% hallucination rate)
- `test_v2_a1_filtered.jsonl` — second run, hardened prompt + post-filter (~33% rejection)
- `train_v1_noisy.jsonl` — full A1-C2 run, 453 kept / 619 generated (26.8% rejection)

## Known quality issues

### Per-descriptor kept rate from production run

| Descriptor family | Quality | Notes |
|---|---|---|
| Mechanical (rules_es validated) | 🟢 good | ORTH, PUNCT, ART:PROF, ASPECT:PERF, PRO_DROP |
| Morpho/lexical (no rules coverage) | 🟡 mixed | N:GEN, V:AUX_HABER, APOCOPE |
| Pragmatic/register | 🔴 noisy | PRAGMATIC:HEDGING ("Vale" flagged wrongly), CONNECT:DISCOURSE |
| Subjonctif complexe | 🔴 noisy | V:SUBJ:IMPERFECT, V:SUBJ:PLUSCUAMPERFECTO |
| Idioms | 🔴 noisy | LEX:IDIOM:OPAQUE, LEX:IDIOM:TRANSPARENT |

### Failure modes observed

1. LLM invents errors on correct sentences ("Me gusta mucho ese libro" labeled QUANT:MUY_MUCHO)
2. LLM inverts corrections ("muy → mucho" when opposite is correct)
3. LLM flags idiomatic native forms as errors ("Por así decirlo", "Vale")
4. LLM over-prescribes archaic alternatives ("pudiera → pudiese")

## Re-fit plan (post-alpha, ~3 months after Maestro launch)

1. Collect ≥500 real `error_log` entries ES via Maestro prod
2. Filter to LLM-scored high-confidence errors
3. Merge with `train_v1_noisy.jsonl` strong-code subset (~150 examples mechanical)
4. Fine-tune `ft:gpt-4o-mini-academie-errors-es-v2` (Latouche EMNLP 2024 two-stage)
5. Evaluate on battery hold-out + real persona tests
6. Activate via `ANALYSIS_MODEL_BY_LANG["es"] = "ft:...es-v2"`

Budget re-fit: ~$3-5 OpenAI (same as skipped Wave 1 fine-tune).

## Reference

- Session 31 (2026-04-20) decision — option C skip fine-tune
- ADR-012-security-remediation — unrelated but same session
- Agent 1 research (Bruhn de Garavito + Collentine + Montrul + Geeslin + Paquet) — drives descriptor definitions in `data/synthetic_descriptors/es.yaml`
- Latouche EMNLP 2024 two-stage synthetic pipeline reference
