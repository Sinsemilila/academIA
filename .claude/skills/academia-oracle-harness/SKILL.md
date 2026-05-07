---
name: academia-oracle-harness
description: |
  Use when working on academia oracle harness — battery validation, judge cascade, scenario tests, deterministic helpers per-language (EN/ES/IT/DE/JP/RU).
  TRIGGER on: files in /opt/academia/oracle/, tests/oracle/, tasks mentioning "oracle", "battery", "judge", "scenario", "kappa κ", "cohen calibration", "_scenario_lang", per-lang patterns.
  SKIP if: pure pedagogy review (use academia-pedagogy), Dify workflow patches (use ecosystem-petit-pont-dify-workflows), or non-academia projects.
---

# Academia — Oracle harness conventions

Pattern d'évaluation automatique academia (Teacher EN, Maestro ES, Wave 2-4 IT/DE/JP/RU) sans natifs reviewers (Sinse seul). Validation via corpus oracle + LLM judge consensus + télémétrie alpha.

## Architecture

```
oracle/
├── batteries/<lang>/
│   ├── a1/  (5-7 scenarios per CEFR level)
│   ├── a2/
│   ├── b1/
│   ├── b2/
│   ├── c1/
│   └── c2/  (futur)
├── judges/
│   ├── helpers/
│   │   ├── per_lang_patterns.py    ← S55 fix : per-lang dicts
│   │   └── lang_threading.py        ← _scenario_lang() detection
│   └── cascade.py                   ← gemini-flash → mistral-medium fallback
├── runners/
│   └── battery_runner.py            ← N=6+ samples per scenario
└── tests/
    └── conftest.py                  ← real DB, no mocks (Sinse policy)
```

## Patterns canonical

### Per-lang patterns dict (S55 fix Maestro ES)

```python
# oracle/judges/helpers/per_lang_patterns.py
PATTERN_DICT = {
    'en': {
        'accent_rgx': r'[^\x00-\x7F]',
        'l1_pollution_rgx': r'\b(en français|in french|sur la base de)\b',
        'scaffold_phrases': ['try saying', 'how about', 'consider'],
    },
    'es': {
        'accent_rgx': r'[áéíóúñü¿¡]',
        'l1_pollution_rgx': r'\b(in english|en anglais)\b',
        'scaffold_phrases': ['intenta decir', 'cómo sobre', 'considera'],
    },
    'it': {
        'accent_rgx': r'[àèéìòù]',
        'l1_pollution_rgx': r'\b(in english|in inglese)\b',
        'scaffold_phrases': ['prova a dire', 'come', 'considera'],
    },
    'de': {
        'accent_rgx': r'[äöüß]',
        'l1_pollution_rgx': r'\b(in english|auf englisch)\b',
        'scaffold_phrases': ['versuch zu sagen', 'wie wäre es', 'betrachte'],
    },
    'ja': {
        'accent_rgx': r'[぀-ゟ゠-ヿ一-龯]',  # hiragana/katakana/kanji
        'l1_pollution_rgx': r'\b(in english|英語で)\b',
        'scaffold_phrases': ['試して言ってみて', 'どうかな'],
    },
    'ru': {
        'accent_rgx': r'[Ѐ-ӿ]',  # Cyrillic
        'l1_pollution_rgx': r'\b(in english|по-английски)\b',
        'scaffold_phrases': ['попробуйте сказать', 'как насчет'],
    },
}

def get_patterns(scenario):
    lang = _scenario_lang(scenario)  # threading via scenario.scenario_key.agent
    return PATTERN_DICT.get(lang, PATTERN_DICT['en'])
```

### Lang threading via scenario_key.agent (S55 fix)

```python
# oracle/judges/helpers/lang_threading.py
AGENT_TO_LANG = {
    'teacher': 'en',
    'maestro': 'es',
    'professore': 'it',
    'lehrer': 'de',
    'sensei': 'ja',
    'profesor': 'ru',  # ou 'учитель' si décidé
}

def _scenario_lang(scenario):
    """Extract lang code from scenario.scenario_key.agent (Pydantic field accessor)."""
    agent = scenario.scenario_key.agent  # NOT scenario.scenario_key (S55 typo bug)
    return AGENT_TO_LANG.get(agent, 'en')
```

### Battery runner pattern (N≥6 samples per scenario)

```python
# oracle/runners/battery_runner.py
async def run_battery(lang: str, level: str, n_samples: int = 6):
    scenarios = load_scenarios(lang, level)
    results = []
    for scenario in scenarios:
        samples = []
        for _ in range(n_samples):
            response = await call_dify_app(scenario, lang)
            samples.append(response)
        kappa = compute_inter_judge_kappa(samples)
        results.append({
            "scenario_id": scenario.id,
            "samples": samples,
            "kappa": kappa,
            "passing": kappa >= 0.84,  # threshold S44 κ study
        })
    return results
```

### Judge cascade (gemini → mistral fallback)

```python
# oracle/judges/cascade.py
async def judge_response(text: str, scenario):
    try:
        return await judge_with_gemini_flash(text, scenario)  # primary κ=0.84
    except RateLimitError:
        try:
            return await judge_with_gemini_3_flash(text, scenario)  # fallback 1
        except Exception:
            return await judge_with_mistral_medium(text, scenario)  # fallback 2 (judge backup S53+)
```

## Gotchas connus (cf failures.md academia)

### G1 — scenario_key vs scenario_key.agent (Pydantic field accessor)

**Symptôme** : `_scenario_lang()` retourne 'en' partout, even pour Maestro ES.

**Cause** : code accéda `scenario.scenario_key` (object) au lieu de `scenario.scenario_key.agent` (string).

**Fix** : Pydantic strict mode catch via test mock — vérifier output `.agent` field accessor.

### G2 — Mock test diverge mock vs prod (S55 cross-lang)

**Symptôme** : oracle helpers passent test mock mais fail live Maestro ES.

**Cause** : mock test had `lang='en'` hardcoded, prod hit `_scenario_lang()` which threw.

**Fix** : tests intégration sur **real DB** + real scenarios (pas mock). Cohérent Sinse policy "no mocks for integration".

### G3 — Pink-elephant rubrics A1/A2 (S55 Teacher EN P0 #3)

**Pattern bug** : rubrics directives "ALWAYS recast inside follow-up question" mentionnent les phrases bannies dans les directives, ce qui pollute le judgment ("pink-elephant" reverse psychology).

**Fix obligatoire** : reformulation **positive-only** :
```yaml
# ❌ Bad
"NEVER say 'good job', NEVER say 'well done', NEVER use generic praise."

# ✅ Good
"ALWAYS recast learner production inside a follow-up question that requires CEFR-level lexical advance."
```

Cross-check via `pedagogy-reviewer` agent (existing custom).

### G4 — Few-shot wiring fragility

Cf `[[ecosystem-petit-pont-dify-workflows]]` G — judge classifies prose, pas labels enum.

## Test runners

```bash
# Battery single language single level
python -m oracle.runners.battery_runner --lang es --level a1 --samples 6

# Full Maestro ES battery (S61 baseline 19/24 = 79%)
python -m oracle.runners.battery_runner --lang es --all-levels

# Wave 2 IT (futur Phase 5)
python -m oracle.runners.battery_runner --lang it --level a1
```

## κ targets per level (S44 study)

| Level | Target κ | Acceptance |
|---|---|---|
| A1/A2 | ≥0.85 | Strict (high recall pink-elephant detection) |
| B1/B2 | ≥0.80 | Medium |
| C1/C2 | ≥0.75 | Lenient (judge ambiguity higher) |

## Scope status (S65)

- **EN Teacher** : 24 scenarios shipped, P0 #4 add 3 C2 scenarios (audit Phase 4)
- **ES Maestro** : 24 scenarios, baseline 19/24 = 79% pre-build floor (PIVOT measure-before-build S55)
- **IT Wave 2** : Phase 1 scoping post-Phase 4 audit Teacher EN (~5-7j)
- **DE/JP/RU** : Phase 5 Wave 2-4 sequential

## Cross-references

- [[academia-pedagogy]] — CEFR + Lyster + scaffolding patterns
- [[ecosystem-petit-pont-dify-workflows]] — Dify workflow gotchas
- vault/projects/academia/knowledge/oracle-harness-conventions.md (vault knowledge file)
- /opt/academia/docs/05-decisions/ADR-XXX-oracle-judge-cascade.md
- /opt/academia/oracle/README.md
