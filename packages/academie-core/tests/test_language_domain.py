"""Sprint 4 Phase D — unit tests pour LanguageDomain.

Valide :
  - instantiation + identité
  - delegate taxonomy (detect_errors, score_tier)
  - delegate pedagogy (build_dynamic_sections, parse_response, pedagogical_feedback)
  - Protocol runtime-checkable (isinstance check)
  - build_system_prompt returns "" (v1 stub)
  - snapshot raises NotImplementedError
"""
from __future__ import annotations

import os

import pytest


# V2 scoring YAML path may require these env vars set to match prod defaults.
# scoring.py reads USE_V2_TOLERANCE/USE_V2_SCORING at import time — set before import.
os.environ.setdefault("USE_V2_TOLERANCE", "true")
os.environ.setdefault("USE_V2_SCORING", "true")


def test_instantiate_default():
    from academie_core.domain.language import LanguageDomain
    d = LanguageDomain()
    assert d.id == "lang:en"
    assert d.lang_target == "en"


def test_instantiate_spanish():
    from academie_core.domain.language import LanguageDomain
    d = LanguageDomain("es")
    assert d.id == "lang:es"
    assert d.lang_target == "es"


def test_unknown_lang_does_not_crash():
    """Instantiation with unknown ISO code is safe (no data-file load at __init__)."""
    from academie_core.domain.language import LanguageDomain
    d = LanguageDomain("xx")
    assert d.id == "lang:xx"


def test_detect_errors_returns_list():
    from academie_core.domain.language import LanguageDomain
    d = LanguageDomain("en")
    errs = d.detect_errors("I have went to Paris yesterday")
    assert isinstance(errs, list)
    # RuleDetection for this sentence may or may not fire — just check shape.
    for e in errs:
        assert hasattr(e, "error_code")
        assert hasattr(e, "original_text")


def test_score_tier_returns_enriched_dict():
    from academie_core.domain.language import LanguageDomain
    d = LanguageDomain("en")
    enriched = d.score_tier("V:TENSE", "B1")
    assert isinstance(enriched, dict)
    assert "tier" in enriched
    assert "gravity_linguistic" in enriched


def test_build_dynamic_sections_8_keys():
    from academie_core.domain.language import LanguageDomain
    from academie_core.pedagogy.teacher_prompt import PromptContext
    d = LanguageDomain("en")
    ctx = PromptContext(level="B1", turn_count=3, l1="fr")
    sections = d.build_dynamic_sections(ctx)
    expected = {"rubric_for_level", "fewshots_block", "dosage_block",
                "level_reminder_inject", "drift_validation_request",
                "l1_watch", "spaced_retrieval_today", "output_schema_block"}
    assert expected.issubset(set(sections.keys()))
    assert "L1 WATCH" in sections["l1_watch"]
    assert "French" in sections["l1_watch"]


def test_parse_response_valid_json():
    from academie_core.domain.language import LanguageDomain
    d = LanguageDomain("en")
    raw = '<output>{"feedback":"great answer","reasoning":"T2 recast","tier_applied":["T2"]}</output>'
    parsed = d.parse_response(raw)
    assert parsed.parse_ok is True
    assert parsed.feedback == "great answer"
    assert "T2" in parsed.tier_applied


def test_parse_response_malformed_graceful():
    from academie_core.domain.language import LanguageDomain
    d = LanguageDomain("en")
    parsed = d.parse_response("plain text without output tags")
    assert parsed.parse_ok is False
    assert parsed.feedback  # fallback renders raw as feedback


def test_pedagogical_feedback_arbitrates_dosage():
    from academie_core.domain.language import LanguageDomain
    d = LanguageDomain("en")
    errors = [
        {"error_code": "PREP", "family": "preposition", "tier": "T3",
         "gravity_linguistic": 0.6, "gravity_communicative": 0.3, "gravity_social": 0},
        {"error_code": "V:TENSE", "family": "verb_tense", "tier": "T4",
         "gravity_linguistic": 0.8, "gravity_communicative": 0.5, "gravity_social": 0},
        {"error_code": "SPELL", "family": "surface", "tier": "T1",
         "gravity_linguistic": 0.2, "gravity_communicative": 0, "gravity_social": 0},
    ]
    plan = d.pedagogical_feedback(errors, "B1")
    assert "to_correct" in plan
    assert "silenced" in plan
    assert plan["dosage_budget"] == 3  # B1 default
    # T4 always included, T1 always silenced
    to_correct_codes = [e["error_code"] for e in plan["to_correct"]]
    assert "V:TENSE" in to_correct_codes
    assert "SPELL" not in to_correct_codes
    # feedback_types mapping non-empty
    assert len(plan["feedback_types"]) == len(plan["to_correct"])


def test_protocol_runtime_checkable():
    """LanguageDomain satisfies Domain Protocol via duck typing."""
    from academie_core.domain.base import Domain
    from academie_core.domain.language import LanguageDomain
    d = LanguageDomain("en")
    assert isinstance(d, Domain)


def test_build_system_prompt_stub_empty():
    """v1 stub — Dify template assembles, webapp doesn't compose."""
    from academie_core.domain.language import LanguageDomain
    from academie_core.pedagogy.teacher_prompt import PromptContext
    d = LanguageDomain("en")
    ctx = PromptContext(level="B1", turn_count=1)
    assert d.build_system_prompt(ctx) == ""


def test_snapshot_raises_not_implemented():
    from academie_core.domain.language import LanguageDomain
    d = LanguageDomain("en")
    with pytest.raises(NotImplementedError):
        d.snapshot(session=None, context=None)


def test_re_exports_via_domain_init():
    """LanguageDomain importable from package root too."""
    from academie_core.domain import LanguageDomain, Domain
    d = LanguageDomain("en")
    assert isinstance(d, Domain)
