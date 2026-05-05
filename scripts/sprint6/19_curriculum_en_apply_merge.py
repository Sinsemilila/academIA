"""Session 41 — Apply agent-decided curriculum_en.yaml merge (53 → 94 concepts).

The Explore agent produced per-concept decisions (ADD / KEEP / RENAME / MOVE /
DROP) across all 6 CEFR levels. This script encodes those decisions and
generates the new `curriculum_en.yaml` directly, preserving the YAML
structure (domain + per-level description + concept_keys + concept_weights
+ concept_groups).

Validation : run `pytest packages/academie-core/tests/test_yaml_schema.py`
after applying — must stay green.

Usage :
  python3 scripts/sprint6/19_curriculum_en_apply_merge.py         # dry-run
  python3 scripts/sprint6/19_curriculum_en_apply_merge.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

YAML_PATH = Path("/opt/academia/packages/academie-core/academie_core/data/curriculum_en.yaml")


# ── Per-level concept definitions (from agent decisions) ──
# Each concept : (key, weight, group)

A1_CONCEPTS = [
    # Existing YAML-KEPT
    ("present_simple_basic", 5, "grammar"),
    ("articles_a_an_the", 5, "nouns_articles"),
    ("prepositions_place", 3, "connectors"),
    ("possessive_s", 3, "nouns_articles"),
    ("can_could_basic", 3, "verb_tenses"),
    ("there_is_there_are", 3, "structures"),
    ("numbers_dates_times", 3, "misc"),
    ("plural_nouns", 3, "nouns_articles"),
    ("greetings_introductions", 3, "misc"),
    # ADD from DB
    ("subject_pronouns", 3, "pronouns"),
    ("object_pronouns", 3, "pronouns"),
    ("to_be_forms", 5, "verb_tenses"),
    ("to_have_got", 5, "verb_tenses"),
    ("demonstratives", 3, "nouns_articles"),
    ("possessive_adjectives", 5, "nouns_articles"),
    ("wh_questions", 5, "questions"),
    ("short_answers", 3, "questions"),
    ("prepositions_time", 5, "connectors"),
]

A2_CONCEPTS = [
    # KEEP
    ("past_simple_regular_irregular", 8, "verb_tenses"),
    ("going_to_future", 5, "verb_tenses"),
    ("comparatives_superlatives", 5, "modifiers"),
    ("will_would_basic", 3, "verb_tenses"),
    ("present_continuous", 5, "verb_tenses"),
    ("countable_uncountable", 5, "nouns_articles"),
    ("adverbs_frequency", 3, "modifiers"),
    ("basic_connectors", 3, "connectors"),
    # ADD
    ("modals_can_must_should", 5, "verb_tenses"),
    ("past_continuous", 5, "verb_tenses"),
    ("relative_clauses_simple", 5, "relative_clauses"),
    ("prepositions_movement", 5, "connectors"),
    ("question_tags", 3, "questions"),
]

B1_CONCEPTS = [
    # KEEP
    ("present_perfect_simple", 8, "verb_tenses"),
    ("present_perfect_vs_past_simple", 8, "verb_tenses"),
    ("conditional_1", 5, "verb_tenses"),
    ("reported_speech", 5, "discourse"),
    ("used_to", 3, "verb_tenses"),
    ("modal_deduction", 5, "verb_tenses"),
    ("phrasal_verbs", 8, "vocabulary"),
    ("relative_clauses", 5, "relative_clauses"),
    ("gerund_vs_infinitive", 5, "structures"),
    ("adj_prepositions", 3, "modifiers"),
    # ADD + MOVED
    ("connectors", 5, "connectors"),
    ("present_perfect_continuous", 8, "verb_tenses"),
    ("past_perfect", 8, "verb_tenses"),
    ("both_either_neither", 5, "connectors"),
    ("adverbs_degree", 5, "modifiers"),           # moved from C1
    ("indirect_questions", 5, "questions"),
    ("so_such_that", 5, "connectors"),
    ("would_habitual", 5, "verb_tenses"),
    ("passive_voice_basic", 8, "verb_tenses"),
    ("imperative", 3, "structures"),               # moved from A1
]

B2_CONCEPTS = [
    # KEEP
    ("conditional_2", 5, "verb_tenses"),
    ("subjunctive_wish_ifonly", 5, "verb_tenses"),
    # RENAME
    ("conditional_3", 8, "verb_tenses"),           # was conditional_3_mixed
    # ADD
    ("reported_speech_full", 8, "discourse"),
    ("passive_voice_advanced", 8, "verb_tenses"),
    ("connectors_sophisticated", 5, "connectors"),
    ("articles_advanced", 3, "nouns_articles"),
    ("causative_structures", 8, "structures"),
    ("cleft_sentences", 8, "structures"),
    ("compound_adjectives", 5, "modifiers"),
    ("inversion_negative", 8, "structures"),
    ("modal_deduction_past", 5, "verb_tenses"),
    ("modal_reproach_regret", 5, "verb_tenses"),
    ("parallel_structures", 5, "discourse"),
    ("participle_clauses", 5, "structures"),
    ("prefixes_suffixes", 5, "vocabulary"),
    ("reduced_relative_clauses", 5, "relative_clauses"),
    ("wish_past_perfect", 8, "verb_tenses"),
    ("wish_would", 5, "verb_tenses"),
]

C1_CONCEPTS = [
    # KEEP
    ("inversion_negative_adverbial", 5, "structures"),
    ("advanced_collocations", 8, "vocabulary"),
    ("idioms_transparent", 8, "vocabulary"),
    ("register_formal_informal", 5, "discourse"),
    ("causative_have", 5, "structures"),
    ("emphatic_do", 3, "structures"),
    # ADD
    ("absolute_constructions", 5, "structures"),
    ("aspect_mastery", 5, "verb_tenses"),
    ("cohesion_deixis", 5, "discourse"),
    ("conditionals_implicit", 8, "verb_tenses"),
    ("ellipsis_substitution", 5, "discourse"),
    ("gerund_subjects_complex", 5, "structures"),
    ("gradation_stylistic", 5, "modifiers"),
    ("hedging_academic", 5, "discourse"),
    ("inversion_stylistic", 8, "structures"),
    ("modals_stylistic", 5, "verb_tenses"),
    ("nominalization", 5, "discourse"),
    ("reported_speech_nuanced", 8, "discourse"),
    ("subjunctive_formal", 8, "verb_tenses"),
    ("topicalization", 5, "discourse"),
]

C2_CONCEPTS = [
    # KEEP
    ("idioms_opaque", 8, "vocabulary"),
    ("literary_inversion", 5, "structures"),
    ("pragmatic_nuance", 8, "discourse"),
    ("cultural_references", 5, "vocabulary"),
    ("discourse_markers_c2", 3, "discourse"),
    # ADD
    ("code_switching_register", 5, "discourse"),
    ("complex_coordination", 5, "discourse"),
    ("creative_punctuation", 5, "discourse"),
    ("free_indirect_discourse", 5, "discourse"),
    ("literary_forms", 5, "discourse"),
    ("meta_grammatical_awareness", 5, "discourse"),
    ("pragmatics_implicature", 5, "discourse"),
    ("rhetorical_manipulation", 5, "discourse"),
    ("stylistic_norm_breaking", 5, "discourse"),
    ("tense_aspect_flexibility", 5, "verb_tenses"),
]

LEVELS = {
    "A1": (A1_CONCEPTS, "Survival — greet, introduce, request basic info (time, price, name, place). Present simple + can/want. Concrete vocab (~500 words BNC)."),
    "A2": (A2_CONCEPTS, "Waystage — tell recent experience, express likes, simple comparisons, shopping. Past simple + going-to + would like."),
    "B1": (B1_CONCEPTS, "Threshold — hold conversation on familiar topics, narrate events, give opinion+reason, manage travel. Past tenses + present perfect + first conditional."),
    "B2": (B2_CONCEPTS, "Vantage — argue, nuance position, cultural comparison, debate. All structures except rare + lexical precision."),
    "C1": (C1_CONCEPTS, "Effective Operational Proficiency — precise mastery, register-aware, academic debate, structured writing. Idioms, literary inversion, advanced collocations."),
    "C2": (C2_CONCEPTS, "Mastery — near-native, pragmatic nuance, linguistic creativity. Residual errors = fluency markers, not competence gaps."),
}


def build_curriculum() -> dict:
    out: dict = {"domain": "en"}
    for lvl, (concepts, description) in LEVELS.items():
        keys = [c[0] for c in concepts]
        weights = {c[0]: c[1] for c in concepts}
        # Build groups
        groups: dict[str, list[str]] = {}
        for k, _, g in concepts:
            groups.setdefault(g, []).append(k)
        out[lvl] = {
            "description": description,
            "concept_keys": keys,
            "concept_weights": weights,
            "concept_groups": groups,
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--show-diff", action="store_true")
    args = ap.parse_args()

    new = build_curriculum()
    old = yaml.safe_load(YAML_PATH.read_text())

    print("▶ Merge summary")
    for lvl in ["A1", "A2", "B1", "B2", "C1", "C2"]:
        old_n = len(old.get(lvl, {}).get("concept_keys", []))
        new_n = len(new[lvl]["concept_keys"])
        print(f"  {lvl} : {old_n} → {new_n} concepts  (+{new_n - old_n})")
    total_old = sum(len(old.get(l, {}).get("concept_keys", [])) for l in ["A1","A2","B1","B2","C1","C2"])
    total_new = sum(len(new[l]["concept_keys"]) for l in ["A1","A2","B1","B2","C1","C2"])
    print(f"  TOTAL : {total_old} → {total_new}")

    if not args.apply:
        print("\n▶ DRY-RUN. Re-run with --apply to overwrite YAML.")
        return 0

    # Preserve the YAML header comment
    header = (
        "# English curriculum — CEFR concepts + weights + groups per level.\n"
        "# Sourced from : CEFR 2020 Companion Volume, Cambridge English Profile (EVP),\n"
        "#   Hughes & Reed B2-C2 grammars, concept_hints/en.yaml (20 concepts) +\n"
        "#   rubrics/en.yaml \"Target structures\" sections per level.\n"
        "# Format mirrors curriculum_es.yaml (used by Dify chatflow Teacher +\n"
        "# error_analysis_router).\n"
        "# Keys MUST match concept_hints/en.yaml where present (additional structural keys\n"
        "# introduced here are documented in comments).\n"
        "#\n"
        "# Updated : Session 41 (2026-04-23) — merge from DB taxonomy (53 → 94 concepts).\n"
        "# See `scripts/sprint6/19_curriculum_en_apply_merge.py` for canonical source of truth.\n"
        "#\n"
        "# weight = minutes estimées par concept (3 = léger, 5 = moyen, 8 = lourd)\n"
        "# group = thème fonctionnel pour les examens (regroupe concepts reliés)\n\n"
    )
    body = yaml.safe_dump(new, sort_keys=False, allow_unicode=True, default_flow_style=False, width=120)
    YAML_PATH.write_text(header + body)
    print(f"▶ Wrote {YAML_PATH.relative_to(Path('/opt/academia'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
