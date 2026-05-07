---
name: academia-pedagogy
description: |
  Use when working on academia pedagogy — rubrics CEFR A1-C2, Lyster patterns (recasts/prompts/scaffolding moves), feedback delivery, scaffolding bibliography references.
  TRIGGER on: files in /opt/academia/data/rubrics/, /opt/academia/oracle/scenarios/, tasks mentioning "rubrics", "CEFR", "scaffolding", "Lyster", "recast", "feedback delivery", "pink-elephant".
  SKIP if: oracle harness implementation (use academia-oracle-harness), Dify mutations (use ecosystem-petit-pont-dify-workflows), or non-pedagogy refactor.
---

# Academia — Pedagogy patterns (CEFR + Lyster + scaffolding)

Source-of-truth conventions pédagogiques cross-langue (Teacher EN + Maestro ES + Wave 2-4 IT/DE/JP/RU). Cohérent vault knowledge `pedagogy-cefr-consolidation`, `feedback-delivery-pedagogy`, `sla-pedagogy-bibliography`.

## CEFR matrix reference architecture

| Level | Lexical scope | Grammar focus | Discourse | Feedback type |
|---|---|---|---|---|
| **A1** | 500-700 words HF | Present simple, basic Q | Single sentences | Recasts (high frequency) |
| **A2** | 1000-1500 words | Past forms, modals basic | Linked sentences | Recasts + targeted prompts |
| **B1** | 2500-3000 words | Complex past, conditionals | Paragraphs | Prompts (force noticing) |
| **B2** | 4000+ words | Subjunctive, complex passive | Multi-para discourse | Metalinguistic feedback |
| **C1** | 8000+ words | Idioms, register variation | Argumentative, rhetorical | Self-correction prompting |
| **C2** | 16000+ words | Native-like nuance | Native-level discourse | Peer-review style |

## Lyster scaffolding moves (Lyster 2007)

### 1. Recasts (most frequent A1-A2)

```
Learner: "I goed yesterday."
Teacher: "Oh, you went yesterday. Where did you go?"
                     ^^^^^ recast embedded in follow-up question
```

**Anti-pattern** : recast standalone (interrupts flow). Pattern correct = recast inside follow-up question forçant CEFR advance.

### 2. Prompts (B1-B2 transition)

```
Learner: "I want learn English."
Teacher: "I want... TO... what?"
                  ^^^^^^^^^^^^ prompt force learner self-correct
```

### 3. Metalinguistic feedback (B2-C1)

```
Learner: "If I would have known, I had gone."
Teacher: "Mixed conditional structure — what tense after 'if' for past hypothetical?"
                                    ^^^^^^^^^^^^^^^^^^^^^^^ explicit grammar prompt
```

### 4. Self-correction prompting (C1-C2)

```
Learner: "The committee's decision was unanimous regarding their disagreement."
Teacher: "Re-read your sentence. Anything contradictory?"
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ peer-review style
```

## Scaffolding bibliography (refs canoniques)

- **Lyster, R. (2007)** — *Learning and Teaching Languages Through Content* (recasts/prompts/scaffolding canonical taxonomy)
- **Doughty & Long (2003)** — *Handbook of Second Language Acquisition* (TBLT, focus on form vs meaning)
- **Lightbown & Spada (2013)** — *How Languages are Learned* (4th ed) — CEFR + age effects + interlanguage
- **Cervantes Institute (2006)** — *Plan curricular A1-A2 + B1-B2 + C1-C2* (ES reference, parity Wave 2 IT/PT)
- **Japan Foundation (2022)** — *JFS Guidebook EN* + 2010 *JFS Standard JP* (JP reference Wave 4)
- **Antonova (2009)** — *Doroga 1-2* RU elementary→basic (Wave 5)
- **Makova/Uskova (2020)** — *V Mire Lyudey* RU (advanced reference)
- **Zalyalova/Mullagalieva (2011)** — *Uprazhneniya RKI Part 2* RU exercises bank

Cf vault/knowledge/books/* (113 lit notes EN/ES/IT/DE/JP/RU + SLA + testing) pour notes détaillées.

## Pink-elephant anti-pattern (S55 Teacher EN P0 #3)

**Règle absolue** : rubrics directives écrites en **positive-only**. JAMAIS lister les phrases bannies dans le directive (le LLM les reproduit par "pink-elephant" reverse psychology).

### Bad patterns à éliminer (Teacher EN P0 #3, 7+ phrases bannies dans rubrics A1/A2/B1)

```yaml
# ❌ A1 rubric pre-fix
"feedback_a1": "NEVER say 'good job'. NEVER say 'well done'. AVOID generic praise like 'excellent' or 'perfect'."
```

```yaml
# ✅ A1 rubric post-fix (positive-only)
"feedback_a1": "ALWAYS recast inside a follow-up question that requires CEFR A1 lexical advance (HF 500-700 words). Embed grammar correction in the recast naturally."
```

### Cross-check workflow

Avant ship rubrics changes, dispatch :

```python
Agent(
    subagent_type="pedagogy-reviewer",
    description="Review rubric A1 EN positive-only compliance",
    prompt="""
    Review /opt/academia/data/rubrics/en.yaml lines 14-19 (A1 feedback rubric).
    Check :
    1. Positive-only construction (no NEVER/AVOID/DON'T patterns)
    2. CEFR A1 alignment (HF 500-700 words, basic grammar)
    3. Lyster recast embedded in follow-up question pattern
    4. Cross-language parity ES/IT/DE/JP/RU (refs same construction)
    Output : pass/fail + specific changes if fail.
    """
)
```

## RAG knowledge sources academia

```
data/
├── rubrics/<lang>.yaml             ← per-language CEFR rubrics
├── concept_hints/<lang>/<level>/   ← Dify Start node injected hints (CAREFUL max_length S55)
├── curriculum/<lang>/<level>/      ← progression curriculum reference
└── functions/<lang>/<level>/       ← functional acts (CEFR can-do statements)
```

Pour Wave 2-4 (IT/DE/JP/RU), avant build data layer per-langue, **dispatch vault-reader** + Explore en parallèle pour leverage les 113 lit notes vault (cohérent feedback_biblio_audit_per_lang memory).

## Gotchas pedagogy

### G1 — Author C2 separately (S55 Teacher EN P0 #4)

C2 scenarios doivent être **authored** (pas extrapolated A1-C1). C2 = native-like nuance + register variation, pas "harder C1".

### G2 — Cross-lang parity (Wave 2-4)

Reference Maestro ES architecture (S61 shipped) pour Wave 2 IT, pas Teacher EN (architecture older + different sequencing).

### G3 — L1 pollution detection per-lang

Cohérent oracle harness `per_lang_patterns.py` `l1_pollution_rgx`. Detect "in english" leak in Spanish/Italian/etc. responses.

### G4 — French scaffolding leak C1 prompt (Teacher EN P0.1 incident)

Bug : C1 system prompt EN avait fragment "en français..." leaked depuis early prototype. → judge marqué "L1 pollution" sur Teacher EN responses.

**Fix** : audit prompts cross-langue pour résidus L1 pollution.

## Cross-references

- [[academia-oracle-harness]] — battery validation patterns
- [[ecosystem-petit-pont-dify-workflows]] — Dify Teacher/Maestro mutations
- vault/knowledge/pedagogy/feedback-delivery-pedagogy.md
- vault/knowledge/pedagogy/sla-pedagogy-bibliography.md
- vault/knowledge/pedagogy/pedagogy-cefr-consolidation.md
- vault/projects/academia/knowledge/teacher-en-improvement-research.md
- vault/projects/academia/knowledge/multilang-{italian,german,japanese,russian}-research.md
