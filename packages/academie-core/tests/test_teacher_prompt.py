"""Session 45 P2 — per-CEFR-level tier→feedback mapping.

Regression lockdown : A1 T3 must NEVER surface metalinguistic or
elicitation (rubric HARD BAN). This was the bug Session 44 κ calibration
caught : 6 A1/A2 scenarios consistently failing cf_move_set_valid.
"""
from __future__ import annotations

import pytest

from academie_core.pedagogy.teacher_prompt import (
    TIER_TO_FEEDBACK_BY_LEVEL,
    TIER_TO_FEEDBACK_DEFAULT,
    tier_to_feedback_type,
)


# ── A1 must stay on implicit_recast / silent / prompt_plus_remediation ──

@pytest.mark.parametrize("tier", ["T0", "T1", "T2", "T3", "T4"])
def test_a1_never_emits_metalinguistic(tier):
    result = tier_to_feedback_type(tier=tier, family="V:TENSE", level="A1")
    assert result != "metalinguistic", f"A1 T{tier} leaked metalinguistic"
    assert result != "elicitation", f"A1 T{tier} leaked elicitation (forbidden per rubric)"


@pytest.mark.parametrize("tier,expected", [
    ("T0", "silent"),
    ("T1", "silent"),
    ("T2", "implicit_recast"),
    ("T3", "implicit_recast"),  # key fix : was "elicitation" (forbidden) before Session 45 P2
    ("T4", "prompt_plus_remediation"),
])
def test_a1_mapping_explicit(tier, expected):
    assert tier_to_feedback_type(tier=tier, family="V:TENSE", level="A1") == expected


# ── A2 allows elicitation + metalinguistic with diversity alternation ──

def test_a2_t3_default_elicitation():
    assert tier_to_feedback_type(tier="T3", family="V:TENSE", level="A2") == "elicitation"


def test_a2_t3_diversity_flips_to_metalinguistic_after_2x_elicitation():
    history = {"V:TENSE": ["elicitation", "elicitation"]}
    result = tier_to_feedback_type(
        tier="T3", family="V:TENSE", level="A2",
        last_feedback_per_family=history,
    )
    assert result == "metalinguistic"


def test_a1_t3_diversity_noop_stays_implicit_recast():
    """A1 has no diversity pair → saturated history doesn't flip anything."""
    history = {"V:TENSE": ["implicit_recast", "implicit_recast"]}
    result = tier_to_feedback_type(
        tier="T3", family="V:TENSE", level="A1",
        last_feedback_per_family=history,
    )
    assert result == "implicit_recast"


# ── C1-C2 tilts metalinguistic at T3 ──

@pytest.mark.parametrize("level", ["C1", "C2"])
def test_c1_c2_t3_defaults_metalinguistic(level):
    assert tier_to_feedback_type(tier="T3", family="V:TENSE", level=level) == "metalinguistic"


# ── Gravity overrides still upgrade tier before level lookup ──

def test_gravity_communicative_upgrades_t1_to_t2_at_a1():
    result = tier_to_feedback_type(
        tier="T1", family="V:TENSE", level="A1",
        gravity={"communicative": 0.8},
    )
    # Upgraded T1 → T2 → implicit_recast at A1
    assert result == "implicit_recast"


def test_gravity_social_upgrades_t2_to_t3_at_a2():
    result = tier_to_feedback_type(
        tier="T2", family="V:TENSE", level="A2",
        gravity={"social": 0.7},
    )
    # Upgraded T2 → T3 → elicitation at A2
    assert result == "elicitation"


# ── Backward-compat : level=None falls back to legacy mapping ──

def test_no_level_falls_back_to_legacy_mapping():
    result = tier_to_feedback_type(tier="T3", family="V:TENSE")  # no level
    assert result == TIER_TO_FEEDBACK_DEFAULT["T3"]  # "elicitation"


# ── Shape invariants ──

def test_all_levels_covered():
    for lvl in ("A1", "A2", "B1", "B2", "C1", "C2"):
        assert lvl in TIER_TO_FEEDBACK_BY_LEVEL
        tiers = TIER_TO_FEEDBACK_BY_LEVEL[lvl]
        assert set(tiers) >= {"T0", "T1", "T2", "T3", "T4"}


def test_a1_bans_elicit_and_metalinguistic_in_mapping():
    """Paranoid check at mapping level before execution."""
    a1 = TIER_TO_FEEDBACK_BY_LEVEL["A1"]
    assert "elicitation" not in a1.values(), "A1 mapping leaks elicitation"
    assert "metalinguistic" not in a1.values(), "A1 mapping leaks metalinguistic"


# ── Anti-pattern contrast examples (P2c) ──

from academie_core.pedagogy.teacher_prompt import render_fewshots_block


@pytest.mark.parametrize("level", ["A1", "A2", "B1"])
def test_fewshots_includes_anti_patterns_at_a1_a2_b1(level):
    """Session 45 P2d — B1 also receives anti-patterns because gpt-4o-mini
    defaults to explicit_correction even at B1."""
    block = render_fewshots_block(level)
    assert "ANTI-PATTERNS" in block
    assert "DO NOT PRODUCE" in block
    assert "❌ WRONG" in block
    assert "✅ CORRECT" in block


@pytest.mark.parametrize("level", ["B2", "C1", "C2"])
def test_fewshots_no_anti_patterns_at_b2plus(level):
    """B2+ learners can handle metalinguistic + direct correction —
    no need for anti-pattern shock therapy."""
    block = render_fewshots_block(level)
    assert "ANTI-PATTERNS" not in block
