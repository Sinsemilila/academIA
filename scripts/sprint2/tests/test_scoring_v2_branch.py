"""Sprint 2 Phase B3 — compute_error_profile honours row["tier"] when flag on.

Covers:
- Flag off (v1 default): tier derived from matrix[family][band], row.tier ignored
- Flag on + row.tier populated: family tier taken from stored T-code (majority)
- Flag on + row.tier NULL: falls back to matrix lookup (legacy rows)
- Flag on + override cell (sentence × beginner): row.tier reflects the override
"""
from __future__ import annotations

import importlib
import sys

import pytest

# Ensure webapp backend importable
_BACKEND = "/opt/academie/webapp/backend"
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


@pytest.fixture
def scoring_mod():
    from app.error_taxonomy import scoring as s
    # Reset cached matrix so USE_V2_TOLERANCE env effect stays deterministic
    s._matrix = None
    return importlib.reload(s)


def _mk_rows(pairs):
    """pairs: list of (error_code, tier_code_or_None)"""
    return [
        {"error_code": c, "turn_number": i, "session_id": f"s{i}", "tier": t}
        for i, (c, t) in enumerate(pairs)
    ]


def test_flag_off_uses_matrix_lookup(scoring_mod, monkeypatch):
    monkeypatch.setattr(scoring_mod, "_USE_V2_SCORING", False)
    # Even if the row carries T3 (penalized), flag-off must yield the matrix lookup value,
    # whatever it is for the currently-loaded yaml. We compare against the canonical lookup.
    m = scoring_mod._load_matrix()
    expected = m["matrix"]["verb_tense"][scoring_mod.get_band_for_level("B1")]
    rows = _mk_rows([("V:TENSE", "T3"), ("V:TENSE", "T3")])
    prof = scoring_mod.compute_error_profile(rows, "B1")
    assert prof["families"]["verb_tense"]["tier"] == expected


def test_flag_on_reads_row_tier(scoring_mod, monkeypatch):
    monkeypatch.setattr(scoring_mod, "_USE_V2_SCORING", True)
    # Row tier T3 = "penalized". Matrix for V:TENSE@B1 would say "ignored" — flag-on should use T3.
    rows = _mk_rows([("V:TENSE", "T3"), ("V:TENSE", "T3")])
    prof = scoring_mod.compute_error_profile(rows, "B1")
    assert prof["families"]["verb_tense"]["tier"] == "penalized"


def test_flag_on_majority_wins(scoring_mod, monkeypatch):
    monkeypatch.setattr(scoring_mod, "_USE_V2_SCORING", True)
    # 2 × T2 (noted) vs 1 × T3 (penalized) → majority "noted"
    rows = _mk_rows([("V:TENSE", "T2"), ("V:TENSE", "T2"), ("V:TENSE", "T3")])
    prof = scoring_mod.compute_error_profile(rows, "B1")
    assert prof["families"]["verb_tense"]["tier"] == "noted"


def test_flag_on_null_tier_falls_back_to_matrix(scoring_mod, monkeypatch):
    monkeypatch.setattr(scoring_mod, "_USE_V2_SCORING", True)
    m = scoring_mod._load_matrix()
    expected = m["matrix"]["verb_tense"][scoring_mod.get_band_for_level("B1")]
    rows = _mk_rows([("V:TENSE", None), ("V:TENSE", None)])
    prof = scoring_mod.compute_error_profile(rows, "B1")
    assert prof["families"]["verb_tense"]["tier"] == expected


def test_flag_on_respects_override_cell(scoring_mod, monkeypatch):
    """SENT:FRAG × beginner is overridden to 'noted' (T2) even though v2 baseline is penalized.
    If a row stored T2, flag-on should reflect that."""
    monkeypatch.setattr(scoring_mod, "_USE_V2_SCORING", True)
    rows = _mk_rows([("SENT:FRAG", "T2")])
    prof = scoring_mod.compute_error_profile(rows, "A1")
    assert prof["families"]["sentence"]["tier"] == "noted"
