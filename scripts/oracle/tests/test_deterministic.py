"""Session 40 Phase B1 — tests for deterministic judges."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from oracle.judges.deterministic import (  # noqa: E402
    _count_lines,
    _count_questions,
    _l2_word_ratio,
    _score_cf_move_partial,
    _score_recast_saliency,
)
from oracle.schemas import ScenarioSchema  # noqa: E402


def _scenario(cefr="A1", max_lines=5, max_questions=2, mini_lesson_allowed=False,
              forbidden=None, l2_band=None):
    spec = {
        "recast_saliency_and_dosage": {
            "max_lines": max_lines,
            "max_questions": max_questions,
            "mini_lesson_allowed": mini_lesson_allowed,
        },
        "cf_move_set_valid": {
            "forbidden": forbidden or [],
            "acceptable": [],
        },
    }
    if l2_band:
        spec["scaffolding_flags_honored"] = {"l2_ratio_band": l2_band}
    return ScenarioSchema.model_validate({
        "id": "sc_test",
        "source": "handcrafted",
        "scenario_key": {"agent": "teacher_en", "cefr": cefr, "target_tier": "T2",
                         "error_category": "verb_tense", "fla": "low"},
        "turns": [{"role": "learner", "text": "yesterday I go", "turn_number": 5}],
        "expected_dimensions": spec,
    })


def test_count_lines_counts_nonblank():
    assert _count_lines("one\n\ntwo\nthree\n") == 3


def test_count_questions_excludes_json():
    txt = "Did you go there?\n<output>{\"x\":\"a?b\"}</output>"
    assert _count_questions(txt) == 1


def test_l2_ratio_english_heavy():
    r = _l2_word_ratio("Yesterday I went to the market and saw many friends.", "en")
    assert r > 0.9


def test_l2_ratio_french_heavy():
    r = _l2_word_ratio("Tu as bien travaillé aujourd'hui.", "en")
    assert r < 0.5  # mostly FR words


def test_recast_lines_under_budget():
    sc = _scenario(max_lines=5, max_questions=2)
    v = _score_recast_saliency(sc, "One line.\nTwo.\nThree.\nFour.")
    assert v.verdict == "pass"


def test_recast_lines_over_budget():
    sc = _scenario(max_lines=2, max_questions=2)
    v = _score_recast_saliency(sc, "One\nTwo\nThree\nFour")
    assert v.verdict == "fail"
    assert "lines=4" in v.reasoning


def test_recast_too_many_questions():
    sc = _scenario(max_lines=5, max_questions=1)
    v = _score_recast_saliency(sc, "A? B? Fine.")
    assert v.verdict == "fail"


def test_recast_micro_lesson_marker_disallowed():
    sc = _scenario(max_lines=5, max_questions=2, mini_lesson_allowed=False)
    v = _score_recast_saliency(sc, "=== MICRO-LEÇON CIBLÉE === present.\nLine.")
    assert v.verdict == "fail"


def test_cf_metalinguistic_flagged():
    sc = _scenario(forbidden=["metalinguistic"])
    v = _score_cf_move_partial(sc, "The past simple is formed with -ed.")
    assert v.verdict == "fail"
    assert "metalinguistic" in v.reasoning


def test_cf_explicit_correction_flagged():
    sc = _scenario(forbidden=["explicit_correction"])
    v = _score_cf_move_partial(sc, "You should say 'went' instead of 'goed'.")
    assert v.verdict == "fail"


def test_cf_clean_response_unknown():
    sc = _scenario(forbidden=["metalinguistic"])
    # Bot implicit recast, no metalinguistic trigger → defer to LLM
    v = _score_cf_move_partial(sc, "Ah, you went to the park! What did you see?")
    assert v.verdict == "unknown"
