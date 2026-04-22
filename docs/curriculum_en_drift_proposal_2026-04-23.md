# curriculum_en.yaml drift proposal

_Generated from DB `curriculums` table (98 total concepts) vs `packages/academie-core/.../curriculum_en.yaml` (53 total)._

## TL;DR

The drift is not just additive — the two sources use **different naming conventions** for similar concepts :
- YAML uses `present_simple_basic` ; DB uses `to_be_forms` + `to_have_got` + `present_simple` (3 granular concepts)
- YAML uses `personal_pronouns` ; DB uses `subject_pronouns` + `object_pronouns` (split by function)
- etc.

So merging requires deciding per-concept whether to :
- **adopt** the DB name (more granular, aligned with error_log taxonomy)
- **keep** the YAML name (simpler, aggregated)
- **add both** (DB in YAML + keep YAML alias as aggregate)

## Summary

| Level | DB | YAML | In DB not YAML | In YAML not DB |
|---|---|---|---|---|
| A1 | 18 | 10 | 14 | 6 |
| A2 | 18 | 9 | 16 | 7 |
| B1 | 20 | 10 | 10 | 0 |
| B2 | 18 | 10 | 18 | 10 |
| C1 | 14 | 9 | 14 | 9 |
| C2 | 10 | 5 | 10 | 5 |
| **Total** | **98** | **53** | **82** | **37** |

## Per-level proposal

For each missing concept, the script proposes a weight (min) and a group based on heuristics. **Sinse validates/overrides each row.**

### A1

#### DB-only — 14 concepts (add to YAML?)

| Concept | Proposed weight | Proposed group | Action |
|---|---|---|---|
| `adjective_position` | 5 | `modifiers` | |
| `cardinal_numbers` | 3 | `misc` | |
| `demonstratives` | 3 | `nouns_articles` | |
| `imperative` | 3 | `misc` | |
| `object_pronouns` | 3 | `nouns_articles` | |
| `ordinal_numbers` | 3 | `misc` | |
| `possessive_adjectives` | 5 | `nouns_articles` | |
| `prepositions_time` | 5 | `connectors` | |
| `present_simple` | 5 | `verb_tenses` | |
| `short_answers` | 3 | `misc` | |
| `subject_pronouns` | 3 | `nouns_articles` | |
| `to_be_forms` | 5 | `verb_tenses` | |
| `to_have_got` | 5 | `verb_tenses` | |
| `wh_questions` | 5 | `questions` | |

_Action legend : `ADD` = integrate as-is / `ADD-RENAME=xxx` = add with different key / `DROP` = DB value was bad, remove from DB_

#### YAML-only — 6 concepts (remove from YAML?)

| Concept | Action |
|---|---|
| `can_could_basic` | |
| `greetings_introductions` | |
| `numbers_dates_times` | |
| `personal_pronouns` | |
| `possessive_s` | |
| `present_simple_basic` | |

_Action legend : `KEEP` = YAML canonical / `REPLACE-BY=xxx` = superseded by a DB concept / `DROP` = obsolete_

### A2

#### DB-only — 16 concepts (add to YAML?)

| Concept | Proposed weight | Proposed group | Action |
|---|---|---|---|
| `comparatives` | 5 | `modifiers` | |
| `conjunctions_basic` | 5 | `connectors` | |
| `future_going_to` | 5 | `verb_tenses` | |
| `future_will` | 5 | `verb_tenses` | |
| `modals_can_must_should` | 5 | `verb_tenses` | |
| `modals_permission` | 5 | `verb_tenses` | |
| `much_many_countable` | 5 | `misc` | |
| `past_continuous` | 5 | `verb_tenses` | |
| `past_simple_irregular` | 5 | `verb_tenses` | |
| `past_simple_regular` | 5 | `verb_tenses` | |
| `prepositions_movement` | 5 | `connectors` | |
| `present_simple_full` | 5 | `verb_tenses` | |
| `question_tags` | 3 | `questions` | |
| `relative_clauses_simple` | 5 | `relative_clauses` | |
| `some_any_no` | 5 | `misc` | |
| `superlatives` | 5 | `modifiers` | |

_Action legend : `ADD` = integrate as-is / `ADD-RENAME=xxx` = add with different key / `DROP` = DB value was bad, remove from DB_

#### YAML-only — 7 concepts (remove from YAML?)

| Concept | Action |
|---|---|
| `basic_connectors` | |
| `comparatives_superlatives` | |
| `countable_uncountable` | |
| `going_to_future` | |
| `object_pronouns` | |
| `past_simple_regular_irregular` | |
| `will_would_basic` | |

_Action legend : `KEEP` = YAML canonical / `REPLACE-BY=xxx` = superseded by a DB concept / `DROP` = obsolete_

### B1

#### DB-only — 10 concepts (add to YAML?)

| Concept | Proposed weight | Proposed group | Action |
|---|---|---|---|
| `adverbs_degree` | 5 | `modifiers` | |
| `both_either_neither` | 5 | `misc` | |
| `conditional_2` | 8 | `verb_tenses` | |
| `connectors` | 5 | `misc` | |
| `indirect_questions` | 5 | `questions` | |
| `passive_voice` | 8 | `verb_tenses` | |
| `past_perfect` | 8 | `verb_tenses` | |
| `present_perfect_continuous` | 8 | `verb_tenses` | |
| `so_such_that` | 5 | `misc` | |
| `would_habitual` | 5 | `misc` | |

_Action legend : `ADD` = integrate as-is / `ADD-RENAME=xxx` = add with different key / `DROP` = DB value was bad, remove from DB_

### B2

#### DB-only — 18 concepts (add to YAML?)

| Concept | Proposed weight | Proposed group | Action |
|---|---|---|---|
| `articles_advanced` | 3 | `nouns_articles` | |
| `causative_structures` | 8 | `misc` | |
| `cleft_sentences` | 8 | `misc` | |
| `compound_adjectives` | 5 | `modifiers` | |
| `conditional_3` | 8 | `verb_tenses` | |
| `connectors_sophisticated` | 5 | `misc` | |
| `inversion_negative` | 8 | `questions` | |
| `mixed_conditionals` | 8 | `verb_tenses` | |
| `modal_deduction_past` | 5 | `verb_tenses` | |
| `modal_reproach_regret` | 5 | `verb_tenses` | |
| `parallel_structures` | 5 | `misc` | |
| `participle_clauses` | 5 | `misc` | |
| `passive_advanced` | 8 | `verb_tenses` | |
| `prefixes_suffixes` | 5 | `misc` | |
| `reduced_relative_clauses` | 5 | `relative_clauses` | |
| `reported_speech_full` | 8 | `verb_tenses` | |
| `wish_past_perfect` | 8 | `verb_tenses` | |
| `wish_would` | 5 | `misc` | |

_Action legend : `ADD` = integrate as-is / `ADD-RENAME=xxx` = add with different key / `DROP` = DB value was bad, remove from DB_

#### YAML-only — 10 concepts (remove from YAML?)

| Concept | Action |
|---|---|
| `conditional_2` | |
| `conditional_3_mixed` | |
| `connectors` | |
| `indirect_questions` | |
| `passive_voice` | |
| `past_perfect` | |
| `present_perfect_continuous` | |
| `so_such_that` | |
| `subjunctive_wish_ifonly` | |
| `would_habitual` | |

_Action legend : `KEEP` = YAML canonical / `REPLACE-BY=xxx` = superseded by a DB concept / `DROP` = obsolete_

### C1

#### DB-only — 14 concepts (add to YAML?)

| Concept | Proposed weight | Proposed group | Action |
|---|---|---|---|
| `absolute_constructions` | 5 | `misc` | |
| `aspect_mastery` | 5 | `misc` | |
| `cohesion_deixis` | 5 | `misc` | |
| `conditionals_implicit` | 8 | `verb_tenses` | |
| `ellipsis_substitution` | 5 | `misc` | |
| `gerund_subjects_complex` | 5 | `vocabulary` | |
| `gradation_stylistic` | 5 | `misc` | |
| `hedging_academic` | 5 | `misc` | |
| `inversion_stylistic` | 8 | `questions` | |
| `modals_stylistic` | 5 | `verb_tenses` | |
| `nominalization` | 5 | `misc` | |
| `reported_speech_nuanced` | 8 | `verb_tenses` | |
| `subjunctive_formal` | 8 | `verb_tenses` | |
| `topicalization` | 5 | `misc` | |

_Action legend : `ADD` = integrate as-is / `ADD-RENAME=xxx` = add with different key / `DROP` = DB value was bad, remove from DB_

#### YAML-only — 9 concepts (remove from YAML?)

| Concept | Action |
|---|---|
| `advanced_collocations` | |
| `adverbs_degree` | |
| `both_either_neither` | |
| `causative_have` | |
| `cleft_sentences` | |
| `emphatic_do` | |
| `idioms_transparent` | |
| `inversion_negative_adverbial` | |
| `register_formal_informal` | |

_Action legend : `KEEP` = YAML canonical / `REPLACE-BY=xxx` = superseded by a DB concept / `DROP` = obsolete_

### C2

#### DB-only — 10 concepts (add to YAML?)

| Concept | Proposed weight | Proposed group | Action |
|---|---|---|---|
| `code_switching_register` | 5 | `discourse` | |
| `complex_coordination` | 5 | `vocabulary` | |
| `creative_punctuation` | 5 | `misc` | |
| `free_indirect_discourse` | 5 | `discourse` | |
| `literary_forms` | 5 | `misc` | |
| `meta_grammatical_awareness` | 5 | `misc` | |
| `pragmatics_implicature` | 5 | `misc` | |
| `rhetorical_manipulation` | 5 | `misc` | |
| `stylistic_norm_breaking` | 5 | `misc` | |
| `tense_aspect_flexibility` | 5 | `vocabulary` | |

_Action legend : `ADD` = integrate as-is / `ADD-RENAME=xxx` = add with different key / `DROP` = DB value was bad, remove from DB_

#### YAML-only — 5 concepts (remove from YAML?)

| Concept | Action |
|---|---|
| `cultural_references` | |
| `discourse_markers_c2` | |
| `idioms_opaque` | |
| `literary_inversion` | |
| `pragmatic_nuance` | |

_Action legend : `KEEP` = YAML canonical / `REPLACE-BY=xxx` = superseded by a DB concept / `DROP` = obsolete_

## What to do

1. Review each row. Mark `✅` keep, `❌` drop. If keep, correct weight/group if my heuristic guess is wrong.
2. Run `python3 scripts/sprint6/19_curriculum_en_merge_apply.py --manual /tmp/curriculum_en_review.md` (Session 42) to merge your corrections into curriculum_en.yaml.
3. Re-run `pytest packages/academie-core/tests/test_yaml_schema.py` — must pass.
4. Run `python3 scripts/inject_curriculum.py --domain en --force` to push to DB.
5. Commit `[data] Session X — curriculum_en.yaml drift merged (XX new concepts from DB)`.