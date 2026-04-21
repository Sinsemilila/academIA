"""Unit tests for scripts/inject_curriculum.py — YAML schema validation +
row building. No DB write (DB-free tests).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make sibling script importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from inject_curriculum import (  # noqa: E402
    load_curriculum,
    validate_schema,
    build_rows,
    CEFR_LEVELS,
)


def test_load_es_curriculum():
    data = load_curriculum("es")
    assert data["domain"] == "es"
    for lvl in CEFR_LEVELS:
        assert lvl in data, f"missing {lvl}"


def test_load_en_curriculum():
    data = load_curriculum("en")
    assert data["domain"] == "en"


def test_load_missing_raises():
    try:
        load_curriculum("xx_nonexistent")
    except FileNotFoundError:
        return
    raise AssertionError("expected FileNotFoundError")


def test_validate_schema_accepts_valid_es():
    data = load_curriculum("es")
    validate_schema(data, "es")  # Must not raise


def test_validate_schema_rejects_domain_mismatch():
    data = load_curriculum("es")
    try:
        validate_schema(data, "en")
    except ValueError as e:
        assert "domain" in str(e).lower()
        return
    raise AssertionError("expected ValueError on domain mismatch")


def test_validate_schema_rejects_missing_level():
    bad = {"domain": "es"}  # no A1-C2
    try:
        validate_schema(bad, "es")
    except ValueError as e:
        assert "A1" in str(e)
        return
    raise AssertionError("expected ValueError on missing level")


def test_validate_schema_rejects_empty_concept_keys():
    bad = {
        "domain": "es",
        **{lvl: {"concept_keys": [], "concept_weights": {}, "concept_groups": {}}
           for lvl in CEFR_LEVELS},
    }
    try:
        validate_schema(bad, "es")
    except ValueError as e:
        assert "concept_keys" in str(e)
        return
    raise AssertionError("expected ValueError on empty concept_keys")


def test_validate_schema_rejects_weights_key_not_in_concept_keys():
    bad = {
        "domain": "es",
        **{lvl: {
            "concept_keys": ["foo", "bar"],
            "concept_weights": {"foo": 5, "baz": 3},  # baz not in keys
            "concept_groups": {"g": ["foo"]},
        } for lvl in CEFR_LEVELS},
    }
    try:
        validate_schema(bad, "es")
    except ValueError as e:
        assert "baz" in str(e)
        return
    raise AssertionError("expected ValueError on orphan weight key")


def test_validate_schema_tolerates_note_annotations():
    ok = {
        "domain": "es",
        **{lvl: {
            "concept_keys": ["foo"],
            "concept_weights": {"foo": 5, "concept_weights_note": "some comment"},
            "concept_groups": {"g": ["foo"]},
        } for lvl in CEFR_LEVELS},
    }
    validate_schema(ok, "es")  # Must not raise


def test_build_rows_produces_6_levels():
    data = load_curriculum("es")
    rows = build_rows(data)
    assert len(rows) == 6
    niveaux = {r["niveau"] for r in rows}
    assert niveaux == set(CEFR_LEVELS)


def test_build_rows_strips_note_annotations_from_weights():
    # Synthetic data with _note entries in concept_weights
    data = {
        "domain": "es",
        **{lvl: {
            "description": "test",
            "concept_keys": ["foo"],
            "concept_weights": {"foo": 5, "weights_note": "comment", "some_note": "doc"},
            "concept_groups": {"g": ["foo"]},
        } for lvl in CEFR_LEVELS},
    }
    rows = build_rows(data)
    for r in rows:
        for key in r["concept_weights"]:
            assert not key.endswith("_note"), f"unexpected note key: {key}"
        assert "foo" in r["concept_weights"]


def test_es_curriculum_row_counts():
    """Sanity check: ES YAML has reasonable concept counts per level."""
    data = load_curriculum("es")
    rows = build_rows(data)
    total = sum(len(r["concept_keys"]) for r in rows)
    assert 40 <= total <= 65, f"ES total concepts out of expected range: {total}"


if __name__ == "__main__":
    ns = dict(globals())
    total = failures = 0
    for name in sorted(ns):
        if name.startswith("test_") and callable(ns[name]):
            total += 1
            try:
                ns[name]()
                print(f"OK   {name}")
            except Exception as e:
                failures += 1
                print(f"FAIL {name}: {type(e).__name__}: {e}")
    print(f"\n{total - failures}/{total} passed")
    sys.exit(0 if failures == 0 else 1)
