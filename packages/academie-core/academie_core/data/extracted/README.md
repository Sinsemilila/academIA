# Extracted knowledge — structured data from canonical books

Pattern : extract code-injectable knowledge from canonical pedagogy/SLA books into structured YAML files, consumable directly by `rules.py`, `tolerance_matrix`, `fewshots`, `dosage_block`, `mini_exam` builders.

**Counterpart vault** : `vault/knowledge/books/<slug>.md` = humain-readable literature note. **This folder** = code-readable structured data.

## Layout

```
extracted/
├── README.md                           ← this file
├── _schemas/                           ← JSON Schema validation for each extraction type
│   ├── cf-taxonomy.schema.yaml
│   ├── acquisition-stages.schema.yaml
│   ├── cefr-can-do.schema.yaml
│   └── ...
├── lyster-2007/                        ← per-book sub-dir (slug = same as vault literature note)
│   ├── cf-taxonomy.yaml
│   └── counterbalanced-principle.yaml
├── pienemann-2005/
│   ├── german-acquisition-stages.yaml
│   ├── spanish-subjunctive-stages.yaml
│   └── teachability-principle.yaml
├── lightbown-spada-2021/
│   ├── ch5-cf-observation-schemes.yaml
│   └── ch6-six-proposals-decision-tree.yaml
├── profile-deutsch/
│   └── b1-can-do-statements.yaml
├── cils-sillabo/
│   └── it-grammar-by-level.yaml
└── ...
```

## When to extract

**Lazy + triggered by code work**, not anticipated batch.

Triggers :
- Implementing `rules_<lang>.py` for new language → extract relevant chapters from per-language anchor (CILS for IT, Profile Deutsch for DE, JLPT for JP, TORFL for RU)
- Designing new judge prompt or rubric → extract Lyster CF taxonomy or Lightbown/Spada CF observation schemes
- Curating fewshots for new CEFR×move cell → extract Lyster recast/prompt CEFR appropriateness mapping
- Building `mini_exam_<lang>.yaml` → extract grammar items from official exam materials (CILS, JLPT 公式問題集, TORFL)
- Tier 2 BIPED architecture → extract Pienemann teachability stages per language

**Not** triggered :
- Casual reading, exploration — that goes in vault literature note free-form
- Reference grammar lookup — keep PDF on hand, lookup, don't extract entire grammar to YAML
- Frequency dictionaries — already structured data elsewhere (Sketch Engine, Wiktionary frequency lists)

## Extraction principle

**Telegraph YAML, citation-anchored.**

Each entry MUST include :
- `source` : `"<book-slug>, ch X, pp. Y-Z"` for traceability + future audit
- `extracted_by` : `claude` or `sinse_manual`
- `extracted_date` : `YYYY-MM-DD`
- `confidence` : `high | medium | low` (high = direct quote/table parse, medium = paraphrase, low = inferred)

## Example — CF taxonomy from Lyster 2007

```yaml
# extracted/lyster-2007/cf-taxonomy.yaml
source_book: "lyster-2007-counterbalanced"
extracted_by: claude
extracted_date: 2026-05-XX
schema_version: 1
schema_ref: "_schemas/cf-taxonomy.schema.yaml"

cf_moves:
  - id: explicit_correction
    definition: "Teacher provides correct form and clearly indicates the learner's utterance was incorrect."
    cefr_appropriateness:
      a1: high     # absolute beginners benefit from explicit
      a2: high
      b1: medium
      b2: low      # autonomy-blocking at B2+
      c1: low
      c2: low
    counter_indications:
      - "implicit feedback usually preferred when learner is at uptake stage"
    source: "Lyster 2007, ch 4, pp. 89-95"
    confidence: high

  - id: implicit_recast
    definition: "Teacher reformulates the learner's utterance, removing the error, without explicit indication."
    cefr_appropriateness:
      a1: medium   # recast often missed by absolute beginners
      a2: high
      b1: high
      b2: high
      c1: medium   # less effective at advanced (already noticed)
      c2: low
    co_occurrence_warning:
      - "with elicitation in prompt sequences (Lyster & Saito 2010)"
    source: "Lyster 2007, ch 4, pp. 96-105"
    confidence: high

  # ... etc
```

## Loader integration

Extracted YAMLs are loaded by `academie_core/data/loader.py` helpers (or new helper to be added in `loader.py` when first consumer lands). Pattern :

```python
@lru_cache(maxsize=32)
def load_extracted(book_slug: str, extraction_name: str) -> dict | None:
    """Load extracted knowledge YAML. Returns None if not yet extracted."""
    path = _DATA_DIR / "extracted" / book_slug / f"{extraction_name}.yaml"
    if not path.exists():
        return None
    with open(path) as f:
        return yaml.safe_load(f)
```

Consumers (rules, tolerance_matrix builder, fewshot generator, judge prompt builder) call `load_extracted("lyster-2007", "cf-taxonomy")` and use the structured data.

## Versioning + audit

- Each extraction file is git-versioned. Updates = new commit `[chore] extracted/<slug> — <description>`.
- Frontmatter `schema_version` allows breaking-change migrations (loaders branch on version).
- Annual audit (cohérent vault L116 audit 3 mois pattern) : check which extractions have actually been consumed by code (grep for `load_extracted("<slug>"`) — if never consumed in 6+ months, candidate for removal.

## See also

- ADR-014 : knowledge extraction pattern decision (`/opt/academia/docs/05-decisions/ADR-014-structured-knowledge-extraction.md`)
- Vault literature notes : `/root/sinse-vault/knowledge/books/`
- Slash command ingestion : `~/.claude/commands/library-ingest.md`
