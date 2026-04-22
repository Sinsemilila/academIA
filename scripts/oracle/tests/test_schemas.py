"""Session 40 Phase A — Unit tests for oracle scenario schemas."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # scripts/ on path

from oracle.schemas import GoldenFile, ScenarioSchema  # noqa: E402

EXAMPLES = (Path(__file__).resolve().parents[1] / "scenarios" / "teacher_en" / "_examples")


def test_examples_dir_exists():
    assert EXAMPLES.is_dir(), f"{EXAMPLES} missing"


def test_all_examples_valid():
    files = sorted(EXAMPLES.glob("*.yaml"))
    assert len(files) >= 4, f"expected ≥ 4 example scenarios, got {len(files)}"
    for f in files:
        raw = yaml.safe_load(f.read_text())
        ScenarioSchema.model_validate(raw)  # raises on drift


@pytest.mark.parametrize("f", sorted(EXAMPLES.glob("*.yaml")))
def test_example_parametric(f):
    raw = yaml.safe_load(f.read_text())
    sc = ScenarioSchema.model_validate(raw)
    assert sc.id == f.stem, f"filename {f.stem} must match id {sc.id}"
    assert sc.scenario_key.agent.startswith("teacher_")
    assert len(sc.turns) >= 1


def test_reject_missing_required():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ScenarioSchema.model_validate({"id": "bad"})


def test_reject_bad_cefr():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ScenarioSchema.model_validate({
            "id": "bad_cefr_test",
            "source": "handcrafted",
            "scenario_key": {"agent": "teacher_en", "cefr": "Z9",  # invalid
                             "target_tier": "T2", "error_category": "x", "fla": "low"},
            "turns": [{"role": "learner", "text": "hi"}],
        })


def test_golden_file_shape():
    GoldenFile.model_validate({
        "scenario_id": "x",
        "sha": "abc1234",
        "recorded_at": "2026-04-23T10:00:00Z",
        "response": "hello",
    })
