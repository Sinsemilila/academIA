"""Session 39 Block 2a — YAML schema validation suite.

Loads every data pack YAML through its pydantic schema. A broken field
(missing key, wrong type, out-of-range value, banned metalinguistic
term in an A1 micro-lesson, etc.) fails the test before the data
ever reaches prod.

Parametric on `_LANGUAGE_CODES` : EN + ES must pass, Wave 2 langs
(IT/DE/JA/RU) skip gracefully if the file doesn't exist yet — the
moment someone drops a `curriculum_it.yaml` in place, the test
automatically starts validating it.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from academie_core.data.schemas import (
    CEFRDiagnosticsPack,
    ConceptHintsPack,
    CurriculumPack,
    FewshotPack,
    L1NamesPack,
    L1TransferPack,
    MicroLessonPack,
    MiniExamBank,
    RubricPack,
)

DATA_DIR = Path(__file__).resolve().parents[1] / "academie_core" / "data"
LANGS = ["en", "es", "it", "de", "ja", "ru"]
ACTIVE_LANGS = ["en", "es"]  # tighter gate for EN+ES


def _load(path: Path) -> dict | None:
    if not path.exists():
        return None
    with path.open() as f:
        return yaml.safe_load(f)


# ── Rubrics ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("lang", LANGS)
def test_rubrics_schema(lang):
    raw = _load(DATA_DIR / "rubrics" / f"{lang}.yaml")
    if raw is None:
        if lang in ACTIVE_LANGS:
            pytest.fail(f"rubrics/{lang}.yaml missing for active lang")
        pytest.skip(f"no rubrics/{lang}.yaml (Wave 2+)")
    RubricPack.model_validate(raw)


# ── Fewshots ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("lang", LANGS)
def test_fewshots_schema(lang):
    raw = _load(DATA_DIR / "fewshots" / f"{lang}.yaml")
    if raw is None:
        if lang in ACTIVE_LANGS:
            pytest.fail(f"fewshots/{lang}.yaml missing for active lang")
        pytest.skip(f"no fewshots/{lang}.yaml (Wave 2+)")
    FewshotPack.model_validate(raw)


# ── Concept hints ─────────────────────────────────────────────────────

@pytest.mark.parametrize("lang", LANGS)
def test_concept_hints_schema(lang):
    raw = _load(DATA_DIR / "concept_hints" / f"{lang}.yaml")
    if raw is None:
        if lang in ACTIVE_LANGS:
            pytest.fail(f"concept_hints/{lang}.yaml missing for active lang")
        pytest.skip(f"no concept_hints/{lang}.yaml (Wave 2+)")
    ConceptHintsPack.validate_mapping(raw)


# ── CEFR diagnostics ──────────────────────────────────────────────────

@pytest.mark.parametrize("lang", LANGS)
def test_cefr_diagnostics_schema(lang):
    raw = _load(DATA_DIR / "cefr_diagnostics" / f"{lang}.yaml")
    if raw is None:
        if lang in ACTIVE_LANGS:
            pytest.fail(f"cefr_diagnostics/{lang}.yaml missing for active lang")
        pytest.skip(f"no cefr_diagnostics/{lang}.yaml (Wave 2+)")
    CEFRDiagnosticsPack.model_validate(raw)


# ── Curriculum ────────────────────────────────────────────────────────

@pytest.mark.parametrize("lang", LANGS)
def test_curriculum_schema(lang):
    raw = _load(DATA_DIR / f"curriculum_{lang}.yaml")
    if raw is None:
        if lang in ACTIVE_LANGS:
            pytest.fail(f"curriculum_{lang}.yaml missing for active lang")
        pytest.skip(f"no curriculum_{lang}.yaml (Wave 2+)")
    CurriculumPack.validate_mapping(raw)


# ── Micro-lessons ─────────────────────────────────────────────────────

@pytest.mark.parametrize("lang", LANGS)
def test_micro_lessons_schema(lang):
    raw = _load(DATA_DIR / "micro_lessons" / f"{lang}.yaml")
    if raw is None:
        if lang in ACTIVE_LANGS:
            pytest.fail(f"micro_lessons/{lang}.yaml missing for active lang")
        pytest.skip(f"no micro_lessons/{lang}.yaml (Wave 2+)")
    MicroLessonPack.validate_mapping(raw)


# ── Mini-exam banks ───────────────────────────────────────────────────

@pytest.mark.parametrize("lang", ACTIVE_LANGS)
@pytest.mark.parametrize("level", ["A1", "A2", "B1", "B2"])
def test_mini_exam_bank_schema(lang, level):
    path = DATA_DIR / "mini_exam" / f"{lang}_{level}.yaml"
    if not path.exists():
        pytest.skip(f"no {path.name}")
    raw = _load(path)
    MiniExamBank.model_validate(raw)


# ── L1 transfer packs ─────────────────────────────────────────────────

L1_TARGETS = ["en", "es", "it", "de", "ja", "ru"]


@pytest.mark.parametrize("target", L1_TARGETS)
def test_l1_transfer_schema(target):
    path = DATA_DIR / "l1_transfer" / f"fr_to_{target}.yaml"
    if not path.exists():
        pytest.skip(f"no fr_to_{target}.yaml")
    raw = _load(path)
    L1TransferPack.model_validate(raw)


def test_l1_names_schema():
    raw = _load(DATA_DIR / "l1_transfer" / "l1_names.yaml")
    assert raw is not None, "l1_names.yaml missing"
    L1NamesPack.model_validate(raw)
