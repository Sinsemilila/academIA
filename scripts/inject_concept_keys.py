#!/usr/bin/env python3
"""
Injecte les concept_keys pour tous les niveaux anglais (A1, A2, B2, C1, C2).
B1 est déjà peuplé (20 clés).
Les clés sont cohérentes avec le curriculum (points_cles.grammaire) de chaque niveau.
"""

import json
import subprocess

CONCEPT_KEYS = {
    "A1": [
        "to_be_forms",
        "to_have_got",
        "present_simple",
        "subject_pronouns",
        "object_pronouns",
        "possessive_adjectives",
        "articles_a_an_the",
        "plural_nouns",
        "adjective_position",
        "demonstratives",
        "wh_questions",
        "short_answers",
        "prepositions_place",
        "prepositions_time",
        "there_is_there_are",
        "imperative",
        "cardinal_numbers",
        "ordinal_numbers"
    ],
    "A2": [
        "present_simple_full",
        "present_continuous",
        "past_simple_regular",
        "past_simple_irregular",
        "past_continuous",
        "future_going_to",
        "future_will",
        "comparatives",
        "superlatives",
        "modals_can_must_should",
        "modals_permission",
        "some_any_no",
        "much_many_countable",
        "adverbs_frequency",
        "relative_clauses_simple",
        "prepositions_movement",
        "conjunctions_basic",
        "question_tags"
    ],
    # B1 already populated — skip
    "B2": [
        "conditional_3",
        "mixed_conditionals",
        "modal_deduction_past",
        "modal_reproach_regret",
        "reported_speech_full",
        "passive_advanced",
        "inversion_negative",
        "cleft_sentences",
        "wish_past_perfect",
        "wish_would",
        "participle_clauses",
        "causative_structures",
        "compound_adjectives",
        "prefixes_suffixes",
        "articles_advanced",
        "reduced_relative_clauses",
        "connectors_sophisticated",
        "parallel_structures"
    ],
    "C1": [
        "nominalization",
        "inversion_stylistic",
        "subjunctive_formal",
        "ellipsis_substitution",
        "cohesion_deixis",
        "topicalization",
        "modals_stylistic",
        "conditionals_implicit",
        "reported_speech_nuanced",
        "hedging_academic",
        "gerund_subjects_complex",
        "absolute_constructions",
        "aspect_mastery",
        "gradation_stylistic"
    ],
    "C2": [
        "tense_aspect_flexibility",
        "rhetorical_manipulation",
        "stylistic_norm_breaking",
        "literary_forms",
        "creative_punctuation",
        "code_switching_register",
        "free_indirect_discourse",
        "complex_coordination",
        "meta_grammatical_awareness",
        "pragmatics_implicature"
    ]
}

for niveau, keys in CONCEPT_KEYS.items():
    keys_json = json.dumps(keys, ensure_ascii=False)
    keys_sql = keys_json.replace("'", "''")

    sql = f"UPDATE curriculums SET concept_keys = '{keys_sql}'::jsonb WHERE domaine = 'anglais' AND niveau = '{niveau}';"

    result = subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db"],
        input=sql, capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"  [OK] {niveau}: {len(keys)} concept_keys — {result.stdout.strip()}")
    else:
        print(f"  [ERR] {niveau}: {result.stderr.strip()}")

# Verify
result = subprocess.run(
    ["docker", "exec", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db",
     "-c", "SELECT niveau, jsonb_array_length(concept_keys) as nb_keys FROM curriculums WHERE domaine='anglais' ORDER BY id;"],
    capture_output=True, text=True
)
print(f"\nVerification:\n{result.stdout}")
