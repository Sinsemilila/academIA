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


# ── Session 37 — per-item FLA flags + intensity shift ────────────────

def test_fla_items_high_speaking_sets_prefer_written():
    p = resolve_policy("A2", "close", "low", fla_items_raw={"fla_a": 5, "fla_b": 1, "fla_c": 1})
    assert p.prefer_written_first is True
    assert p.no_explicit_correction is False
    assert p.provide_chunks_ahead is False


def test_fla_items_high_mockery_sets_no_correction():
    p = resolve_policy("A2", "close", "low", fla_items_raw={"fla_a": 1, "fla_b": 5, "fla_c": 1})
    assert p.no_explicit_correction is True
    assert p.prefer_written_first is False


def test_fla_items_high_freeze_sets_provide_chunks():
    p = resolve_policy("A2", "close", "low", fla_items_raw={"fla_a": 1, "fla_b": 1, "fla_c": 5})
    assert p.provide_chunks_ahead is True


def test_fla_items_threshold_at_4():
    # Exactly 4 triggers the flag; 3 does not
    p4 = resolve_policy("A2", "close", "low", fla_items_raw={"fla_a": 4, "fla_b": 3, "fla_c": 3})
    assert p4.prefer_written_first is True
    p3 = resolve_policy("A2", "close", "low", fla_items_raw={"fla_a": 3, "fla_b": 3, "fla_c": 3})
    assert p3.prefer_written_first is False


def test_intensity_shift_from_low_selfeff():
    # B1+/close base is "low" intensity. self_eff=1 → +1 → medium.
    p = resolve_policy("B1", "close", "low", self_efficacy=1)
    assert p.scaffolding_intensity == "medium"


def test_intensity_shift_from_autonomous_expert():
    # A2/close base is "medium". self_eff=5 + autonomy="autonomous" → -1 → low.
    p = resolve_policy("A2", "close", "low",
                      self_efficacy=5, autonomy_pref="autonomous")
    assert p.scaffolding_intensity == "low"


def test_intensity_no_shift_for_mid_selfeff():
    p = resolve_policy("A2", "close", "low", self_efficacy=3)
    assert p.scaffolding_intensity == "medium"


def test_intensity_shift_caps_at_high():
    # A1/close base already "high" — +1 shift must cap (no "very_high" tier).
    p = resolve_policy("A1", "close", "low", self_efficacy=1)
    assert p.scaffolding_intensity == "high"


def test_intensity_shift_caps_at_low():
    # B1+/close base "low" — -1 shift must stay "low".
    p = resolve_policy("B1", "close", "low",
                      self_efficacy=5, autonomy_pref="autonomous")
    assert p.scaffolding_intensity == "low"


def test_build_block_renders_anxiety_routing():
    block = build_scaffolding_block(
        "A2", "close", "low", "Español",
        fla_items_raw={"fla_a": 5, "fla_b": 5, "fla_c": 5},
    )
    assert "ANXIETY ROUTING" in block
    assert "speaking à froid" in block
    assert "corrections publiques" in block
    assert "Freeze mémoriel" in block


def test_build_block_skips_anxiety_routing_when_flags_off():
    block = build_scaffolding_block(
        "A2", "close", "low", "Español",
        fla_items_raw={"fla_a": 2, "fla_b": 2, "fla_c": 2},
    )
    assert "ANXIETY ROUTING" not in block


def test_build_block_still_empty_when_pure_noop():
    # B1+/close with no anxiety flags → must remain empty (no-op)
    block = build_scaffolding_block("B1", "close", "low", "Español",
                                     fla_items_raw={"fla_a": 1, "fla_b": 1, "fla_c": 1})
    assert block == ""


def test_build_block_renders_intensity_line():
    block = build_scaffolding_block("A1", "close", "low", "Español")
    assert "Scaffolding intensity:" in block


def test_backward_compat_no_kwargs():
    # Calling resolve_policy without Session 37 kwargs must not break
    p = resolve_policy("A1", "close", "low")
    assert p.l2_ratio_pct == 90
    assert p.prefer_written_first is False
    assert p.scaffolding_intensity == "high"
