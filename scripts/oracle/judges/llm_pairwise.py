"""Session 40 Phase A — LLM pairwise dim scoring (stubs, filled Phase B1)."""
from __future__ import annotations

from ..schemas import DimVerdict, ScenarioSchema


def score_all(scenario: ScenarioSchema, response: str, golden: str, cfg: dict, n: int = 3) -> list[DimVerdict]:
    """Returns verdicts for LLM-judged dims. Stub for now."""
    return []  # Phase B1 fills
