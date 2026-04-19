# sprint1/mappings — Source-schema → AcademIA taxonomy mappings

One YAML per source-lang pair. Each maps corpus-specific error tags to our
12-family taxonomy (`T1_ignored`/`T2_noted`/`T3_penalized`/`T4_regressive`
is applied downstream by `scoring.py` via `tolerance_matrix_v2_{lang}.yaml`).

## Contract

```yaml
mappings:
  "<source_tag>":
    academie_code: "<our code, free-form but stable>"
    family: "<one of our 12 families>"

unmappable:
  "<source_tag>":
    reason: "<why this tag can't be mapped>"

academie_codes_no_source:
  # Codes in our taxonomy that the source corpus cannot provide a signal for.
  # Their weights stay at priors until a dedicated annotation layer appears.
  <family>:
    - "<code>"
```

## Files

| File | Status |
|---|---|
| `errant_to_academie_en.yaml` | ✅ Production (copy of the legacy root-level file) |
| `cows_to_academie_es.yaml` | 🟡 Stub — Wave 1 ES |
| `merlin_to_academie_it.yaml` | 🟡 Stub — Wave 2 IT |
| `merlin_to_academie_de.yaml` | 🟡 Stub — Wave 2 DE |
| `falko_to_academie_de.yaml` | 🟡 Stub — Wave 2 DE |
| `rlc_to_academie_ru.yaml` | 🟡 Stub — Wave 4 RU |

Note : the legacy file `scripts/sprint1/errant_to_academie.yaml` is kept
untouched to avoid breaking the working EN pipeline
(`02_normalize.py` reads it by relative path).
