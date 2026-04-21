import pytest

from academie_core.pedagogy.scaffolding_policy import (
    POLICY_MATRIX,
    build_scaffolding_block,
    resolve_policy,
    _normalize_fla,
)


# Parametrized over all 9 cells of the base matrix (A1/A2/B1+ × close/medium/distant)
@pytest.mark.parametrize("band,distance", list(POLICY_MATRIX.keys()))
def test_base_matrix_well_formed(band, distance):
    row = POLICY_MATRIX[(band, distance)]
    assert 0 <= row.l2_ratio_pct <= 100
    assert isinstance(row.l1_uses, tuple)
    assert isinstance(row.sandwich, bool)
    assert isinstance(row.reassurance_l1, bool)
    # 100% L2 implies no L1 uses permitted
    if row.l2_ratio_pct == 100:
        assert row.l1_uses == ()


def test_a1_distant_high_fla_shifts_same_distant():
    # FLA high on distant stays distant (already maxed)
    p = resolve_policy("A1", "distant", "high")
    assert p.l2_ratio_pct == 55
    assert p.reassurance_l1 is True


def test_a1_close_high_fla_shifts_to_medium():
    p_low = resolve_policy("A1", "close", "low")
    p_high = resolve_policy("A1", "close", "high")
    assert p_low.l2_ratio_pct == 90
    assert p_high.l2_ratio_pct == 85  # shifted to medium cell


def test_a1_medium_high_fla_shifts_to_distant():
    p = resolve_policy("A1", "medium", "high")
    assert p.l2_ratio_pct == 55  # now at distant cell


def test_b1_close_is_full_l2():
    block = build_scaffolding_block("B1", "close", "low", "Español")
    assert block == ""  # no-op


def test_b1_distant_still_has_minimal_gloss():
    block = build_scaffolding_block("B1", "distant", "low", "日本語")
    assert "L1/L2 MIX POLICY" in block
    assert "95%" in block


def test_a1_close_low_fla_renders_sandwich():
    block = build_scaffolding_block("A1", "close", "low", "Español", "français")
    assert "90%" in block
    assert "SANDWICH" in block
    assert "reassurance" not in block.lower()


def test_a1_distant_high_fla_renders_reassurance():
    block = build_scaffolding_block("A1", "distant", "high", "日本語", "français")
    assert "55%" in block
    assert "SANDWICH" in block
    assert "reassurance" in block or "one short" in block


def test_sandwich_disabled_past_turn_6():
    b1 = build_scaffolding_block("A1", "medium", "low", "English", turn_count=1)
    b10 = build_scaffolding_block("A1", "medium", "low", "English", turn_count=10)
    assert "SANDWICH" in b1
    assert "SANDWICH" not in b10


def test_reassurance_only_early_turns():
    b1 = build_scaffolding_block("A1", "distant", "high", "日本語", turn_count=1)
    b5 = build_scaffolding_block("A1", "distant", "high", "日本語", turn_count=5)
    assert "one short" in b1
    assert "one short" not in b5  # only turn 1-2


def test_cefr_band_collapses():
    # A1+ collapses to A1
    p1 = resolve_policy("A1+", "close", "low")
    p2 = resolve_policy("A1", "close", "low")
    assert p1 == p2


def test_unknown_placement_falls_to_b1_plus():
    # Unknown / empty → treated as B1+ (safe default, no extra scaffolding)
    p = resolve_policy("", "close", "low")
    assert p.l2_ratio_pct == 100


def test_normalize_fla_defaults_medium():
    assert _normalize_fla(None) == "medium"
    assert _normalize_fla("") == "medium"
    assert _normalize_fla("LOW") == "low"
    assert _normalize_fla("garbage") == "medium"
