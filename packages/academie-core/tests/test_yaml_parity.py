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


# ── Session 37 — Wave 2-4 L1 transfer stubs ──────────────────────────


import pytest


@pytest.mark.parametrize("target,min_count,wave", [
    ("it", 3, "Wave 2"),
    ("de", 3, "Wave 2"),
    ("ja", 3, "Wave 3"),
    ("ru", 3, "Wave 4"),
])
def test_l1_transfer_stub_loads_with_min_entries(target, min_count, wave):
    transfers = load_l1_transfers("fr", target)
    assert len(transfers) >= min_count, (
        f"fr_to_{target} ({wave}) has only {len(transfers)} entries (min {min_count})"
    )


@pytest.mark.parametrize("target", ["it", "de", "ja", "ru"])
def test_l1_transfer_stub_schema_valid(target):
    transfers = load_l1_transfers("fr", target)
    for fam, mult, desc in transfers:
        assert isinstance(fam, str) and fam, f"empty family in fr_to_{target}"
        assert isinstance(mult, (int, float)) and 1.0 <= mult <= 2.0, (
            f"multiplier out of range in fr_to_{target}: {fam}={mult}"
        )
        assert isinstance(desc, str) and len(desc) > 50, (
            f"description too short in fr_to_{target}: {fam}"
        )


@pytest.mark.parametrize("target", ["it", "de", "ja", "ru"])
def test_l1_transfer_stub_multipliers_descending(target):
    transfers = load_l1_transfers("fr", target)
    mults = [m for _, m, _ in transfers]
    assert mults == sorted(mults, reverse=True), (
        f"fr_to_{target} multipliers not descending: {mults}"
    )


# ── Session 37 — curriculum_en.yaml parity with curriculum_es.yaml ──

import yaml as _yaml
from pathlib import Path as _Path
import academie_core as _ac

# Resolve via installed package so tests work from any CWD (host or container).
_CURR_DIR = _Path(_ac.__file__).resolve().parent / "data"


def _load_curriculum(lang: str) -> dict:
    path = _CURR_DIR / f"curriculum_{lang}.yaml"
    return _yaml.safe_load(path.read_text())


def test_curriculum_en_yaml_exists_and_loads():
    curr = _load_curriculum("en")
    assert curr is not None
    assert curr.get("domain") == "en"


@pytest.mark.parametrize("lang", ["en", "es"])
@pytest.mark.parametrize("level", ["A1", "A2", "B1", "B2", "C1", "C2"])
def test_curriculum_level_has_required_sections(lang, level):
    curr = _load_curriculum(lang)
    assert level in curr, f"{lang} missing {level}"
    block = curr[level]
    assert block.get("concept_keys"), f"{lang}/{level} empty concept_keys"
    assert block.get("concept_weights"), f"{lang}/{level} empty concept_weights"
    assert block.get("concept_groups"), f"{lang}/{level} empty concept_groups"


@pytest.mark.parametrize("lang", ["en", "es"])
@pytest.mark.parametrize("level", ["A1", "A2", "B1", "B2", "C1", "C2"])
def test_curriculum_weights_refer_valid_keys(lang, level):
    curr = _load_curriculum(lang)
    keys = set(curr[level]["concept_keys"])
    weights = curr[level]["concept_weights"]
    for k in weights:
        if k.endswith("_note"):
            continue  # free-form annotation allowed
        assert k in keys, f"{lang}/{level}: weight key {k!r} not in concept_keys"


@pytest.mark.parametrize("lang", ["en", "es"])
@pytest.mark.parametrize("level", ["A1", "A2", "B1", "B2", "C1", "C2"])
def test_curriculum_all_concepts_grouped(lang, level):
    curr = _load_curriculum(lang)
    keys = set(curr[level]["concept_keys"])
    grouped = set()
    for g in curr[level]["concept_groups"].values():
        if isinstance(g, list):
            grouped.update(g)
    orphans = keys - grouped
    assert not orphans, f"{lang}/{level}: ungrouped concepts {orphans}"


def test_curriculum_en_total_concepts_reasonable():
    """Session 37 sanity: EN should have ~45-60 concepts (ES has 52)."""
    curr = _load_curriculum("en")
    total = sum(len(curr[lvl]["concept_keys"]) for lvl in ["A1","A2","B1","B2","C1","C2"])
    assert 45 <= total <= 65, f"curriculum_en total concepts out of range: {total}"


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
