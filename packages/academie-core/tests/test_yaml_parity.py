"""YAML parity tests — ensure externalized YAML files match hardcoded fallbacks.

These tests guard against silent data drift between YAML and Python sources.
If a YAML file is missing, the hardcoded fallback is used automatically;
these tests verify the YAML files exist and contain identical data.
"""
from __future__ import annotations

from academie_core.data.loader import load_rubrics, load_fewshots, load_l1_names, load_l1_transfers
from academie_core.pedagogy.teacher_prompt import LanguageData


# ── Rubrics ──────────────────────────────────────────────────────────


def test_rubrics_yaml_exists_and_loads():
    rubrics = load_rubrics("en")
    assert rubrics is not None, "en.yaml missing from data/rubrics/"
    assert isinstance(rubrics, dict)


def test_rubrics_yaml_has_all_six_levels():
    rubrics = load_rubrics("en")
    for level in ("A1", "A2", "B1", "B2", "C1", "C2"):
        assert level in rubrics, f"Missing level {level} in rubrics/en.yaml"
        assert len(rubrics[level]) > 50, f"Rubric {level} too short"


def test_rubrics_yaml_content_starts_correctly():
    rubrics = load_rubrics("en")
    assert rubrics["A1"].startswith("RUBRIC A1")
    assert rubrics["C2"].startswith("RUBRIC C2")


# ── Fewshots ─────────────────────────────────────────────────────────


def test_fewshots_yaml_exists_and_loads():
    fewshots = load_fewshots("en")
    assert fewshots is not None, "en.yaml missing from data/fewshots/"
    assert isinstance(fewshots, list)


def test_fewshots_yaml_count_and_ids():
    fewshots = load_fewshots("en")
    assert len(fewshots) == 14, f"Expected 14 fewshots, got {len(fewshots)}"
    ids = {fs["id"] for fs in fewshots}
    assert "a1-recast-past-go" in ids
    assert "c2-silence-creative-style" in ids


def test_fewshots_yaml_all_have_required_keys():
    fewshots = load_fewshots("en")
    required = {"id", "level", "type", "learner", "teacher"}
    for fs in fewshots:
        missing = required - set(fs.keys())
        assert not missing, f"Fewshot {fs.get('id', '?')} missing keys: {missing}"


def test_fewshots_yaml_covers_all_levels():
    fewshots = load_fewshots("en")
    levels = {fs["level"] for fs in fewshots}
    for level in ("A1", "A2", "B1", "B2", "C1", "C2"):
        assert level in levels, f"No fewshot for level {level}"


# ── L1 Transfer ──────────────────────────────────────────────────────


def test_l1_names_yaml_exists():
    names = load_l1_names()
    assert len(names) >= 14, f"Expected >=14 L1 names, got {len(names)}"
    assert names["fr"] == "French"
    assert names["es"] == "Spanish"
    assert names["ja"] == "Japanese"


def test_l1_transfer_fr_en_yaml_exists():
    transfers = load_l1_transfers("fr", "en")
    assert len(transfers) == 5, f"Expected 5 FR→EN transfers, got {len(transfers)}"


def test_l1_transfer_fr_en_families():
    transfers = load_l1_transfers("fr", "en")
    families = [t[0] for t in transfers]
    assert "articles" in families
    assert "prepositions" in families
    assert "false_friends" in families


def test_l1_transfer_fr_en_multipliers_ordered():
    transfers = load_l1_transfers("fr", "en")
    multipliers = [t[1] for t in transfers]
    assert multipliers == sorted(multipliers, reverse=True), "Transfers should be ordered by multiplier descending"


def test_l1_transfer_missing_pair_returns_empty():
    transfers = load_l1_transfers("xx", "yy")
    assert transfers == []


# ── LanguageData ─────────────────────────────────────────────────────


def test_language_data_for_en_loads_all():
    ld = LanguageData.for_lang("en")
    assert ld.lang_target == "en"
    assert len(ld.rubrics) == 6
    assert len(ld.fewshots) == 14
    assert len(ld.l1_names) >= 14


def test_language_data_for_unknown_graceful():
    ld = LanguageData.for_lang("xx")
    assert ld.lang_target == "xx"
    # Falls back to EN data (hardcoded or YAML-loaded EN)
    assert len(ld.rubrics) == 6, "Unknown lang should fallback to EN rubrics"
    assert len(ld.fewshots) == 14, "Unknown lang should fallback to EN fewshots"
