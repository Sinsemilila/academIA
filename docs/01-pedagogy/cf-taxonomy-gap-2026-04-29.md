---
title: CF taxonomy gap analysis — codebase vs Lyster (2007) extracted
status: draft
last_reviewed: 2026-04-29
author: claude
context: "Layer 1.5 first concrete extraction Lyster 2007 → cf-taxonomy.yaml révèle incohérence inter-modules sur les enum cf_move dans le codebase. Document supporte décision Tier 2 BIPED design (P1 mai)."
---

# CF taxonomy gap analysis — état codebase vs Lyster 2007 extracted

**Trigger** : extraction structurée Lyster (2007) Ch 4-5 → `data/extracted/lyster-2007-counterbalanced-content/cf-taxonomy.yaml` (10 cf_moves canonical Lyster taxonomy). Audit cohérence sur le codebase actuel révèle **3 taxonomies différentes** coexistant.

## État actuel : 3 taxonomies cf_move coexistantes

### 1. Schema canonical (extracted Lyster) — 10 enum values

Source : `data/extracted/_schemas/cf-taxonomy.schema.yaml` + `data/extracted/lyster-2007-counterbalanced-content/cf-taxonomy.yaml`

```
implicit_recast | explicit_recast | full_recast | partial_recast |
explicit_correction | clarification_request | repetition |
metalinguistic_feedback | elicitation | prompt_plus_remediation
```

### 2. Judge LLM (oracle Tier 1) — 7 enum values

Source : `scripts/oracle/judges/llm_pairwise.py:CF_MOVES`

```
full_recast | partial_recast | clarification_request | metalinguistic |
elicitation | repetition | explicit_correction
```

**Différences vs schema** :
- ❌ `implicit_recast` MANQUE (les implicit/explicit recasts sont conflated en full/partial recast → distinction Doughty/Varela 1998 perdue)
- ❌ `explicit_recast` MANQUE
- ❌ `prompt_plus_remediation` MANQUE (T4 escalation, utilisée explicitement dans rubric B2-C1)
- ⚠️ `metalinguistic` (short) vs schema `metalinguistic_feedback` (long) — naming mismatch

### 3. Fewshots / Teacher rubrics — 5+1 valeurs implicites

Source : `data/fewshots/en.yaml` + `data/rubrics/en.yaml`

```
implicit_recast | elicitation | metalinguistic | prompt_plus_remediation | silent
+ explicit_correction (anti-patterns wrong_type)
```

**Différences vs schema** :
- ✅ `implicit_recast` présent
- ✅ `prompt_plus_remediation` présent
- ➕ **`silent` ADDED** (= no CF, valid policy choice — pas dans Lyster taxonomy car Lyster classify CF moves only, pas absence-of-CF)
- ❌ `full_recast`, `partial_recast`, `explicit_recast`, `clarification_request`, `repetition` MANQUENT (sous-couvertes)
- ⚠️ `metalinguistic` (short) — same naming mismatch

## Tableau cohérence cross-module

| cf_move | Schema (extracted) | Judge | Fewshots/Rubric | Status |
|---|---|---|---|---|
| `silent` | ❌ absent | ❌ | ✅ | **Add to schema** (valid policy) |
| `implicit_recast` | ✅ | ❌ (conflated) | ✅ | **Add to judge** |
| `explicit_recast` | ✅ | ❌ (conflated) | ❌ | **Schema-only** until needed |
| `full_recast` | ✅ | ✅ | ❌ (implicit usage) | OK |
| `partial_recast` | ✅ | ✅ | ❌ (implicit usage) | OK |
| `clarification_request` | ✅ | ✅ | ❌ | Less used in rubrics |
| `repetition` | ✅ | ✅ | ❌ | Less used in rubrics |
| `metalinguistic_feedback` | ✅ | ⚠️ (`metalinguistic`) | ⚠️ (`metalinguistic`) | **Naming reconcile** |
| `elicitation` | ✅ | ✅ | ✅ | OK |
| `prompt_plus_remediation` | ✅ | ❌ | ✅ | **Add to judge** |
| `explicit_correction` | ✅ | ✅ | ⚠️ (anti-pattern only) | OK |

## Implications Tier 2 BIPED design

### Architecture proposée BIPED step 1 (CF classifier)

**Enum = 10 classes** (Lyster canonical + `silent`) :

```python
CF_MOVES_BIPED = [
    "silent",
    "implicit_recast",
    "explicit_recast",   # rare but distinct from implicit per Doughty/Varela 1998
    "full_recast",
    "partial_recast",
    "clarification_request",
    "repetition",
    "metalinguistic",     # short form — RECONCILE schema rename
    "elicitation",
    "prompt_plus_remediation",
    "explicit_correction",  # contraindicated A1-B1, allowed C1-C2 stylistic
]
```

= **11 classes** total (incluant silent + explicit_correction) — match cf-taxonomy.yaml 10 + silent addition.

### Décisions à acter

1. **Schema rename `metalinguistic_feedback` → `metalinguistic`** pour aligner avec fewshots+rubrics convention codebase. Edit `cf-taxonomy.schema.yaml` enum + re-run extracted Lyster cf-taxonomy.yaml field. **Effort : ~10 min**.

2. **Schema add `silent` enum value** + add field `is_cf: bool` (true for cf_moves, false for silent). Update extracted Lyster YAML pour clarifier que `silent` = absence-de-CF policy decision. **Effort : ~15 min**.

3. **Judge upgrade vers 11-class enum** (cohérent BIPED step 1) :
   - Change `CF_MOVES` constant `scripts/oracle/judges/llm_pairwise.py`
   - Update `CF_MOVE_PROMPT` to describe 11 classes
   - **Risk** : 11-class problem = plus de variance vs 7-class (Lyster reports judge agreement decreases with more classes)
   - **Mitigation** : asymmetric threshold déjà en place (Session 51 P0.2) absorbe variance partielle
   - **Effort : ~30 min code change + 1 battery RPD pour validate** (390 RPD)

4. **BIPED Step 1 prompt ingests cf-taxonomy.yaml** au runtime via `load_extracted("lyster-2007-counterbalanced-content", "cf-taxonomy")` :
   - Pour chaque cf_move : inject `definition` + `cefr_appropriateness[level]` + `counter_indications`
   - Step 1 output = cf_move ID enum (1 of 11)
   - Step 2 = response generator conditioned on (cf_move chosen + learner input + scaffolding context)
   - **Effort : ~3-5j BIPED design + impl**

### Décisions ouvertes Sinse review

**Q1** : `silent` traité comme cf_move enum value (11-class) OU comme orthogonal flag `cf_active: bool` qui gate la 10-class enum ?
- Option A (11-class enum incluant silent) — simpler, BIPED step 1 unique decision
- Option B (cf_active gate + 10-class enum) — cleaner conceptually mais 2-step decision

→ Recommendation : **Option A** (simpler, mirror Lightbown's "no feedback" as observable category)

**Q2** : Update judge maintenant (avant BIPED) ou après BIPED stable ?
- **Now** : judge classification cohérent avec rubric+fewshots immédiatement (élimine variance source partielle)
- **After BIPED** : minimize moving parts during BIPED design phase

→ Recommendation : **Now** (cohérence immédiate, BIPED design plus simple avec judge déjà aligned)

**Q3** : `explicit_recast` vs `full_recast`+`partial_recast` — vraiment besoin distinct or can merge ?
- Lyster traite explicit_recast comme variant (recast + stress/reduction) — empirically distinct effect (Doughty/Varela 1998)
- En français-immersion observation Lyster, explicit_recast = pratiquement pas observé (94-98% des recasts = implicit)
- Pour AcademIA EN target, explicit_recast pourrait être encouraged at A2-B1 (vs plus risque ignored)

→ Recommendation : **Keep distinct** dans schema, BIPED step 1 peut classifier — fewshots peuvent commencer sans explicit_recast (simplifier curation initiale)

## Roadmap concret pre-BIPED

| # | Action | Effort | Dépendance |
|---|---|---|---|
| 1 | Schema rename `metalinguistic_feedback` → `metalinguistic` + add `silent` | 15 min | none |
| 2 | Update extracted Lyster cf-taxonomy.yaml (rename + add silent if applicable) | 5 min | #1 |
| 3 | Update `judge.py:CF_MOVES` to 11-class | 20 min | none (parallel #1-2) |
| 4 | Validate cohérence : grep cf_move strings cross-codebase | 10 min | #1-3 |
| 5 | RPD test : 1 battery EN n=5 to confirm judge 11-class doesn't regress baseline | 30 min wall + 390 RPD | #1-4 |
| 6 | BIPED step 1 prompt design (consume cf-taxonomy.yaml + counterbalanced-principle.yaml) | 1-2j | #5 stable |
| 7 | BIPED step 2 response generator design | 1-2j | #6 |
| 8 | Battery EN + ES (BIPED end-to-end) | 1-2 jours wall + 750 RPD | #7 |

**Total pre-BIPED prep + BIPED dev** : ~5-7j wall, ~1140 RPD cumulé sur 2-3 jours différents (étalé pour respecter daily 540 limit).

## Cross-references

- ADR-014 : structured knowledge extraction (Layer 1.5)
- `data/extracted/lyster-2007-counterbalanced-content/cf-taxonomy.yaml`
- `data/extracted/lyster-2007-counterbalanced-content/counterbalanced-principle.yaml`
- `scripts/oracle/judges/llm_pairwise.py`
- `data/rubrics/en.yaml` + `data/rubrics/es.yaml`
- `data/fewshots/en.yaml` + `data/fewshots/es.yaml`
- [[teacher-en-improvement-research]] (vault — Tier 2 BIPED rationale Session 51)
- [[lyster-2007-counterbalanced-content]] (vault literature note)
