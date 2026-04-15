"""Test override loader logic (Phase B1).

Validates that tolerance_matrix_v2_overrides.yaml is parsed correctly and
that, when applied on top of v2 matrix, sentence×beginner becomes 'noted'.

Logic mirrored locally — does not import backend modules (avoids uvicorn
path complications).
"""
from pathlib import Path

import pytest
import yaml

V2_YAML = Path("/opt/academie/webapp/backend/app/config/tolerance_matrix_v2.yaml")
OV_YAML = Path("/opt/academie/webapp/backend/app/config/tolerance_matrix_v2_overrides.yaml")


def _apply_overrides(matrix: dict, overrides_doc: dict) -> dict:
    """Mirror of scoring._load_matrix override application."""
    for fam, bands in (overrides_doc.get("overrides") or {}).items():
        if fam in matrix.get("matrix", {}):
            matrix["matrix"][fam].update(bands)
    return matrix


def test_overrides_yaml_parses():
    assert OV_YAML.exists()
    with open(OV_YAML) as f:
        doc = yaml.safe_load(f)
    assert "overrides" in doc
    assert "sentence" in doc["overrides"]
    assert doc["overrides"]["sentence"]["beginner"] == "noted"


def test_v2_baseline_has_sentence_beginner_penalized():
    """Sanity reverse: without the override, v2 still says 'penalized'."""
    with open(V2_YAML) as f:
        v2 = yaml.safe_load(f)
    assert v2["matrix"]["sentence"]["beginner"] == "penalized"


def test_override_applied_flips_sentence_beginner_to_noted():
    """Core test: applying overrides on v2 yields sentence×beginner=noted."""
    with open(V2_YAML) as f:
        v2 = yaml.safe_load(f)
    with open(OV_YAML) as f:
        ov = yaml.safe_load(f)
    merged = _apply_overrides(v2, ov)
    assert merged["matrix"]["sentence"]["beginner"] == "noted", \
        "override sentence×beginner=noted not applied"


def test_override_only_touches_targeted_cells():
    """Other cells must remain untouched after override application."""
    with open(V2_YAML) as f:
        v2 = yaml.safe_load(f)
    # Snapshot a few unrelated cells
    expected = {
        ("verb_tense", "advanced"): v2["matrix"]["verb_tense"]["advanced"],
        ("noun_det", "intermediate"): v2["matrix"]["noun_det"]["intermediate"],
        ("preposition", "beginner"): v2["matrix"]["preposition"]["beginner"],
    }
    with open(OV_YAML) as f:
        ov = yaml.safe_load(f)
    merged = _apply_overrides(v2, ov)
    for (fam, band), val in expected.items():
        assert merged["matrix"][fam][band] == val, \
            f"override accidentally touched {fam}×{band}"
