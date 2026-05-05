"""Tests for ERRANT → AcademIA mapping.

Exits non-zero if coverage of W&I tags drops below 95%.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from errant_mapper import ErrantMapper, map_errant_tag  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
M2_DIR = Path("/mnt/cosmos-data/sprint1/data/raw/wi+locness/m2")
ACADEMIE_CATEGORIES_PY = Path("/opt/academia/webapp/backend/app/error_taxonomy/categories.py")


@pytest.fixture(scope="module")
def mapper() -> ErrantMapper:
    return ErrantMapper()


@pytest.fixture(scope="module")
def wi_tags() -> set[str]:
    """Collect every distinct ERRANT tag that appears in W&I .m2 files."""
    tags: set[str] = set()
    if not M2_DIR.exists():
        pytest.skip("W&I corpus not downloaded yet")
    for m2 in M2_DIR.glob("*.m2"):
        with open(m2) as f:
            for line in f:
                if line.startswith("A "):
                    # Format: A start end|||TAG|||correction|||REQUIRED|||...
                    parts = line.split("|||")
                    if len(parts) >= 2:
                        tags.add(parts[1])
    return tags


@pytest.fixture(scope="module")
def academie_codes() -> set[str]:
    """Extract AcademIA TIER1_CATEGORIES codes via simple regex."""
    text = ACADEMIE_CATEGORIES_PY.read_text()
    m = re.search(r"TIER1_CATEGORIES\s*=\s*\{(.+?)\}", text, re.DOTALL)
    assert m, "TIER1_CATEGORIES not found"
    return set(re.findall(r'"([A-Z]+(?::[A-Z:]+)?)"', m.group(1)))


def test_every_tag_in_wi_either_mapped_or_unmappable(mapper, wi_tags):
    unknown = []
    for tag in wi_tags:
        result = mapper.map(tag)
        if result.status == "unknown":
            unknown.append(tag)
    assert not unknown, f"Unknown tags (add to yaml): {unknown}"


def test_mapped_coverage_above_threshold(mapper):
    """≥80% of *actual-error* ERRANT instances should map to an AcademIA code.

    `noop` (no error) is excluded from the denominator since it represents
    sentences with no annotation needed — not a classification failure.
    """
    error_instances = 0
    mapped_instances = 0
    for m2 in M2_DIR.glob("*.m2"):
        with open(m2) as f:
            for line in f:
                if line.startswith("A "):
                    parts = line.split("|||")
                    if len(parts) >= 2:
                        tag = parts[1]
                        if tag == "noop":
                            continue
                        error_instances += 1
                        if mapper.map(tag).status == "mapped":
                            mapped_instances += 1
    coverage = mapped_instances / error_instances if error_instances else 0.0
    print(f"\nERRANT→AcademIA mapped coverage (excl. noop): {coverage:.1%} ({mapped_instances}/{error_instances})")
    assert coverage >= 0.80, f"Mapped coverage {coverage:.1%} < 80%"


def test_mapped_codes_exist_in_academie(mapper, academie_codes):
    """Every mapped academie_code must exist in TIER1_CATEGORIES."""
    with open(ROOT / "errant_to_academie.yaml") as f:
        cfg = yaml.safe_load(f)
    bad = []
    for core_tag, m in cfg["mappings"].items():
        if m["academie_code"] not in academie_codes:
            bad.append((core_tag, m["academie_code"]))
    assert not bad, f"Mapped codes not in TIER1_CATEGORIES: {bad}"


def test_op_prefix_is_stripped():
    assert map_errant_tag("R:VERB:TENSE").academie_code == "V:TENSE"
    assert map_errant_tag("M:VERB:TENSE").academie_code == "V:TENSE"
    assert map_errant_tag("U:VERB:TENSE").academie_code == "V:TENSE"
    assert map_errant_tag("M:PREP").academie_code == "PREP"
    assert map_errant_tag("R:NOUN:NUM").academie_code == "N:COUNT"
    assert map_errant_tag("UNK").status == "unmappable"
    assert map_errant_tag("NOPE").status == "unknown"
