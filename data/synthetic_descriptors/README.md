# Synthetic descriptors — one YAML per target language

Feed for `scripts/synthetic/generate_errors.py`. Each descriptor tells
GPT-4o-mini what kind of error to generate (code, family, CEFR level,
linguistic description, optional hint).

## Schema

```yaml
descriptors:
  - code: "V:SER_ESTAR"              # our stable code, referenced by rules/llm
    family: "verb_usage"              # one of our 12 families
    level: "a2"                       # target CEFR level (a1..c2)
    description: "..."                # what the error looks like
    examples_hint: "..."              # optional; inspires variety
```

## Coverage status

| Lang | File | Status | Notes |
|---|---|---|---|
| ES | `es.yaml` | 🟢 Seed (8 descriptors) — extend at Wave 1 | Covers PCIC priorities |
| IT | `it.yaml` | 🟡 Placeholder — Wave 2 | Profilo della lingua references |
| DE | `de.yaml` | 🟡 Placeholder — Wave 2 | Profile Deutsch references |
| JP | `jp.yaml` | 🟢 Seed (7 descriptors) — extend at Wave 3 | **Critical path for JP** (no GLMM anchor) ; based on Polyglossia Oyama empirical distribution + Tanos/Bunpro lists |
| RU | `ru.yaml` | 🟡 Placeholder — Wave 4 | Gosstandart ТРКИ references |

## Level labels

Always use lowercase internal CEFR (`a1`, `a2`, `b1`, `b2`, `c1`, `c2`).
For JP/RU, JLPT/TORFL levels are translated via
`academie_core/levels.py:parse_user_level()`.
