# data/battery — Battery personas per lang

Each `{lang}_personas.yaml` defines 4 scripted personas (A1, A2, B1, B2)
with 10 learner-message turns each. Used by
`scripts/sprint3/eval_live_battery.py --lang {lang}`.

**EN exception** — does NOT live here. The EN baseline uses the in-code
dict `PERSONAS` in `scripts/sprint3/eval_personas.py` (Sprint 3 Phase 3
reference) to guarantee strict backward compatibility of regression runs.

## Schema

```yaml
personas:
  A1:
    level: "A1"
    profile: "<short description>"
    turns:
      - - "learner_message_text"
        - [{family: "noun_det", tier: "T3"}, ...]   # planted errors
      - ...  # 9 more turns
  A2:
    ...
  B1:
    ...
  B2:
    ...
```

Field notes :
- `level` ∈ {"A1","A2","B1","B2"} — string, upper-case (matches CEFR display)
- `profile` is informational, not used by assertions
- `turns` = list of 10 entries ; each entry is `[message_str, planted_errors]`
- planted `family` must match error-family values handled by the Teacher
  V2 output schema (see `pedagogy/teacher_prompt.py`)
- planted `tier` ∈ {"T1","T2","T3","T4"}

## Current status

| Lang | File | Status |
|---|---|---|
| EN | (in-code PERSONAS) | Production baseline, 99.4% pass rate |
| ES | `es_personas.yaml` | Template stub — to enrich at Wave 1 kickoff |
| IT | — | Wave 2 |
| DE | — | Wave 2 |
| JP | — | Wave 3 |
| RU | — | Wave 4 |
