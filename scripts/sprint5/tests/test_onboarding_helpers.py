"""Unit tests for onboarding_router helpers — no DB, no API.

Run : python3 scripts/sprint5/tests/test_onboarding_helpers.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make backend importable without Docker
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "webapp" / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "packages" / "academie-core"))


from app.routers.onboarding_router import (  # noqa: E402
    LearnerProfileSubmit,
    UniversalBlock,
    DomainLevelSubmit,
    DomainMotivationSubmit,
    _score_goal_specificity,
    _score_probe,
    _compute_derivations,
    _compute_tutor_hints,
    _render_nl_summary,
    _cefr_min,
    _cefr_max,
    _cefr_step,
)


def test_cefr_ladder():
    assert _cefr_min("A1", "B2") == "A1"
    assert _cefr_max("A1", "B2") == "B2"
    assert _cefr_step("B2", -1) == "B1"
    assert _cefr_step("A1", -1) == "A1"  # floor
    assert _cefr_step("C1", 2) == "C2"   # ceiling


def test_goal_specificity_scores():
    assert _score_goal_specificity("progresser") == 0
    assert _score_goal_specificity("progresser et apprendre") == 0  # vague only
    assert _score_goal_specificity("parler avec mes amis au boulot") == 1  # context
    assert _score_goal_specificity("comprendre Netflix en VO") in (2, 3)  # entity
    assert _score_goal_specificity("passer le DELE B2 en juin") == 3       # entity + temporal
    assert _score_goal_specificity("xx") == 0  # too short


def test_probe_score_en_strong():
    overlay_en = {
        "accepted_variants_regex": {
            "strong": r"(?i)(if i had known|had i known).*(you were coming).*(would have (prepared|made))",
            "medium": r"(?i)(if i (knew|had known)).*(coming).*(would (have )?(prepared|made))",
            "weak": r"(?i)(if i know|knew).*(come|coming).*(prepare|make)",
        }
    }
    strong = "If I had known you were coming, I would have prepared a meal."
    medium = "If I knew you were coming, I would have made something."
    weak = "If I know you come, I prepare food."
    score, hit = _score_probe(strong, overlay_en)
    assert score == 3 and hit, f"strong scored {score}"
    score, hit = _score_probe(medium, overlay_en)
    assert score == 2 and hit, f"medium scored {score}"
    score, hit = _score_probe(weak, overlay_en)
    assert score == 1 and hit, f"weak scored {score}"
    score, hit = _score_probe(None, overlay_en)
    assert score == 0 and not hit
    score, hit = _score_probe("", overlay_en)
    assert score == 0 and not hit


def _make_submit(
    cefr_comp="A2", cefr_prod="A2", self_eff=3, mindset="growth",
    goal="voyager en Espagne cet été", autonomy="semi_autonomous",
    engagement="daily_short", probe=None,
    tags=None, fla=None,
):
    return LearnerProfileSubmit(
        universal_block=UniversalBlock(
            self_efficacy=self_eff,
            mindset=mindset,
            goal_text=goal,
            autonomy_pref=autonomy,
            engagement_pattern=engagement,
        ),
        domain_level=DomainLevelSubmit(
            cefr_comprehension=cefr_comp,
            cefr_production=cefr_prod,
            probe_answer=probe,
        ),
        domain_motivation=DomainMotivationSubmit(
            ideal_l2_self_tags=tags or ["daily_communication"],
            fla_items_raw=fla or {"fla_a": 3, "fla_b": 3, "fla_c": 3},
        ),
    )


def test_derivations_baseline_A2():
    s = _make_submit()
    d = _compute_derivations(s, None)
    assert d["domain_level"]["cefr_baseline"] == "A2"
    assert d["domain_level"]["cefr_final"] == "A2"
    assert d["domain_level"]["cefr_placement"] == "A1"  # -1 step
    assert d["domain_level"]["probe_flag"] is False


def test_derivations_probe_reveals_overconfidence():
    overlay_probe = {
        "accepted_variants_regex": {
            "strong": r"impossible",
            "medium": r"impossible2",
            "weak": r"impossible3",
        }
    }
    # User claims B2 bi-skill but probe answer doesn't match
    s = _make_submit(cefr_comp="B2", cefr_prod="B2", probe="foo bar")
    d = _compute_derivations(s, overlay_probe)
    assert d["domain_level"]["probe_score"] == 0
    assert d["domain_level"]["cefr_final"] == "B1"  # Dunning-Kruger correction
    assert d["domain_level"]["probe_flag"] is True


def test_derivations_probe_reveals_underestimation():
    overlay = {
        "accepted_variants_regex": {
            "strong": r"(?i)good answer",
            "medium": r"(?i)ok",
            "weak": r"(?i)tryyy",
        }
    }
    s = _make_submit(cefr_comp="A1", cefr_prod="A1", probe="this is a good answer")
    d = _compute_derivations(s, overlay)
    assert d["domain_level"]["probe_score"] == 3
    assert d["domain_level"]["cefr_final"] == "B1"  # correction upward


def test_fla_category_bins():
    for fla_a, fla_b, fla_c, expected in [
        (1, 1, 1, "low"),
        (2, 3, 3, "moderate"),
        (5, 5, 5, "high"),
        (3, 4, 5, "high"),  # mean 4.0
    ]:
        s = _make_submit(fla={"fla_a": fla_a, "fla_b": fla_b, "fla_c": fla_c})
        d = _compute_derivations(s, None)
        assert d["domain_motivation"]["fla_category"] == expected, \
            f"{fla_a},{fla_b},{fla_c} → {d['domain_motivation']['fla_category']} vs {expected}"


def test_tutor_hints_high_anxiety_boosts_scaffold():
    s = _make_submit(self_eff=5, fla={"fla_a": 5, "fla_b": 5, "fla_c": 5})
    d = _compute_derivations(s, None)
    hints = _compute_tutor_hints(s, d)
    # self_eff=5 normally → low scaffold ; high FLA bumps to medium
    assert hints["scaffolding_level"] == "medium"
    assert hints["allow_speaking_day1"] is False
    assert hints["feedback_framing"] == "gentle"


def test_tutor_hints_autonomy_to_style():
    for pref, style in [("guided", "prescriptive"),
                         ("semi_autonomous", "collaborative"),
                         ("autonomous", "adaptive")]:
        s = _make_submit(autonomy=pref)
        d = _compute_derivations(s, None)
        hints = _compute_tutor_hints(s, d)
        assert hints["tutor_style"] == style


def test_nl_summary_under_200_words():
    s = _make_submit(goal="parler avec ma belle-famille en espagnol d'ici juin")
    d = _compute_derivations(s, None)
    hints = _compute_tutor_hints(s, d)
    summary = _render_nl_summary(s, d, hints, "espagnol")
    word_count = len(summary.split())
    assert word_count <= 200, f"summary too long: {word_count} words"
    assert "espagnol" in summary
    assert "A1" in summary  # placement shown


def test_nl_summary_deterministic():
    s = _make_submit()
    d = _compute_derivations(s, None)
    hints = _compute_tutor_hints(s, d)
    s1 = _render_nl_summary(s, d, hints, "anglais")
    s2 = _render_nl_summary(s, d, hints, "anglais")
    assert s1 == s2


# ── Runner ────────────────────────────────────────────────
def run():
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    failed = []
    for t in tests:
        try:
            t()
            print(f"  OK   {t.__name__}")
        except AssertionError as e:
            failed.append((t.__name__, str(e)))
            print(f"  FAIL {t.__name__}  {e}")
        except Exception as e:
            failed.append((t.__name__, f"{type(e).__name__}: {e}"))
            print(f"  ERR  {t.__name__}  {type(e).__name__}: {e}")
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(run())
