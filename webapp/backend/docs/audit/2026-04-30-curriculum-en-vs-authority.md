---
status: authoritative
last_reviewed: 2026-04-30
type: audit
session: 53
---

# Audit `curriculum_en.yaml` vs Authority Anchors (Hawkins 2012 + CEFR Companion 2020)

**Author** : Claude Sonnet 4.6 (Session 53 Phase B, 2026-04-30)
**Sources** :
- [`extracted/hawkins-filipovic-2012-criterial-features-l2-english/criterial-features-by-level.yaml`](../../packages/academie-core/academie_core/data/extracted/hawkins-filipovic-2012-criterial-features-l2-english/criterial-features-by-level.yaml)
- [`extracted/coe-2020-cefr-companion-volume/salient-features-by-level.yaml`](../../packages/academie-core/academie_core/data/extracted/coe-2020-cefr-companion-volume/salient-features-by-level.yaml)
- [`extracted/coe-2020-cefr-companion-volume/changes-2001-to-2020.yaml`](../../packages/academie-core/academie_core/data/extracted/coe-2020-cefr-companion-volume/changes-2001-to-2020.yaml)
- [`packages/academie-core/academie_core/data/curriculum_en.yaml`](../../packages/academie-core/academie_core/data/curriculum_en.yaml) (105 concept_keys A1-C2)

**Goal** : identify gaps + over-specifications + drift in `curriculum_en.yaml` vs Hawkins criterial features + Companion 2020 salient features. Each row = action for Phase B4 patch.

**Action codes** :
- `keep` : concept aligned, no action
- `add` : concept absent AcademIA, present in authority — ADD to curriculum
- `refine` : concept present but granularity wrong — REFINE description/weight
- `remove` : concept overspecified, not present in authority for this level — DEMOTE or REMOVE
- `relabel` : concept_key naming inconsistent with authority — RENAME
- `wording` : description text needs Companion 2020 inclusivity update

---

## Niveau A2

### A2 Authority criterial features (Hawkins 9.1.1 — 22 features) vs AcademIA (13 keys)

| # | Authority feature | AcademIA concept | Status | Action |
|---|---|---|---|---|
| 1 | Simple intransitive clauses NP-V | (implicit in `present_simple_basic`) | implicit | `keep` (granular implicit) |
| 2 | Transitive clauses NP-V-NP | (implicit) | implicit | `keep` |
| 3 | Ditransitive clauses NP-V-NP-NP | none | **gap** | `add` : `ditransitive_basic` weight 5 |
| 4 | Verbs with finite complement clause NP-V-S | none explicit | **gap** | `add` : `finite_complement_basic` weight 5 (e.g., "I knew that...") |
| 5 | Verbs with subject-controlled infinitival NP-V-VPinfin | (implicit `gerund_vs_infinitive` is B1) | **gap A2** | `add` : `infinitive_complements_basic` weight 5 (e.g., "I want to buy") |
| 6 | Direct WH-questions | `wh_questions` | aligned | `keep` |
| 7 | Pronoun plus infinitive ("something to eat") | none | **gap** | `add` : `pronoun_plus_infinitive` weight 3 |
| 8 | Postnominal modification with -ed ("paintings painted by") | none | **gap** | `add` : `postnominal_ed_modification` weight 5 |
| 9 | [of [of]] double embedding genitives | none | **gap** | `add` : `genitive_of_double_embedding` weight 3 |
| 10 | Modal MAY (Possibility/Epistemic) | (implicit `can_could_basic` covers possibility loosely) | **partial** | `refine` : split modal coverage explicitly |
| 11 | Modal MIGHT (Possibility) | none | **gap** | `add` : `might_possibility` weight 3 |
| 12 | Modal CAN (Possibility) | `can_could_basic` | aligned | `keep` |
| 13 | Modal MUST (Obligation/Deontic) | `modals_can_must_should` (but in A2 currently) | aligned | `keep` (but key is at A2 not A1) |
| 14 | Modal SHOULD (Advice/Deontic) | `modals_can_must_should` | partial | `refine` : SHOULD distinct sense |
| 15-20 | Negative criterial : NO Raising / NO Tough Movement | (correctly absent at A2) | aligned | `keep` |
| 21 | A2 verbs first attested (12 verbs : break, brush, climb...) | not lexicalized at concept level | n/a | `keep` (lexical inventory belongs to `concept_hints` + EVP, not curriculum_en) |
| 22 | Verb-particle "put on", "take off" Tr. | bundled into `phrasal_verbs` (currently B1!) | **mismatch** | `relabel` : Hawkins shows phrasal verbs FIRST appear at A2 (literal Tr.). Stratification A2/B1/B2/C1 per ADR + TODO Phase B5 cross-system migration |

### A2 AcademIA-only concepts (not in Hawkins criterial)

| AcademIA key | Hawkins A2? | Status | Action |
|---|---|---|---|
| `articles_a_an_the` | not in 9.1 (lexical) | over-spec | `keep` (correct A1-A2 scope, just not in 9.1 syntactic table) |
| `prepositions_place` | not in 9.1 | n/a | `keep` |
| `possessive_s` | not in 9.1 | n/a | `keep` |
| `there_is_there_are` | not in 9.1 | n/a | `keep` |
| `numbers_dates_times` | not in 9.1 | n/a | `keep` |
| `plural_nouns` | not in 9.1 | n/a | `keep` |
| `greetings_introductions` | (Companion App 2 A1-A2 social functions) | n/a | `keep` |
| `subject_pronouns` / `object_pronouns` | not in 9.1 | n/a | `keep` |
| `to_be_forms` / `to_have_got` | not in 9.1 | n/a | `keep` |
| `demonstratives` / `possessive_adjectives` | not in 9.1 | n/a | `keep` |
| `short_answers` | not in 9.1 | n/a | `keep` |
| `prepositions_time` | not in 9.1 | n/a | `keep` |
| `going_to_future` | not in 9.1 | n/a | `keep` (Companion B1 production) |
| `comparatives_superlatives` | not in 9.1 | n/a | `keep` |
| `will_would_basic` | not in 9.1 | n/a | `keep` |
| `present_continuous` | not in 9.1 | n/a | `keep` |
| `countable_uncountable` | not in 9.1 | n/a | `keep` |
| `adverbs_frequency` | not in 9.1 | n/a | `keep` |
| `basic_connectors` | not in 9.1 | n/a | `keep` |
| `past_continuous` | not in 9.1 | n/a | `keep` |
| `relative_clauses_simple` | not in 9.1 (Hawkins puts genitive-position relative clauses at B1) | n/a | `keep` |
| `prepositions_movement` | not in 9.1 | n/a | `keep` |
| `question_tags` | not in 9.1 | n/a | `keep` |

### A2 net actions

- **Add 7 concept_keys** : `ditransitive_basic`, `finite_complement_basic`, `infinitive_complements_basic`, `pronoun_plus_infinitive`, `postnominal_ed_modification`, `genitive_of_double_embedding`, `might_possibility`
- **Refine 1** : `modals_can_must_should` → split sense per modal (epistemic vs deontic) + integrate at proper levels (CAN already in A1, MAY+MIGHT at A2, MUST/SHOULD per Hawkins)
- **Phase B5 migration** : phrasal_verbs A2 stratification (cross-system, deferred per TODO)

A2 expansion : 13 → ~20 concepts (~+54%)

---

## Niveau B1

### B1 Authority criterial features (Hawkins 9.1.2 — 19 features) vs AcademIA (20 keys)

| # | Authority feature | AcademIA concept | Status | Action |
|---|---|---|---|---|
| 1 | MLU 10.8 (vs A2's 7.9) | n/a | meta | (curriculum doesn't track MLU per concept — could feed scoring threshold) |
| 2 | Object-controlled infinitival ("I ordered him to gather") | `gerund_vs_infinitive` partial | partial | `refine` : split object-controlled subcategory |
| 3 | Object-controlled -ing ("I saw a girl standing") | none | **gap** | `add` : `object_controlled_ing` weight 5 |
| 4 | Postnominal -ing ("mail asking for") | none | **gap** | `add` : `postnominal_ing_modification` weight 5 |
| 5 | It Extraposition with finite ("It's true that...") | none | **gap** | `add` : `it_extraposition_finite` weight 5 |
| 6 | Verbs PP plus finite complement NP-V-PP-S | none | **gap** | `add` : `verb_pp_finite_complement` weight 5 |
| 7 | Relative clauses on genitive position ("painter whose pictures") | covered by `relative_clauses` (whose) | aligned | `keep` |
| 8 | Pseudocleft WH as direct object ("what I saw was...") | none | **gap** | `add` : `pseudocleft_wh_object` weight 5 |
| 9 | Indirect WH-questions in finite ("Guess where I have been") | `indirect_questions` | aligned | `keep` |
| 10 | Indirect WH in infinitival ("where to look") | (within `indirect_questions`) | partial | `refine` : description should mention infinitival variant |
| 11 | Complex auxiliaries WOULD RATHER, HAD BETTER | none | **gap** | `add` : `complex_auxiliaries_b1` weight 3 |
| 12 | Adverbial subordinate -ing (following clause) | none | **gap** | `add` : `adverbial_ing_following` weight 5 |
| 13 | Subject-to-Subject Raising (seem, supposed) | none | **gap** | `add` : `raising_seem_supposed` weight 5 |
| 14 | Subject-to-Object Raising unpassivised (expect, like, want) | none | **gap** | `add` : `raising_object_basic` weight 5 |
| 15 | Tough Movement (easy) | none | **gap** | `add` : `tough_movement_easy` weight 3 |
| 16 | [of [-s]] double embedding genitive | none | **gap** | `add` : `genitive_of_s_embedding` weight 3 |
| 17 | Modal MAY (Permission/Deontic) | (implicit) | partial | `refine` |
| 18 | Modal MUST (Necessity/Epistemic) | (implicit) | partial | `refine` |
| 19 | Modal SHOULD (Probability/Epistemic) | (implicit) | partial | `refine` |

### B1 AcademIA concepts (existing — 20)

`present_perfect_simple`, `present_perfect_vs_past_simple`, `conditional_1`, `reported_speech`, `used_to`, `modal_deduction`, `phrasal_verbs`, `relative_clauses`, `gerund_vs_infinitive`, `adj_prepositions`, `connectors`, `present_perfect_continuous`, `past_perfect`, `both_either_neither`, `adverbs_degree`, `indirect_questions`, `so_such_that`, `would_habitual`, `passive_voice_basic`, `imperative`

| AcademIA key | Hawkins B1? | Status | Action |
|---|---|---|---|
| `present_perfect_simple` | not 9.1 | n/a | `keep` (Companion B1 narration descriptors) |
| `present_perfect_vs_past_simple` | not 9.1 | n/a | `keep` |
| `conditional_1` | not 9.1 | n/a | `keep` |
| `reported_speech` | not 9.1 | n/a | `keep` |
| `used_to` | not 9.1 | n/a | `keep` |
| `modal_deduction` | partial overlap with MUST B1 epistemic | aligned | `refine` description |
| `phrasal_verbs` | A2/B1 (Hawkins 8.2 progression) | mismatch | `relabel` Phase B5 |
| `relative_clauses` | aligned (whose at B1) | aligned | `keep` |
| `gerund_vs_infinitive` | partial (object-controlled split needed) | partial | `refine` |
| `adj_prepositions` | not 9.1 | n/a | `keep` |
| `connectors` | not 9.1 | n/a | `keep` |
| `present_perfect_continuous` | not 9.1 | n/a | `keep` |
| `past_perfect` | not 9.1 | n/a | `keep` |
| `both_either_neither` | not 9.1 | n/a | `keep` |
| `adverbs_degree` | not 9.1 | n/a | `keep` |
| `indirect_questions` | aligned | aligned | `keep` (refine to mention infinitival) |
| `so_such_that` | not 9.1 | n/a | `keep` |
| `would_habitual` | not 9.1 | n/a | `keep` |
| `passive_voice_basic` | not 9.1 (Hawkins B2 has Subject-to-Object passive) | aligned | `keep` (Hawkins focuses on raising passives, but basic passive correctly at B1) |
| `imperative` | not 9.1 (Companion functions) | n/a | `keep` |

### B1 net actions

- **Add 11 concept_keys** : `object_controlled_ing`, `postnominal_ing_modification`, `it_extraposition_finite`, `verb_pp_finite_complement`, `pseudocleft_wh_object`, `complex_auxiliaries_b1`, `adverbial_ing_following`, `raising_seem_supposed`, `raising_object_basic`, `tough_movement_easy`, `genitive_of_s_embedding`
- **Refine 3** : `gerund_vs_infinitive` split, `modal_deduction` split senses, `indirect_questions` mention infinitival

B1 expansion : 20 → ~31 concepts (~+55%)

---

## Niveau B2

### B2 Authority criterial features (Hawkins 9.1.3 — 11 features) vs AcademIA (19 keys)

| # | Authority feature | AcademIA concept | Status | Action |
|---|---|---|---|---|
| 1 | MLU 14.2 | n/a | meta | n/a |
| 2 | Adverbial subordinate -ing (preceding clause) | none | **gap** | `add` : `adverbial_ing_preceding` weight 5 |
| 3 | It Extraposition with infinitival | (covered partially by B1 it_extraposition_finite split) | **gap** | `add` : `it_extraposition_infinitival` weight 5 |
| 4 | Pseudocleft WH as subject ("what fascinated me was") | (B1 has WH as object) | **gap** | `add` : `pseudocleft_wh_subject` weight 8 |
| 5 | NP plus finite complement NP-V-NP-S ("I told him I loved...") | (covered by `reported_speech_full`) | partial | `refine` |
| 6 | Secondary predications ("paint the houses yellow") | none | **gap** | `add` : `secondary_predications` weight 5 |
| 7 | Productive Subject-to-Subject Raising (appear, certain, likely...) | none | **gap** | `add` : `raising_subject_productive` weight 8 |
| 8 | New Subject-to-Object Raising unpassivised (imagine, prefer) | none | **gap** | `add` (extend B1 `raising_object_basic`) |
| 9 | Subject-to-Object Raising plus Passive (expected, known, obliged, thought) | (currently `passive_voice_advanced` could cover) | partial | `refine` : split into `raising_passive_b2` |
| 10 | New Tough Movement (difficult, good, hard) | (extends B1 `tough_movement_easy`) | partial | `refine` |
| 11 | [[of] -s] double embedding ("United States of America's") | none | **gap** | `add` : `genitive_double_embedding_b2` weight 5 |

### B2 AcademIA concepts existing — 19

`conditional_2`, `subjunctive_wish_ifonly`, `conditional_3`, `reported_speech_full`, `passive_voice_advanced`, `connectors_sophisticated`, `articles_advanced`, `causative_structures`, `cleft_sentences`, `compound_adjectives`, `inversion_negative`, `modal_deduction_past`, `modal_reproach_regret`, `parallel_structures`, `participle_clauses`, `prefixes_suffixes`, `reduced_relative_clauses`, `wish_past_perfect`, `wish_would`

Most B2 AcademIA keys NOT in Hawkins 9.1 (Hawkins focuses on raising/embedding ; AcademIA focuses on tense/conditional). Both valid — complementary.

⚠️ **Note** : `cleft_sentences` AcademIA = "It was John who broke it / What I need is rest" — but Hawkins B1 has WH-object pseudocleft, B2 has WH-subject pseudocleft. AcademIA `cleft_sentences` conflates both. **Refine** : split `cleft_it_was`, `pseudocleft_wh_object` (B1), `pseudocleft_wh_subject` (B2).

### B2 net actions

- **Add 6 concept_keys** : `adverbial_ing_preceding`, `it_extraposition_infinitival`, `pseudocleft_wh_subject`, `secondary_predications`, `raising_subject_productive`, `genitive_double_embedding_b2`
- **Refine 4** : `cleft_sentences` split, `passive_voice_advanced` add raising passive variant, `reported_speech_full` mention NP-V-NP-S

B2 expansion : 19 → ~25 concepts (~+32%)

---

## Niveau C1

### C1 Authority criterial features (Hawkins 9.1.4 — 6 features) vs AcademIA (20 keys)

| # | Authority feature | AcademIA concept | Status | Action |
|---|---|---|---|---|
| 1 | MLU 17.3 | n/a | meta | n/a |
| 2 | New Subject-to-Subject Raising (chance) | (extends B2 `raising_subject_productive`) | partial | `refine` |
| 3 | New Subject-to-Object Raising unpassivised (believe, find, suppose, take) | (extends B2) | partial | `refine` |
| 4 | New Subject-to-Object Raising plus Passive (assumed, discovered, felt, found, proved) | (extends B2) | partial | `refine` |
| 5 | [[-s] -s] double embedding ("the bride's family's house") | none | **gap** | `add` : `genitive_ss_embedding` weight 5 |
| 6 | Modal MIGHT (Permission/Deontic — "Might I tell you?") | none | **gap** | `add` : `might_permission_formal` weight 3 |

### C1 AcademIA-only concepts (20 keys)

Most are **valid stylistic/discourse features** (inversion, hedging, nominalization) that Hawkins doesn't cover (Hawkins focus = syntax + lexis at A2-C2 ; stylistic discourse outside scope).

| AcademIA key | Authority alignment | Action |
|---|---|---|
| `inversion_negative_adverbial` | not Hawkins (style) | `keep` |
| `advanced_collocations` | not Hawkins (lexical/style) | `keep` |
| `idioms_transparent` | not Hawkins | `keep` |
| `register_formal_informal` | Companion C1 social_academic_professional | aligned | `keep` |
| `causative_have` | not Hawkins | `keep` |
| `emphatic_do` | not Hawkins | `keep` |
| `absolute_constructions` | not Hawkins | `keep` |
| `aspect_mastery` | not Hawkins | `keep` |
| `cohesion_deixis` | Companion C1 cohesive devices | aligned | `keep` |
| `conditionals_implicit` | not Hawkins | `keep` |
| `ellipsis_substitution` | not Hawkins | `keep` |
| `gerund_subjects_complex` | not Hawkins | `keep` |
| `gradation_stylistic` | not Hawkins | `keep` |
| `hedging_academic` | Companion C1 academic | aligned | `keep` |
| `inversion_stylistic` | not Hawkins | `keep` |
| `modals_stylistic` | not Hawkins | `keep` |
| `nominalization` | not Hawkins | `keep` |
| `reported_speech_nuanced` | not Hawkins | `keep` |
| `subjunctive_formal` | not Hawkins | `keep` |
| `topicalization` | not Hawkins | `keep` |

### C1 net actions

- **Add 2 concept_keys** : `genitive_ss_embedding`, `might_permission_formal`
- **Refine 3** : raising extensions

C1 expansion : 20 → ~22 concepts (~+10%)

---

## Niveau C2

### C2 Authority criterial features (Hawkins 9.1.5 — 5 features) vs AcademIA (15 keys)

| # | Authority feature | AcademIA concept | Status | Action |
|---|---|---|---|---|
| 1 | MLU 19.0 | n/a | meta | n/a |
| 2 | New Subject-to-Object Raising unpassivised (declare, presume, remember) | (extends C1) | partial | `refine` |
| 3 | New Subject-to-Object Raising plus Passive (presumed) | (extends C1) | partial | `refine` |
| 4 | New Tough Movement (tough) | (extends B2) | partial | `refine` |
| 5 | NEGATIVE : No new Subject-to-Subject Raising | meta | n/a | n/a |

C2 AcademIA keys (15) cover idioms, stylistic features, pragmatic nuance — **valid C2 mastery markers** outside Hawkins scope.

### C2 wording fix

⚠️ **CRITICAL** : `curriculum_en.yaml` C2 description says **"near-native, pragmatic nuance"**. Companion 2020 explicitly states **C2 is NOT native-speaker level** (App 1 page 175 : "Level C2 is not intended to imply native-speaker or near native-speaker competence").

**Action** `wording` : C2 description revise → "highly successful learner mastery — pragmatic nuance, linguistic creativity. Residual errors = fluency markers, not competence gaps. NOT native-speaker level."

### C2 net actions

- **Wording fix** : C2 description (remove "near-native") — Companion 2020 inclusivity
- **Refine 3** : raising extensions
- No additions (C2 syntax features fold into C1 raising extensions)

---

## Cross-cutting (all levels)

### Inclusivity wording (CEFR Companion 2020 App 7)

⚠️ **All curriculum descriptions reference "native-speaker" terminology should be updated** :
- Currently `curriculum_en.yaml` C2 = "near-native" → revise to "highly successful learner"
- B2 description "argue, nuance position, cultural comparison, debate" = OK
- Other descriptions clean

### NEW dimensions absent (defer Phase D)

Curriculum_en is **structural-only**. CEFR Companion 2020 organizes by **4 modes** (Reception / Production / Interaction / **Mediation NEW 2020**). PCIC has 13 inventarios. AcademIA has 1 dimension.

→ **Phase D** dedicated session : add `data/functions/`, `data/mediation/`, possibly skills-based parallel structure.

### Header source attribution fix

`curriculum_en.yaml` line 2 originally claimed "Sourced from CEFR 2020 Companion + EVP + Hughes & Reed" — these were aspirational pre-S52. Phase A header annotation S53 already honest. **Now Phase B4 patch** : update header to cite REAL sources :
```
# Sources actually consulted (post-S53 audit) :
# - Hawkins/Filipović 2012 — Criterial Features in L2 English (Ch 9.1 horizontal summary)
# - Council of Europe 2020 — CEFR Companion Volume (App 1 salient features + App 7 changes)
```

---

## Summary table

| Level | AcademIA pre-audit | Audit additions | Audit refines | Audit removes | Post-audit estimate |
|---|---|---|---|---|---|
| A1 | 18 | 0 | 0 | 0 | 18 (Hawkins doesn't cover A1) |
| A2 | 13 | +7 | 1 | 0 | ~20 |
| B1 | 20 | +11 | 3 | 0 | ~31 |
| B2 | 19 | +6 | 4 | 0 | ~25 |
| C1 | 20 | +2 | 3 | 0 | ~22 |
| C2 | 15 | 0 | 3 + wording | 0 | 15 |
| **Total** | **105** | **+26** | **14** | **0** | **~131** |

**Net**: curriculum_en passes from 105 → ~131 concepts (+25%). All additions are Hawkins criterial features (syntax + raising + extraposition + cleft). Stylistic/discourse C1+C2 keys remain.

---

## Phase B4 patch checklist

- [ ] Update `curriculum_en.yaml` header source attribution (real sources)
- [ ] Add 26 concept_keys A2-C1 with weights + groups
- [ ] Refine 14 concept descriptions/granularity
- [ ] Update C2 description (remove "near-native" → "highly successful learner")
- [ ] Sync `concept_hints/en.yaml` with 26 new entries (Phase A1 already 105 covered, expand to ~131)
- [ ] Run pytest schema validation
- [ ] Smoke test (oracle harness battery EN — 26 goldens) post-patch — expect baseline preserved 18-19/26 ±1

**DEFERRED Phase B5** : phrasal_verbs cross-system migration (A2/B1/B2/C1 stratification per Hawkins Ch 8) — separate dedicated session, touches profile_router.py + tolerance_matrix + Dify workflows.

**DEFERRED Phase D** : Functions + Mediation + Skills-based dimensions.
