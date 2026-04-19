"""Tests for academie_core.levels — JLPT/TORFL ↔ CEFR mapping."""
from __future__ import annotations

import pytest

from academie_core.levels import (
    CEFR_LEVELS,
    CEFR_TO_JLPT,
    CEFR_TO_TORFL,
    JLPT_TO_CEFR,
    LEVEL_SYSTEM_BY_DOMAIN,
    TORFL_TO_CEFR,
    cefr_to_native,
    display_level,
    jlpt_score_to_cefr,
    parse_user_level,
)


class TestCefrCanon:
    def test_cefr_levels_tuple(self):
        assert CEFR_LEVELS == ("a1", "a2", "b1", "b2", "c1", "c2")


class TestJlptMapping:
    def test_all_jlpt_levels_map(self):
        assert JLPT_TO_CEFR["N5"] == "a1"
        assert JLPT_TO_CEFR["N4"] == "a2"
        assert JLPT_TO_CEFR["N3"] == "b1"
        assert JLPT_TO_CEFR["N2"] == "b2"
        assert JLPT_TO_CEFR["N1"] == "c1"
        assert JLPT_TO_CEFR["beyond_N1"] == "c2"

    def test_roundtrip_jlpt(self):
        for jlpt, cefr in JLPT_TO_CEFR.items():
            assert CEFR_TO_JLPT[cefr] == jlpt

    def test_all_cefr_have_jlpt(self):
        for cefr in CEFR_LEVELS:
            assert cefr in CEFR_TO_JLPT


class TestTorflMapping:
    def test_all_torfl_levels_map(self):
        assert TORFL_TO_CEFR["TEU"] == "a1"
        assert TORFL_TO_CEFR["TBU"] == "a2"
        assert TORFL_TO_CEFR["TORFL-I"] == "b1"
        assert TORFL_TO_CEFR["TORFL-II"] == "b2"
        assert TORFL_TO_CEFR["TORFL-III"] == "c1"
        assert TORFL_TO_CEFR["TORFL-IV"] == "c2"

    def test_roundtrip_torfl(self):
        for torfl, cefr in TORFL_TO_CEFR.items():
            assert CEFR_TO_TORFL[cefr] == torfl


class TestDomainDispatch:
    def test_cefr_domains(self):
        assert LEVEL_SYSTEM_BY_DOMAIN["teacher"] == "cefr"
        assert LEVEL_SYSTEM_BY_DOMAIN["maestro"] == "cefr"
        assert LEVEL_SYSTEM_BY_DOMAIN["professore"] == "cefr"
        assert LEVEL_SYSTEM_BY_DOMAIN["lehrer"] == "cefr"

    def test_native_domains(self):
        assert LEVEL_SYSTEM_BY_DOMAIN["sensei"] == "jlpt"
        assert LEVEL_SYSTEM_BY_DOMAIN["uchitel"] == "torfl"


class TestDisplayLevel:
    def test_teacher_cefr_display(self):
        assert display_level("b1", "teacher") == "B1"
        assert display_level("c2", "maestro") == "C2"

    def test_sensei_jlpt_display(self):
        assert display_level("a1", "sensei") == "N5"
        assert display_level("b1", "sensei") == "N3"
        assert display_level("c1", "sensei") == "N1"
        assert display_level("c2", "sensei") == "beyond_N1"

    def test_uchitel_torfl_display(self):
        assert display_level("a1", "uchitel") == "TEU"
        assert display_level("b2", "uchitel") == "TORFL-II"
        assert display_level("c2", "uchitel") == "TORFL-IV"

    def test_unknown_domain_defaults_cefr(self):
        assert display_level("a2", "unknown_agent") == "A2"

    def test_invalid_cefr_raises(self):
        with pytest.raises(ValueError, match="unknown CEFR level"):
            display_level("d1", "teacher")


class TestParseUserLevel:
    def test_parse_cefr_direct(self):
        assert parse_user_level("B1", "teacher") == "b1"
        assert parse_user_level("a1", "maestro") == "a1"

    def test_parse_jlpt_for_sensei(self):
        assert parse_user_level("N4", "sensei") == "a2"
        assert parse_user_level("N1", "sensei") == "c1"

    def test_parse_torfl_for_uchitel(self):
        assert parse_user_level("TORFL-I", "uchitel") == "b1"
        assert parse_user_level("TEU", "uchitel") == "a1"

    def test_cross_system_fallback(self):
        # A user on teacher domain entering JLPT still resolves.
        assert parse_user_level("N3", "teacher") == "b1"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            parse_user_level("", "teacher")

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="cannot parse"):
            parse_user_level("XYZ99", "teacher")


class TestCefrToNative:
    def test_alias_of_display_level(self):
        assert cefr_to_native("b1", "sensei") == display_level("b1", "sensei")
        assert cefr_to_native("a2", "uchitel") == display_level("a2", "uchitel")


class TestJlptScoreBridge:
    def test_n5_threshold(self):
        assert jlpt_score_to_cefr("N5", 80) == "a1"
        assert jlpt_score_to_cefr("N5", 180) == "a1"

    def test_n3_boundary(self):
        assert jlpt_score_to_cefr("N3", 95) == "a2"
        assert jlpt_score_to_cefr("N3", 103) == "a2"
        assert jlpt_score_to_cefr("N3", 104) == "b1"
        assert jlpt_score_to_cefr("N3", 180) == "b1"

    def test_n2_boundary(self):
        assert jlpt_score_to_cefr("N2", 111) == "b1"
        assert jlpt_score_to_cefr("N2", 112) == "b2"

    def test_n1_boundary(self):
        assert jlpt_score_to_cefr("N1", 141) == "b2"
        assert jlpt_score_to_cefr("N1", 142) == "c1"

    def test_below_minimum_raises(self):
        with pytest.raises(ValueError, match="below minimum"):
            jlpt_score_to_cefr("N5", 79)
        with pytest.raises(ValueError, match="below minimum"):
            jlpt_score_to_cefr("N3", 94)

    def test_unknown_level_raises(self):
        with pytest.raises(ValueError, match="unknown JLPT"):
            jlpt_score_to_cefr("N99", 100)
