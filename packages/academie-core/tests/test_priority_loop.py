"""Unit tests for priority_loop.compute_priority_concepts."""
from __future__ import annotations

from datetime import date

import pytest

from academie_core.pedagogy.priority_loop import (
    compute_priority_concepts,
    _time_factor,
    _days_since,
)


TODAY = date(2026, 4, 21)


# ── Time factor monotonicity ───────────────────────────────────────────

def test_time_factor_null_is_one():
    assert _time_factor(None) == 1.0
    assert _time_factor(0) == 1.0


def test_time_factor_monotonic_increasing():
    assert _time_factor(7) < _time_factor(14)
    assert _time_factor(14) < _time_factor(30)
    assert _time_factor(30) < _time_factor(100)


def test_time_factor_reasonable_plateau():
    # At J+100 should be under 5 (not exploding)
    assert _time_factor(100) < 5.0
    # At J+7 formula = 1 + sqrt(1) = 2.0
    assert _time_factor(7) == pytest.approx(2.0)
    # At J+28 = 1 + sqrt(4) = 3.0
    assert _time_factor(28) == pytest.approx(3.0)


# ── _days_since ────────────────────────────────────────────────────────

def test_days_since_parses_iso():
    assert _days_since("2026-04-14", TODAY) == 7
    assert _days_since("2026-04-21", TODAY) == 0


def test_days_since_tolerates_invalid():
    assert _days_since(None, TODAY) is None
    assert _days_since("", TODAY) is None
    assert _days_since("not a date", TODAY) is None


# ── compute_priority_concepts core behaviour ──────────────────────────

def test_empty_concept_keys_returns_empty():
    assert compute_priority_concepts({}, [], {}, TODAY) == []


def test_nominal_overdue_weak_wins():
    sc = {
        "c_fresh": {"score": 50, "last_seen": "2026-04-21"},  # today
        "c_overdue": {"score": 50, "last_seen": "2026-03-21"},  # 31 days ago
        "c_mastered": {"score": 100, "last_seen": "2026-04-20"},
    }
    keys = ["c_fresh", "c_overdue", "c_mastered"]
    weights = {"c_fresh": 5, "c_overdue": 5, "c_mastered": 5}
    out = compute_priority_concepts(sc, keys, weights, TODAY, limit=3)
    # c_mastered filtered out (priority ~0), c_overdue top
    assert out[0]["concept_key"] == "c_overdue"
    assert "pas revu depuis 31 jours" in out[0]["reason"]


def test_untested_concepts_surface_by_weight():
    # All untested, weights differ → highest weight ranks first
    sc = {}
    keys = ["c_light", "c_heavy", "c_medium"]
    weights = {"c_light": 3, "c_heavy": 8, "c_medium": 5}
    out = compute_priority_concepts(sc, keys, weights, TODAY, limit=3)
    assert out[0]["concept_key"] == "c_heavy"
    assert out[0]["score"] == 0
    assert out[0]["days_since_last_seen"] is None


def test_full_mastery_returns_empty():
    sc = {k: {"score": 100, "last_seen": "2026-04-21"} for k in ("a", "b", "c")}
    keys = ["a", "b", "c"]
    weights = {"a": 5, "b": 5, "c": 5}
    out = compute_priority_concepts(sc, keys, weights, TODAY)
    assert out == []  # all filtered by priority_score > 0.05


def test_scores_confiance_empty_falls_back_to_untested_weighted():
    # Fresh ES learner — no scores_confiance yet
    sc = {}
    keys = ["genero", "ser_estar", "presente"]
    weights = {"genero": 5, "ser_estar": 8, "presente": 5}
    out = compute_priority_concepts(sc, keys, weights, TODAY, limit=3)
    assert len(out) == 3
    assert out[0]["concept_key"] == "ser_estar"
    assert all(c["days_since_last_seen"] is None for c in out)


def test_monotonicity_older_ranks_higher():
    sc = {
        "c_j7": {"score": 60, "last_seen": "2026-04-14"},
        "c_j30": {"score": 60, "last_seen": "2026-03-22"},
    }
    keys = ["c_j7", "c_j30"]
    weights = {"c_j7": 5, "c_j30": 5}
    out = compute_priority_concepts(sc, keys, weights, TODAY)
    assert out[0]["concept_key"] == "c_j30"
    assert out[0]["priority_score"] > out[1]["priority_score"]


def test_tolerates_legacy_bare_number_scores():
    # If scores_confiance is in old format {concept: number} instead of {concept: {score: ...}}
    sc = {"c1": 40, "c2": 80}
    keys = ["c1", "c2"]
    weights = {"c1": 5, "c2": 5}
    out = compute_priority_concepts(sc, keys, weights, TODAY)
    # c1 has deficit 0.6, c2 has 0.2 → c1 ranks higher
    assert out[0]["concept_key"] == "c1"


def test_tolerates_missing_weights_uses_default():
    # No weights provided — all concepts use default weight_norm=0.5
    sc = {"c1": {"score": 30, "last_seen": "2026-04-10"},
          "c2": {"score": 60, "last_seen": "2026-04-10"}}
    out = compute_priority_concepts(sc, ["c1", "c2"], {}, TODAY)
    # c1 lower score → higher deficit → higher priority
    assert out[0]["concept_key"] == "c1"


def test_limit_respected():
    sc = {}
    keys = [f"c{i}" for i in range(10)]
    weights = {k: 5 for k in keys}
    out = compute_priority_concepts(sc, keys, weights, TODAY, limit=3)
    assert len(out) == 3


def test_reason_explains_staleness():
    sc = {"c_old": {"score": 40, "last_seen": "2026-03-01"}}  # 51 days
    out = compute_priority_concepts(sc, ["c_old"], {"c_old": 5}, TODAY)
    assert "51 jours" in out[0]["reason"]
    assert "score faible" in out[0]["reason"]


def test_reason_never_seen():
    out = compute_priority_concepts({}, ["new_concept"], {"new_concept": 5}, TODAY)
    assert "pas encore vu" in out[0]["reason"]


def test_priority_score_range_sanity():
    sc = {"c": {"score": 0, "last_seen": "2025-04-21"}}  # 1 year ago, untested
    out = compute_priority_concepts(sc, ["c"], {"c": 10}, TODAY)
    # Max weight_norm (1.0) × tf (~8) × deficit (1.0) ≈ 8 worst-case
    assert 0 <= out[0]["priority_score"] < 10
