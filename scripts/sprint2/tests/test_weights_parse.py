"""Sanity tests: v2 tolerance matrix parses and is internally consistent."""
from pathlib import Path

import pytest
import yaml

_TM_DIR = Path("/opt/academie/packages/academie-core/academie_core/data/tolerance_matrix")
V2_YAML = _TM_DIR / "tolerance_matrix_v2.yaml"
V1_YAML = _TM_DIR / "tolerance_matrix.yaml"


@pytest.fixture(scope="module")
def v2():
    with open(V2_YAML) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def v1():
    with open(V1_YAML) as f:
        return yaml.safe_load(f)


def test_v2_yaml_exists_and_parses(v2):
    assert isinstance(v2, dict)
    assert "families" in v2
    assert "matrix" in v2
    assert "weights" in v2


def test_v2_has_12_families(v2):
    assert len(v2["families"]) == 12


def test_v2_matrix_covers_all_families(v2):
    assert set(v2["matrix"].keys()) == set(v2["families"].keys())


def test_v2_weights_shape(v2):
    w = v2["weights"]
    # v2 keeps v1 vocab (ignored/noted/penalized/shadow) + adds regressive
    required = {"ignored", "noted", "penalized", "shadow"}
    assert required.issubset(set(w.keys())), f"Missing tiers: {required - set(w.keys())}"
    # All weights in [0, 1]
    for tier, val in w.items():
        assert 0.0 <= val <= 1.0, f"Weight {tier}={val} out of [0,1]"


def test_v2_weights_monotone_ignored_noted_penalized(v2):
    w = v2["weights"]
    assert w["ignored"] <= w["noted"] <= w["penalized"]


def test_v2_weights_source_tagged(v2):
    assert "weights_source" in v2
    assert "GLMM" in v2["weights_source"] or "empirical" in v2["weights_source"]


def test_v2_glmm_diagnostics_present(v2):
    assert "glmm_diagnostics" in v2
    d = v2["glmm_diagnostics"]
    assert d["r_hat_max"] <= 1.05  # reasonable convergence
    assert d["ess_bulk_min"] >= 200  # not catastrophically low
    assert d["n_samples"] >= 1000


def test_all_rules_codes_in_v2_families(v2):
    """Every error code used by rules.py must appear in v2.families.codes."""
    # Extract known AcademIA codes from categories.py via regex (avoid import)
    categories_py = Path("/opt/academie/packages/academie-core/academie_core/taxonomy/categories.py").read_text()
    import re
    m = re.search(r"TIER1_CATEGORIES\s*=\s*\{(.+?)\}", categories_py, re.DOTALL)
    academie_codes = set(re.findall(r'"([A-Z]+(?::[A-Z:]+)?)"', m.group(1)))

    v2_codes = set()
    for fam_def in v2["families"].values():
        v2_codes.update(fam_def.get("codes", []))

    missing = academie_codes - v2_codes
    assert not missing, f"Codes in TIER1_CATEGORIES missing from v2.families: {missing}"


def test_v2_matrix_diff_vs_v1_is_21_cells(v1, v2):
    """Document the expected delta — Sprint 1.5 report says 44% = 21/48 cells."""
    bands = ["beginner", "intermediate", "upper", "advanced"]
    changed = 0
    for fam in v1["matrix"]:
        for band in bands:
            if v1["matrix"][fam].get(band) != v2["matrix"][fam].get(band):
                changed += 1
    assert changed == 21, f"Expected 21 changed cells, got {changed}"
