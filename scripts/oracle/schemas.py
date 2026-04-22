"""Session 40 Phase A — Oracle V1 scenario + golden pydantic schemas.

Mirrors the pattern already in `packages/academie-core/academie_core/data/schemas.py`
(Session 39 YAML validator). `extra='forbid'` on leaf types to catch typos ;
the dimension spec container is Lax because dim names can evolve.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CEFRLevel = Literal["A1", "A2", "B1", "B2", "C1", "C2"]
Tier = Literal["T1", "T2", "T3", "T4"]
FLABand = Literal["low", "mid", "high"]
StyleProfile = Literal["direct", "encourageant", "doux", "humour"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Lax(BaseModel):
    model_config = ConfigDict(extra="allow")


class ScenarioKey(_Strict):
    agent: str = Field(..., pattern=r"^[a-z_]+_[a-z]{2}$")  # teacher_en, maestro_es
    cefr: CEFRLevel
    target_tier: Tier
    error_category: str = Field(..., min_length=2)  # verb_tense, articles, ...
    fla: FLABand
    style_profile: StyleProfile = "direct"


class ScenarioTurn(_Strict):
    role: Literal["learner", "teacher"]
    text: str = Field(..., min_length=1)
    turn_number: int = Field(default=1, ge=1)
    expected_errors: list[str] = Field(default_factory=list)
    uptake: Literal["yes", "no", "partial"] | None = None  # multi-turn only


class GoldenRef(_Strict):
    sha: str = Field(..., min_length=7, max_length=40)  # git SHA of prompt-time
    recorded_at: str  # ISO timestamp
    path: str | None = None  # relative to oracle/scenarios/teacher_en/golden/
    response: str | None = None  # inline option (small goldens only)


class ScenarioSchema(_Lax):
    """Top-level Oracle scenario. Fields beyond those typed are tolerated
    so dimension specs can evolve without breaking existing YAMLs."""
    id: str = Field(..., min_length=5, max_length=120)
    source: str = Field(..., min_length=3)
    scenario_key: ScenarioKey
    multi_turn: bool = False
    turns: list[ScenarioTurn] = Field(..., min_length=1)
    expected_dimensions: dict = Field(default_factory=dict)  # free-form dict, Lax
    golden: GoldenRef | None = None  # None = golden to be recorded in Phase B2
    aspirational: bool = False


class GoldenFile(_Strict):
    """Shape of the JSON stored in scripts/oracle/scenarios/teacher_en/golden/*.json."""
    scenario_id: str
    sha: str
    recorded_at: str
    response: str
    dify_conversation_id: str | None = None
    dify_message_id: str | None = None
    usage: dict | None = None  # token counts from Dify


class LintResult(_Strict):
    check: str
    passed: bool
    detail: str = ""


class DimVerdict(_Strict):
    dim: str
    verdict: Literal["pass", "fail", "unknown"]
    score: float | None = None
    reasoning: str = ""
    judge_votes: list[dict] = Field(default_factory=list)


class ScenarioResult(_Lax):
    scenario_id: str
    mode: Literal["lint", "smoke", "full"]
    lint: list[LintResult] = Field(default_factory=list)
    dims: list[DimVerdict] = Field(default_factory=list)
    overall: Literal["pass", "fail", "skip"] = "pass"
