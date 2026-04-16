"""Sprint 2 B+ — property-based invariants for the scoring engine.

Covers global guarantees that any reasonable `compute_error_profile` +
`enrich_error_fields` implementation should satisfy, generated via
pytest-hypothesis rather than fixed fixtures.

Run with USE_V2_TOLERANCE=true to exercise the empirical matrix — the
properties hold regardless but the v2 yaml is closer to the live config.
"""
from __future__ import annotations

import importlib
import sys
from collections import Counter

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

_BACKEND = "/opt/academie/webapp/backend"
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


@pytest.fixture(scope="module")
def scoring_mod():
    from academie_core.taxonomy import scoring as s
    s._matrix = None
    return importlib.reload(s)


# ── Strategies ──────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def all_codes(scoring_mod):
    m = scoring_mod._load_matrix()
    codes = []
    for defn in m["families"].values():
        codes.extend(defn["codes"])
    return codes


@pytest.fixture(scope="module")
def all_levels():
    return ["A1", "A2", "B1", "B2", "C1", "C2"]


def _row_strat(codes, tier_codes=None):
    """Build a Hypothesis strategy for one error_log row.

    turn_number drawn from [0, 99] — we later rewrite within each test to
    keep max_per_turn cap untouched where required.
    """
    return st.fixed_dictionaries({
        "error_code": st.sampled_from(codes),
        "turn_number": st.integers(min_value=0, max_value=99),
        "session_id": st.sampled_from(["s1", "s2", "s3"]),
        "tier": st.sampled_from(tier_codes) if tier_codes else st.none(),
    })


# ── 1. Tier code ↔ label round-trip ─────────────────────────────────

def test_tier_label_code_round_trip(scoring_mod):
    for label, code in scoring_mod._TIER_LABEL_TO_CODE.items():
        assert scoring_mod._TIER_CODE_TO_LABEL[code] == label
    for code, label in scoring_mod._TIER_CODE_TO_LABEL.items():
        assert scoring_mod._TIER_LABEL_TO_CODE[label] == code


# ── 2. Weights monotonicity ──────────────────────────────────────────

def test_weights_monotone(scoring_mod):
    """Only asserts the order across tiers actually present in the loaded matrix.
    v1 ships without `regressive`; v2 adds it (GLMM-calibrated). The invariant
    is that every consecutive pair in [ignored, noted, penalized, regressive]
    is monotone non-decreasing for whichever tiers exist."""
    w = scoring_mod._load_matrix()["weights"]
    order = [t for t in ("ignored", "noted", "penalized", "regressive") if t in w]
    for a, b in zip(order, order[1:]):
        assert w[a] <= w[b], f"weights not monotone: {a}={w[a]} > {b}={w[b]}"


# ── 3. Band normalization ────────────────────────────────────────────

@given(
    level=st.sampled_from(["A1", "A2", "B1", "B2", "C1", "C2"]),
    pad_l=st.integers(min_value=0, max_value=3),
    pad_r=st.integers(min_value=0, max_value=3),
    upper=st.booleans(),
    plus=st.booleans(),
)
def test_band_lookup_is_case_and_whitespace_stable(scoring_mod, level, pad_l, pad_r, upper, plus):
    variant = level + ("+" if plus else "")
    variant = variant.lower() if not upper else variant
    variant = " " * pad_l + variant + " " * pad_r
    assert scoring_mod.get_band_for_level(variant) == scoring_mod.get_band_for_level(level)


# ── 4. total_errors never exceeds input row count ───────────────────

@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(n_rows=st.integers(min_value=0, max_value=20))
def test_total_errors_bounded_by_rows(scoring_mod, all_codes, n_rows):
    rows = [
        {"error_code": all_codes[i % len(all_codes)], "turn_number": i, "session_id": "s1", "tier": None}
        for i in range(n_rows)
    ]
    prof = scoring_mod.compute_error_profile(rows, "B1")
    assert prof["summary"]["total_errors"] <= n_rows


# ── 5. Row permutation stability (when no turn-cap collision) ───────
# Uniqueness invariant: if every row has a unique (session_id, turn_number),
# the turn cap never triggers, so permuting rows leaves family counts identical.

@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=st.data())
def test_permutation_stable_when_no_turn_collision(scoring_mod, all_codes, data):
    n = data.draw(st.integers(min_value=0, max_value=15))
    codes = [data.draw(st.sampled_from(all_codes)) for _ in range(n)]
    # unique turn_number per row → no (session, turn) cap collision
    rows = [
        {"error_code": codes[i], "turn_number": i, "session_id": "s1", "tier": None}
        for i in range(n)
    ]
    permuted = data.draw(st.permutations(rows))

    p1 = scoring_mod.compute_error_profile(rows, "B1")
    p2 = scoring_mod.compute_error_profile(permuted, "B1")

    for fk in p1["families"]:
        assert p1["families"][fk]["count"] == p2["families"][fk]["count"]
        assert p1["families"][fk]["tier"] == p2["families"][fk]["tier"]
    assert p1["summary"]["total_errors"] == p2["summary"]["total_errors"]


# ── 6. Family isolation ──────────────────────────────────────────────
# Adding rows belonging to family X does not change the count of family Y.

@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=st.data())
def test_family_isolation(scoring_mod, all_codes, data):
    m = scoring_mod._load_matrix()
    # Pick two distinct families
    fams = list(m["families"].keys())
    fa, fb = data.draw(st.tuples(st.sampled_from(fams), st.sampled_from(fams)).filter(lambda t: t[0] != t[1]))
    codes_a = m["families"][fa]["codes"]
    codes_b = m["families"][fb]["codes"]

    baseline = [
        {"error_code": data.draw(st.sampled_from(codes_b)), "turn_number": i, "session_id": "s1", "tier": None}
        for i in range(data.draw(st.integers(min_value=0, max_value=5)))
    ]
    extra_a = [
        {"error_code": data.draw(st.sampled_from(codes_a)), "turn_number": 100 + i, "session_id": "sx", "tier": None}
        for i in range(data.draw(st.integers(min_value=1, max_value=5)))
    ]
    # independent session_id + disjoint turn_numbers → no cross-contamination via turn cap

    p_before = scoring_mod.compute_error_profile(baseline, "B1")
    p_after = scoring_mod.compute_error_profile(baseline + extra_a, "B1")

    assert p_before["families"][fb]["count"] == p_after["families"][fb]["count"]


# ── 7. Flag-on majority vote ────────────────────────────────────────
# With USE_V2_SCORING on and a strict tier-code majority in one family,
# the resulting tier must be the label for that code.

@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_majority=st.integers(min_value=2, max_value=6),
    n_minority=st.integers(min_value=0, max_value=1),
    majority_code=st.sampled_from(["T1", "T2", "T3", "T4"]),
    minority_code=st.sampled_from(["T1", "T2", "T3", "T4"]),
)
def test_flag_on_strict_majority_wins(scoring_mod, monkeypatch, n_majority, n_minority, majority_code, minority_code):
    if majority_code == minority_code:
        return  # not a contested scenario
    monkeypatch.setattr(scoring_mod, "_USE_V2_SCORING", True)
    rows = (
        [{"error_code": "V:TENSE", "turn_number": i, "session_id": f"s{i}", "tier": majority_code}
         for i in range(n_majority)]
        + [{"error_code": "V:TENSE", "turn_number": 100 + i, "session_id": f"m{i}", "tier": minority_code}
           for i in range(n_minority)]
    )
    prof = scoring_mod.compute_error_profile(rows, "B1")
    expected = scoring_mod._TIER_CODE_TO_LABEL[majority_code]
    assert prof["families"]["verb_tense"]["tier"] == expected


# ── 8. enrich_error_fields determinism ─────────────────────────────

@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=st.data())
def test_enrich_is_deterministic(scoring_mod, all_codes, all_levels, data):
    code = data.draw(st.sampled_from(all_codes))
    level = data.draw(st.one_of(st.none(), st.sampled_from(all_levels)))
    a = scoring_mod.enrich_error_fields(code, level)
    b = scoring_mod.enrich_error_fields(code, level)
    assert a == b


# ── 9. enrich_error_fields returns valid tier codes ─────────────────

@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=st.data())
def test_enrich_tier_is_valid_code(scoring_mod, all_codes, all_levels, data):
    code = data.draw(st.sampled_from(all_codes))
    level = data.draw(st.sampled_from(all_levels))
    out = scoring_mod.enrich_error_fields(code, level)
    if out["tier"] is not None:
        assert out["tier"] in scoring_mod._TIER_CODE_TO_LABEL


# ── 10. progress_pct bounded ─────────────────────────────────────────

@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(n_rows=st.integers(min_value=0, max_value=10))
def test_progress_pct_in_range(scoring_mod, all_codes, n_rows):
    rows = [
        {"error_code": all_codes[i % len(all_codes)], "turn_number": i, "session_id": "s1", "tier": None}
        for i in range(n_rows)
    ]
    prof = scoring_mod.compute_error_profile(rows, "B1", concept_keys=["present_simple", "articles"])
    pct = prof["progression"]["progress_pct"]
    assert 0 <= pct <= 100
