"""Unit tests for Session 37 consolidation bubble templates + new
msg_validation_after_failed_exam helper.
"""
from __future__ import annotations

import pytest

from academie_core.pedagogy.consolidation import (
    bubble_template,
    msg_validation_after_failed_exam,
    _BUBBLE_TEMPLATES_BY_L1,
)


# ── bubble_template L1 dispatch ────────────────────────────────────────


def test_bubble_all_five_kinds_fr_returns_non_empty():
    for kind in (
        "auto_validate_match",
        "auto_validate_after_failed_exam",
        "upgrade_accepted",
        "downgrade_accepted",
        "stay_current",
    ):
        msg = bubble_template(kind, "fr", level="A1", tested_level="A2")
        assert msg, f"empty FR template for {kind}"
        assert "A1" in msg or "a1" in msg.lower(), f"level missing in {kind}"


def test_bubble_falls_back_to_fr_for_unknown_l1():
    msg_fr = bubble_template("auto_validate_match", "fr", level="B1")
    msg_unknown = bubble_template("auto_validate_match", "xx", level="B1")
    assert msg_fr == msg_unknown, "unknown L1 should fall back to FR"


def test_bubble_falls_back_to_fr_for_none_l1():
    msg = bubble_template("auto_validate_match", None, level="A2")
    assert msg  # Not empty — FR fallback


def test_bubble_failed_exam_mentions_tested_level():
    msg = bubble_template(
        "auto_validate_after_failed_exam", "fr",
        level="A1", tested_level="A2",
    )
    assert "A1" in msg
    assert "A2" in msg


def test_bubble_unknown_kind_returns_empty():
    msg = bubble_template("nonexistent_kind", "fr", level="A1")  # type: ignore[arg-type]
    assert msg == ""


def test_bubble_case_insensitive_l1():
    a = bubble_template("auto_validate_match", "FR", level="A1")
    b = bubble_template("auto_validate_match", "fr", level="A1")
    assert a == b


def test_fr_templates_cover_all_five_kinds():
    expected = {
        "auto_validate_match",
        "auto_validate_after_failed_exam",
        "upgrade_accepted",
        "downgrade_accepted",
        "stay_current",
    }
    assert set(_BUBBLE_TEMPLATES_BY_L1["fr"].keys()) == expected


# ── msg_validation_after_failed_exam ────────────────────────────────────


def test_failed_exam_msg_mentions_both_levels_and_turns():
    msg = msg_validation_after_failed_exam(n_turns=8, qcm_level="A1", tested_level="A2")
    assert "8" in msg
    assert "A1" in msg
    assert "A2" in msg


def test_failed_exam_msg_is_distinct_from_msg_validation():
    from academie_core.pedagogy.consolidation import msg_validation
    msg_fail = msg_validation_after_failed_exam(8, "A1", "A2")
    msg_match = msg_validation(8, "A1")
    assert msg_fail != msg_match, "failed-exam should not reuse the match message"
    # The failed-exam message should NOT claim "tes auto-évaluations étaient justes"
    assert "auto-évaluations étaient justes" not in msg_fail
    # The failed-exam message SHOULD mention the tested level explicitly
    assert "A2" in msg_fail
