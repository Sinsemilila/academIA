"""Phase 1.4 — unit tests for Gwet's AC2 implementation."""
from __future__ import annotations

import pytest

from scripts.oracle.kappa.ac2 import (
    AC2Result,
    ac2_binary,
    ac2_with_ci,
    aggregate_per_dim,
    aggregate_global,
)


def test_perfect_agreement():
    """Unanimous votes across all items → AC2 = 1.0."""
    items = [(5, 0), (5, 0), (0, 5), (5, 0), (0, 5)]
    assert ac2_binary(items) == pytest.approx(1.0, abs=1e-6)


def test_max_disagreement_with_4_raters():
    """Perfectly split 2/2 across all items → below chance, AC2 < 0."""
    items = [(2, 2)] * 4
    val = ac2_binary(items)
    assert val < 0  # below chance


def test_skewed_binary_high_agreement():
    """90%+ pass with high agreement → AC2 > 0.8 (paradox-robust).

    Cohen's kappa would be near 0 on this skewed distribution despite
    98% pairwise agreement. Gwet's AC2 correctly reports high agreement.
    """
    items = [(5, 0)] * 9 + [(4, 1)]
    val = ac2_binary(items)
    assert val > 0.8


def test_empty_items():
    """No items → AC2 = 0.0 default."""
    assert ac2_binary([]) == 0.0


def test_single_rater_returns_zero():
    """n_raters < 2 → AC2 undefined, returns 0."""
    items = [(1, 0), (0, 1)]
    assert ac2_binary(items) == 0.0


def test_ci_bounds_are_consistent():
    """CI low ≤ point ≤ CI high (when point is within bootstrap range)."""
    items = [(5, 0)] * 8 + [(4, 1)] * 2
    result = ac2_with_ci(items, n_boot=200, seed=42)
    assert result.ci_low <= result.ac2 + 1e-6
    assert result.ac2 - 1e-6 <= result.ci_high
    assert result.n_items == 10
    assert result.n_raters == 5


def test_aggregate_per_dim():
    """Per-dim aggregation returns dict of AC2Result."""
    verdicts = {
        "cf_move_set_valid": [(5, 0), (4, 1), (5, 0)],
        "register_cefr_alignment": [(3, 2), (5, 0), (4, 1)],
    }
    out = aggregate_per_dim(verdicts, n_boot=100, seed=42)
    assert set(out.keys()) == {"cf_move_set_valid", "register_cefr_alignment"}
    for dim, res in out.items():
        assert isinstance(res, AC2Result)
        assert res.n_items == 3


def test_aggregate_global_flattens():
    """Global aggregation flattens across all dims."""
    verdicts = {
        "dim_a": [(5, 0), (4, 1)],
        "dim_b": [(5, 0), (5, 0)],
    }
    out = aggregate_global(verdicts, n_boot=100, seed=42)
    assert out.n_items == 4


def test_reproducible_with_seed():
    """Same seed → same bootstrap CI."""
    items = [(5, 0)] * 5 + [(4, 1)] * 5
    r1 = ac2_with_ci(items, n_boot=200, seed=42)
    r2 = ac2_with_ci(items, n_boot=200, seed=42)
    assert r1.ci_low == r2.ci_low
    assert r1.ci_high == r2.ci_high
