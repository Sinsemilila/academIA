"""Session 40 Phase A — Deterministic dim scoring (stubs, filled Phase B1)."""
from __future__ import annotations

from ..schemas import DimVerdict, ScenarioSchema


def score_all(scenario: ScenarioSchema, response: str) -> list[DimVerdict]:
    """Returns verdicts for dims we can score without an LLM. Stub for now."""
    return []  # Phase B1 fills
