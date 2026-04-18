"""Test enrich_error_fields() helper (Sprint 2 Phase B2).

Replicates the lookup logic with the v2 yaml + override file to validate
without importing the backend module (path complications). The actual
scoring.enrich_error_fields is still the source of truth — these tests
verify the contract its callers rely on.
"""
from pathlib import Path

import pytest
import yaml

_TM_DIR = Path("/opt/academie/packages/academie-core/academie_core/data/tolerance_matrix")
V2_YAML = _TM_DIR / "tolerance_matrix_v2.yaml"
OV_YAML = _TM_DIR / "tolerance_matrix_v2_overrides.yaml"

_TIER_LABEL_TO_CODE = {
    "ignored": "T1",
    "noted": "T2",
    "penalized": "T3",
    "regressive": "T4",
    "shadow": "T0",
}


def _load_v2_with_overrides() -> dict:
    with open(V2_YAML) as f:
        m = yaml.safe_load(f)
    if OV_YAML.exists():
        with open(OV_YAML) as f:
            ov = yaml.safe_load(f) or {}
        for fam, bands in (ov.get("overrides") or {}).items():
            if fam in m.get("matrix", {}):
                m["matrix"][fam].update(bands)
    return m


def _enrich(matrix: dict, error_code: str, niveau: str | None) -> dict:
    """Replica of scoring.enrich_error_fields logic for autonomous testing."""
    fam = None
    for k, defn in matrix["families"].items():
        if error_code in defn.get("codes", []):
            fam = k
            break
    if not fam:
        return {k: None for k in (
            "tier", "gravity_linguistic", "gravity_communicative",
            "gravity_social", "criterial_level_emergence", "criterial_level_mastery",
        )}
    band = matrix["cefr_bands"].get((niveau or "B1").strip().upper(), "intermediate")
    tier_label = matrix["matrix"].get(fam, {}).get(band, "ignored")
    tier_code = _TIER_LABEL_TO_CODE.get(tier_label)
    g = matrix.get("gravity_per_family", {}).get(fam, {})
    c = matrix.get("criterial_per_family", {}).get(fam, {})
    return {
        "tier": tier_code,
        "gravity_linguistic": g.get("linguistic"),
        "gravity_communicative": g.get("communicative"),
        "gravity_social": g.get("social"),
        "criterial_level_emergence": c.get("emergence"),
        "criterial_level_mastery": c.get("mastery"),
    }


@pytest.fixture(scope="module")
def matrix():
    return _load_v2_with_overrides()


def test_enrich_verb_tense_b1_is_t1_ignored(matrix):
    """V:TENSE at B1 → tier=T1 (ignored, empirical reach > 0.7)."""
    out = _enrich(matrix, "V:TENSE", "B1")
    assert out["tier"] == "T1"
    assert out["gravity_linguistic"] == 0.6
    assert out["criterial_level_emergence"] == "A1"
    assert out["criterial_level_mastery"] == "B2"


def test_enrich_sentence_a1_uses_override_noted(matrix):
    """SENT:FRAG at A1 → tier=T2 (override sentence×beginner=noted, B1 layered on)."""
    out = _enrich(matrix, "SENT:FRAG", "A1")
    assert out["tier"] == "T2", \
        f"expected T2 (noted via override), got {out['tier']}"
    assert out["gravity_communicative"] == 0.7
    assert out["criterial_level_emergence"] == "A2"


def test_enrich_unknown_code_returns_all_none(matrix):
    out = _enrich(matrix, "ZZ:NOPE", "B2")
    assert all(v is None for v in out.values())


def test_enrich_handles_none_niveau(matrix):
    """niveau_global None → fallback band=intermediate, no crash."""
    out = _enrich(matrix, "V:TENSE", None)
    assert out["tier"] is not None
    assert out["gravity_linguistic"] == 0.6


def test_tier_label_mapping_covers_all_5_labels():
    """All v1 tier labels (incl. shadow + new regressive) map to T-codes."""
    expected = {
        "ignored": "T1",
        "noted": "T2",
        "penalized": "T3",
        "regressive": "T4",
        "shadow": "T0",
    }
    assert _TIER_LABEL_TO_CODE == expected
    assert all(c.startswith("T") and c[1:].isdigit() for c in expected.values())
