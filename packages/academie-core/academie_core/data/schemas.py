"""Session 39 Block 2a — Pydantic v2 schemas for every YAML data pack.

Each pack used by the tutoring pipeline gets a BaseModel here. Loading
a malformed YAML via the matching schema raises `ValidationError` at
test time so a broken data pack never reaches prod.

Philosophy :
  - Strict types on fields whose drift would cause silent misbehavior
    (e.g. multiplier range, CEFR level enum, mandatory identifiers).
  - Lenient on free-form prose fields (rubric bodies, few-shot teacher
    replies) — those evolve often and no schema can police style.
  - Test-time only : no pydantic validation in the prod loader hot
    path. See `tests/test_yaml_schema.py` for the runner.

Mirror file discovery logic : tests import these and iterate over the
`_LANGUAGE_CODES` constant in `loader.py`.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CEFRLevel = Literal["A1", "A2", "B1", "B2", "C1", "C2"]
MicroLessonBand = Literal["A1", "A2", "B1"]
FewshotType = Literal[
    "implicit_recast", "silent", "prompt_plus_remediation",
    "elicitation", "metalinguistic", "stylistic_nuance",
    "explicit_correction",
]
ExamItemType = Literal["fill", "transform", "choice", "produce_short"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Lax(BaseModel):
    # Some packs carry free-form comment keys; allow extra so forward-compat
    # additions don't break existing tests.
    model_config = ConfigDict(extra="allow")


# ── Rubrics pack ─────────────────────────────────────────────────────

class RubricPack(_Strict):
    """rubrics/{lang}.yaml — one rubric prose per CEFR level."""
    rubrics: dict[CEFRLevel, str]

    @field_validator("rubrics")
    @classmethod
    def _all_levels_present(cls, v: dict[str, str]) -> dict[str, str]:
        missing = {"A1", "A2", "B1", "B2", "C1", "C2"} - set(v.keys())
        if missing:
            raise ValueError(f"missing CEFR levels: {sorted(missing)}")
        for lvl, body in v.items():
            if len(body) < 100:
                raise ValueError(f"rubric {lvl} is suspiciously short: {len(body)} chars")
        return v


# ── Fewshots pack ────────────────────────────────────────────────────

class FewshotEntry(_Strict):
    id: str = Field(..., min_length=4)
    level: CEFRLevel
    type: FewshotType
    learner: str = Field(..., min_length=5)
    teacher: str = Field(..., min_length=5)


class FewshotPack(_Strict):
    fewshots: list[FewshotEntry]

    @field_validator("fewshots")
    @classmethod
    def _all_levels_covered(cls, v: list[FewshotEntry]) -> list[FewshotEntry]:
        levels = {e.level for e in v}
        missing = {"A1", "A2", "B1", "B2", "C1", "C2"} - levels
        if missing:
            raise ValueError(f"fewshots missing levels: {sorted(missing)}")
        ids = [e.id for e in v]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate fewshot ids")
        return v


# ── Concept hints pack ───────────────────────────────────────────────

class ConceptHintsPack(_Lax):
    """concept_hints/{lang}.yaml — flat {concept_key: hint_string}.

    Schema is essentially "dict of strings" — we use Lax + a post-init
    check so new keys don't cause drift false-positives.
    """

    @classmethod
    def validate_mapping(cls, raw: dict) -> None:
        if not isinstance(raw, dict):
            raise ValueError("concept_hints must be a dict")
        if not raw:
            raise ValueError("concept_hints must not be empty")
        for k, v in raw.items():
            if not isinstance(k, str) or not k:
                raise ValueError(f"bad key: {k!r}")
            if not isinstance(v, str) or len(v) < 5:
                raise ValueError(f"hint for {k!r} too short: {v!r}")


# ── CEFR diagnostics pack ────────────────────────────────────────────

class CEFRDiagnosticsPack(_Lax):
    paliers_first_question: dict[str, str]
    paliers_reference: dict[str, str]

    @field_validator("paliers_first_question", "paliers_reference")
    @classmethod
    def _nonempty_strings(cls, v: dict[str, str]) -> dict[str, str]:
        for k, vv in v.items():
            if not vv or len(vv) < 10:
                raise ValueError(f"palier {k!r} empty/short: {vv!r}")
        return v


# ── Curriculum pack ──────────────────────────────────────────────────

class CurriculumLevel(_Lax):
    description: str = Field(..., min_length=20)
    concept_keys: list[str] = Field(..., min_length=1)
    concept_weights: dict[str, int]
    concept_groups: dict[str, list[str]]


class CurriculumPack(_Lax):
    """curriculum_{lang}.yaml — domain + per-CEFR blocks.

    Lax on root because the domain key is dynamic (`en`, `es`, ...);
    we validate structure manually via `validate_mapping`.
    """

    @classmethod
    def validate_mapping(cls, raw: dict) -> None:
        if "domain" not in raw:
            raise ValueError("missing 'domain' root key")
        for lvl in ("A1", "A2", "B1", "B2", "C1", "C2"):
            if lvl not in raw:
                raise ValueError(f"missing level block: {lvl}")
            CurriculumLevel.model_validate(raw[lvl])
            block = raw[lvl]
            keys = set(block["concept_keys"])
            # every weight key must be a declared concept
            stray = set(block["concept_weights"]) - keys
            if stray:
                raise ValueError(f"{lvl} concept_weights references unknown concepts: {stray}")
            # every grouped concept must be declared
            grouped = {c for lst in block["concept_groups"].values() for c in lst}
            stray = grouped - keys
            if stray:
                raise ValueError(f"{lvl} concept_groups references unknown concepts: {stray}")


# ── Micro-lesson pack ────────────────────────────────────────────────

class MicroLessonFamily(_Strict):
    A1: str
    A2: str
    B1: str

    @field_validator("A1")
    @classmethod
    def _a1_no_metalinguistic(cls, v: str) -> str:
        # Lyster-compliant A1 rubric — banned terms (language-agnostic
        # sample, can be extended per-lang).
        banned = ["past simple", "past participle", "auxiliary",
                  "propiedades inherentes", "clasificatorias"]
        low = v.lower()
        hits = [b for b in banned if b in low]
        if hits:
            raise ValueError(f"A1 variant contains banned metalinguistic term(s): {hits}")
        return v


class MicroLessonPack(_Lax):
    """micro_lessons/{lang}.yaml — family → {A1, A2, B1}."""

    @classmethod
    def validate_mapping(cls, raw: dict) -> None:
        if not isinstance(raw, dict) or not raw:
            raise ValueError("micro_lessons must be a non-empty dict")
        for family, bands in raw.items():
            if not isinstance(bands, dict):
                raise ValueError(f"family {family!r} must be a dict")
            MicroLessonFamily.model_validate(bands)


# ── Mini-exam banks ──────────────────────────────────────────────────

class MiniExamItem(_Lax):
    id: str = Field(..., min_length=4)
    type: ExamItemType
    prompt: str = Field(..., min_length=10)
    expected_regex: str = Field(..., min_length=1)


class MiniExamBank(_Strict):
    level: CEFRLevel
    lang: str = Field(..., min_length=2, max_length=5)
    description: str
    items: list[MiniExamItem] = Field(..., min_length=1)

    @field_validator("items")
    @classmethod
    def _ids_unique(cls, v: list[MiniExamItem]) -> list[MiniExamItem]:
        ids = [e.id for e in v]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate mini_exam item ids")
        return v


# ── L1 transfer pack ─────────────────────────────────────────────────

class L1TransferEntry(_Strict):
    family: str = Field(..., min_length=2)
    multiplier: float = Field(..., ge=1.0, le=2.0)
    description: str = Field(..., min_length=20)


class L1TransferPack(_Strict):
    l1: str = Field(..., min_length=2, max_length=5)
    target: str = Field(..., min_length=2, max_length=5)
    transfers: list[L1TransferEntry] = Field(..., min_length=1)


# ── L1 names pack ────────────────────────────────────────────────────

class L1NamesPack(_Strict):
    names: dict[str, str]

    @field_validator("names")
    @classmethod
    def _iso_codes(cls, v: dict[str, str]) -> dict[str, str]:
        for code, name in v.items():
            if not (2 <= len(code) <= 3):
                raise ValueError(f"bad ISO code: {code!r}")
            if not name or len(name) < 3:
                raise ValueError(f"empty/short name for {code}: {name!r}")
        return v
