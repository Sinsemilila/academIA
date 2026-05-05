"""Sprint 3 — Tests for teacher_prompt.py helpers.

Validates dosage budget, tier→feedback mapping (with diversity rule + gravity
overrides), anti-drift triggers, L1 watch, spaced retrieval, JSON parsing.

Run with USE_V2_TOLERANCE=true for parity with prod.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_BACKEND = "/opt/academia/webapp/backend"
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from academie_core.pedagogy.teacher_prompt import (
    DOSAGE_BUDGET,
    DOSAGE_HARD_CAP,
    FEEDBACK_TYPES,
    LEVELS,
    TIERS,
    arbitrate_dosage,
    build_drift_check_request,
    build_dynamic_sections,
    build_l1_watch,
    build_level_reminder,
    build_spaced_retrieval_block,
    compute_dosage_budget,
    parse_teacher_response,
    PromptContext,
    render_fewshots_block,
    rubric_for_level,
    select_fewshots,
    should_inject_level_reminder,
    should_request_drift_check,
    tier_to_feedback_type,
    update_feedback_history,
)


# ── Constants sanity ─────────────────────────────────────────────────


def test_levels_constant_covers_a1_to_c2():
    assert LEVELS == ("A1", "A2", "B1", "B2", "C1", "C2")


def test_tiers_constant_covers_t0_to_t4():
    assert TIERS == ("T0", "T1", "T2", "T3", "T4")


def test_feedback_types_5_distinct():
    assert len(set(FEEDBACK_TYPES)) == 5
    assert "implicit_recast" in FEEDBACK_TYPES
    assert "elicitation" in FEEDBACK_TYPES
    assert "metalinguistic" in FEEDBACK_TYPES
    assert "prompt_plus_remediation" in FEEDBACK_TYPES
    assert "silent" in FEEDBACK_TYPES


def test_dosage_budget_has_every_level():
    assert set(DOSAGE_BUDGET.keys()) == set(LEVELS)
    assert set(DOSAGE_HARD_CAP.keys()) == set(LEVELS)
    # Hard cap must be ≥ regular budget
    for lvl in LEVELS:
        assert DOSAGE_HARD_CAP[lvl] >= DOSAGE_BUDGET[lvl]


# ── Rubric per level ─────────────────────────────────────────────────


@pytest.mark.parametrize("level", LEVELS)
def test_rubric_returns_non_empty_for_every_level(level):
    rubric = rubric_for_level(level)
    assert rubric
    # First non-empty line should mention the level
    first_line = rubric.split("\n", 1)[0]
    assert level in first_line


def test_rubric_unknown_level_falls_back_to_b1():
    assert rubric_for_level("X9").startswith("RUBRIC B1")


def test_rubric_handles_plus_suffix():
    # B1+ should normalise to B1
    assert rubric_for_level("B1+") == rubric_for_level("B1")


# ── Dosage budget computation ────────────────────────────────────────


@pytest.mark.parametrize("level,expected", [
    ("A1", 1), ("A2", 2), ("B1", 3), ("B2", 3), ("C1", 4), ("C2", 4),
])
def test_dosage_budget_matches_design(level, expected):
    assert compute_dosage_budget(level) == expected


def test_dosage_budget_all_t4_uses_hard_cap():
    assert compute_dosage_budget("A1", all_t4=True) == 2
    assert compute_dosage_budget("B1", all_t4=True) == 4


def test_arbitrate_t4_always_included_within_cap():
    errors = [
        {"error_code": "X1", "tier": "T4", "gravity_linguistic": 0.8},
        {"error_code": "X2", "tier": "T4", "gravity_linguistic": 0.8},
    ]
    decision = arbitrate_dosage("A1", errors)
    assert decision.budget == 2  # hard cap because all T4
    assert len(decision.to_correct) == 2
    assert decision.saturated is False


def test_arbitrate_t3_drops_when_over_budget():
    errors = [
        {"error_code": "X1", "tier": "T3", "gravity_linguistic": 0.8},
        {"error_code": "X2", "tier": "T3", "gravity_linguistic": 0.8},
        {"error_code": "X3", "tier": "T3", "gravity_linguistic": 0.8},
        {"error_code": "X4", "tier": "T3", "gravity_linguistic": 0.8},
    ]
    decision = arbitrate_dosage("A1", errors)
    assert decision.budget == 1
    assert len(decision.to_correct) == 1
    assert len(decision.silenced_for_spaced_retrieval) == 3
    assert decision.saturated is True


def test_arbitrate_t1_never_in_silenced_for_retrieval():
    # T1 errors are silently dropped, NOT queued for spaced retrieval
    errors = [
        {"error_code": "X1", "tier": "T1", "gravity_linguistic": 0.3},
        {"error_code": "X2", "tier": "T2", "gravity_linguistic": 0.6},
    ]
    decision = arbitrate_dosage("A1", errors)
    silenced_codes = [e["error_code"] for e in decision.silenced_for_spaced_retrieval]
    assert "X1" not in silenced_codes


def test_arbitrate_t2_low_gravity_skipped():
    """T2 included only if gravity_linguistic >= 0.5 and budget remains."""
    errors = [
        {"error_code": "X1", "tier": "T2", "gravity_linguistic": 0.2},
        {"error_code": "X2", "tier": "T2", "gravity_linguistic": 0.6},
    ]
    decision = arbitrate_dosage("B1", errors)
    codes = [e["error_code"] for e in decision.to_correct]
    assert "X2" in codes
    assert "X1" not in codes  # low gravity skipped


def test_arbitrate_priority_t4_t3_t2():
    errors = [
        {"error_code": "T2_a", "tier": "T2", "gravity_linguistic": 0.6},
        {"error_code": "T4_x", "tier": "T4", "gravity_linguistic": 0.8},
        {"error_code": "T3_y", "tier": "T3", "gravity_linguistic": 0.8},
    ]
    decision = arbitrate_dosage("B1", errors)  # budget 3
    codes = [e["error_code"] for e in decision.to_correct]
    # T4 first
    assert codes[0] == "T4_x"
    # T3 second
    assert codes[1] == "T3_y"
    # T2 third
    assert codes[2] == "T2_a"


# ── Tier → feedback type mapping (with diversity + gravity) ─────────


def test_tier_to_feedback_default_t2_recast():
    assert tier_to_feedback_type("T2", "verb_tense") == "implicit_recast"


def test_tier_to_feedback_default_t3_elicitation():
    assert tier_to_feedback_type("T3", "verb_tense") == "elicitation"


def test_tier_to_feedback_default_t4_prompt():
    assert tier_to_feedback_type("T4", "verb_tense") == "prompt_plus_remediation"


def test_tier_to_feedback_t1_silent():
    assert tier_to_feedback_type("T1", "verb_tense") == "silent"


def test_diversity_rule_switches_after_two_elicitations():
    history = {"verb_tense": ["elicitation", "elicitation"]}
    assert tier_to_feedback_type("T3", "verb_tense", last_feedback_per_family=history) == "metalinguistic"


def test_diversity_rule_switches_after_two_metalinguistic():
    history = {"verb_tense": ["metalinguistic", "metalinguistic"]}
    assert tier_to_feedback_type("T3", "verb_tense", last_feedback_per_family=history) == "elicitation"


def test_diversity_rule_no_switch_after_one():
    history = {"verb_tense": ["elicitation"]}
    assert tier_to_feedback_type("T3", "verb_tense", last_feedback_per_family=history) == "elicitation"


def test_gravity_communicative_upgrades_t1_to_recast():
    """If gravity_communicative >= 0.7 + tier T1, upgrade to T2 → implicit_recast."""
    result = tier_to_feedback_type(
        "T1", "sentence",
        gravity={"communicative": 0.85}
    )
    assert result == "implicit_recast"


def test_gravity_social_upgrades_t2_to_elicitation():
    """If gravity_social >= 0.6 + tier T2, upgrade to T3 → elicitation."""
    result = tier_to_feedback_type(
        "T2", "discourse",
        gravity={"social": 0.7}
    )
    assert result == "elicitation"


def test_gravity_no_upgrade_when_threshold_below():
    result = tier_to_feedback_type("T1", "x", gravity={"communicative": 0.5})
    assert result == "silent"


# ── Anti-drift triggers ──────────────────────────────────────────────


def test_level_reminder_every_5_turns():
    assert should_inject_level_reminder(0) is False
    assert should_inject_level_reminder(1) is False
    assert should_inject_level_reminder(4) is False
    assert should_inject_level_reminder(5) is True
    assert should_inject_level_reminder(10) is True
    assert should_inject_level_reminder(15) is True
    assert should_inject_level_reminder(7) is False


def test_drift_check_every_10_turns():
    assert should_request_drift_check(0) is False
    assert should_request_drift_check(5) is False
    assert should_request_drift_check(10) is True
    assert should_request_drift_check(20) is True
    assert should_request_drift_check(13) is False


def test_build_level_reminder_contains_level():
    reminder = build_level_reminder("B1")
    assert "B1" in reminder
    assert "LEVEL REMINDER" in reminder


def test_build_drift_check_request_contains_self_grade():
    req = build_drift_check_request()
    assert "drift_self_grade" in req
    assert "compliant" in req


# ── L1 transfer hook (Phase 6) ───────────────────────────────────────


def test_l1_watch_empty_when_no_l1():
    assert build_l1_watch(None) == ""


def test_l1_watch_empty_when_unknown_l1():
    assert build_l1_watch("xx") == ""


def test_l1_watch_fr_en_includes_top_3_families():
    block = build_l1_watch("fr", target_lang="en", top_n=3)
    assert "L1 WATCH" in block
    assert "fr" in block
    # Should mention top families by multiplier
    assert "articles" in block
    assert "prepositions" in block
    assert "false_friends" in block


def test_l1_watch_top_n_respected():
    block = build_l1_watch("fr", top_n=2)
    # Count bullet lines (start with "  -")
    bullets = [line for line in block.split("\n") if line.strip().startswith("- ")]
    assert len(bullets) == 2


def test_l1_watch_renders_language_names():
    """Phase 7 tuning — prose should use English names, not ISO codes."""
    block = build_l1_watch("fr", target_lang="en")
    assert "French" in block, "l1 name should be spelled out"
    assert "English" in block, "target lang name should be spelled out"
    assert "In French we say" in block, "EXPLICIT_CONTRAST example should use name"
    assert "(fr)" in block, "code should still appear once parenthetically"


def test_l1_watch_unknown_code_falls_back():
    """Unknown ISO code (not in L1_NAMES) should render the code verbatim, not crash."""
    from academie_core.pedagogy.teacher_prompt import L1_TRANSFER_SEED
    # Inject a dummy transfer for an unmapped code.
    L1_TRANSFER_SEED.setdefault("xy", {})["en"] = [("articles", 1.0, "dummy")]
    try:
        block = build_l1_watch("xy", target_lang="en")
        assert "xy" in block
    finally:
        L1_TRANSFER_SEED.pop("xy", None)


# ── Spaced retrieval (Phase 7) ──────────────────────────────────────


def test_spaced_retrieval_empty_when_no_items():
    assert build_spaced_retrieval_block([]) == ""


def test_spaced_retrieval_renders_items():
    items = [
        {"concept_key": "past_simple_irregular", "last_error_summary": "struggled with goed/taked"},
        {"concept_key": "articles", "last_error_summary": "missing 'a' in 'I am student'"},
    ]
    block = build_spaced_retrieval_block(items)
    assert "AUJOURD'HUI" in block
    assert "past_simple_irregular" in block
    assert "articles" in block


# ── Few-shots selection ──────────────────────────────────────────────


@pytest.mark.parametrize("level", LEVELS)
def test_select_fewshots_returns_for_every_level(level):
    fewshots = select_fewshots(level, max_examples=3)
    assert len(fewshots) >= 1


def test_fewshots_diversity_of_types():
    """Should pick examples with different feedback types when possible."""
    fewshots = select_fewshots("B1", max_examples=3)
    types = [fs["type"] for fs in fewshots]
    # Should have at least 2 distinct types
    assert len(set(types)) >= 2


def test_render_fewshots_block_includes_learner_and_teacher():
    block = render_fewshots_block("B1", max_examples=2)
    assert "Learner:" in block
    assert "Teacher:" in block
    assert "FEW-SHOT EXAMPLES" in block


# ── JSON output parsing ─────────────────────────────────────────────


def test_parse_valid_json_response():
    raw = """
Some preamble that should be ignored.

<output>
{
  "reasoning": "T2 V:TENSE on verb_tense → recast.",
  "feedback": "Oh you went to Paris! What did you do there?",
  "tier_applied": ["T2"],
  "feedback_types": ["implicit_recast"],
  "error_codes": ["V:TENSE"],
  "dosage_check": "1/3",
  "silenced_for_spaced_retrieval": [],
  "drift_self_grade": "not_checked",
  "level_reinjected": false
}
</output>

Trailing junk.
"""
    parsed = parse_teacher_response(raw)
    assert parsed.parse_ok is True
    assert parsed.feedback == "Oh you went to Paris! What did you do there?"
    assert parsed.tier_applied == ["T2"]
    assert parsed.feedback_types == ["implicit_recast"]
    assert parsed.error_codes == ["V:TENSE"]


def test_parse_legacy_no_output_tags():
    raw = "Just a plain Teacher response without tags."
    parsed = parse_teacher_response(raw)
    assert parsed.parse_ok is False
    assert parsed.feedback == "Just a plain Teacher response without tags."


def test_parse_malformed_json_falls_back():
    raw = "<output>{not valid json</output>"
    parsed = parse_teacher_response(raw)
    assert parsed.parse_ok is False
    # Falls back to text outside tags (which is empty here)
    assert parsed.feedback in ("", raw)


def test_parse_drift_grade_default():
    raw = '<output>{"feedback": "ok"}</output>'
    parsed = parse_teacher_response(raw)
    assert parsed.drift_self_grade == "not_checked"


# ── update_feedback_history ─────────────────────────────────────────


def test_history_appends_per_family():
    history = {}
    family_lookup = {"V:TENSE": "verb_tense", "PREP": "preposition"}
    out = update_feedback_history(
        history,
        error_codes=["V:TENSE", "PREP"],
        feedback_types=["elicitation", "implicit_recast"],
        family_lookup=family_lookup,
    )
    assert out["verb_tense"] == ["elicitation"]
    assert out["preposition"] == ["implicit_recast"]


def test_history_caps_at_4():
    history = {"verb_tense": ["a", "b", "c", "d", "e"]}
    out = update_feedback_history(
        history,
        error_codes=["V:TENSE"],
        feedback_types=["f"],
        family_lookup={"V:TENSE": "verb_tense"},
        cap=4,
    )
    assert len(out["verb_tense"]) == 4
    assert out["verb_tense"] == ["c", "d", "e", "f"]


# ── End-to-end: build_dynamic_sections ──────────────────────────────


def test_build_dynamic_sections_basic():
    ctx = PromptContext(
        level="B1",
        turn_count=3,
        errors_detected=[
            {"error_code": "V:TENSE", "family": "verb_tense", "tier": "T3", "gravity_linguistic": 0.8},
        ],
        l1=None,
    )
    sections = build_dynamic_sections(ctx)
    assert "RUBRIC B1" in sections["rubric_for_level"]
    assert "DOSAGE THIS TURN" in sections["dosage_block"]
    assert "Budget for B1: max 3" in sections["dosage_block"]
    assert sections["level_reminder_inject"] == ""  # turn 3 not divisible by 5
    assert sections["drift_validation_request"] == ""  # turn 3 not divisible by 10
    assert sections["l1_watch"] == ""  # no L1 set
    assert sections["spaced_retrieval_today"] == ""  # no items


def test_build_dynamic_sections_turn_5_injects_reminder():
    ctx = PromptContext(level="A1", turn_count=5, errors_detected=[])
    sections = build_dynamic_sections(ctx)
    assert "LEVEL REMINDER" in sections["level_reminder_inject"]


def test_build_dynamic_sections_turn_10_requests_drift_check():
    ctx = PromptContext(level="B2", turn_count=10, errors_detected=[])
    sections = build_dynamic_sections(ctx)
    assert "LEVEL REMINDER" in sections["level_reminder_inject"]  # also turn % 5 == 0
    assert "DRIFT SELF-CHECK" in sections["drift_validation_request"]


def test_build_dynamic_sections_l1_fr_includes_watch():
    ctx = PromptContext(level="C1", turn_count=2, errors_detected=[], l1="fr")
    sections = build_dynamic_sections(ctx)
    assert "L1 WATCH" in sections["l1_watch"]
    assert "fr" in sections["l1_watch"]


def test_build_dynamic_sections_with_spaced_retrieval():
    ctx = PromptContext(
        level="A2",
        turn_count=1,
        spaced_retrieval_due=[{"concept_key": "past_irregular", "last_error_summary": "x"}],
    )
    sections = build_dynamic_sections(ctx)
    assert "AUJOURD'HUI" in sections["spaced_retrieval_today"]
    assert "past_irregular" in sections["spaced_retrieval_today"]
