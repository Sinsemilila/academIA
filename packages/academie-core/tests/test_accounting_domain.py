"""S57 — basic tests for AccountingDomain Phase 1 stub.

Phase 2 Mode A étoffera avec real detect_errors/score_tier/etc. Phase 1 Mode B
validation : instantiation + Protocol-compatible signatures + safe stub returns.
"""
from __future__ import annotations

import pytest

from academie_core.domain.accounting import AccountingDomain
from academie_core.domain.language import LanguageDomain


def test_accounting_domain_instantiates():
    """AccountingDomain instantiates without crash on default variant."""
    ad = AccountingDomain()
    assert ad.id == "accounting:compta_fr"
    assert ad.variant == "compta_fr"
    assert ad.lang_target == "compta_fr"  # alias for chat_router compatibility


def test_accounting_domain_custom_variant():
    """Custom variant str is honored."""
    ad = AccountingDomain("compta_be")  # Belgique future
    assert ad.id == "accounting:compta_be"


def test_detect_errors_phase1_stub():
    """Phase 1 Mode B = stub. Phase 2 Mode A = real rules_compta."""
    ad = AccountingDomain()
    assert ad.detect_errors("Débit 6061 100€ Crédit 401 100€") == []


def test_score_tier_phase1_stub():
    """Phase 1 stub returns benign T1 dict."""
    ad = AccountingDomain()
    out = ad.score_tier("COMPTA:DEBIT_CREDIT_INVERSE", "N1")
    assert out["tier"] == "T1"
    assert out["error_code"] == "COMPTA:DEBIT_CREDIT_INVERSE"
    assert out["level"] == "N1"


def test_compute_progression_phase1_stub():
    """Phase 1 stub returns empty dict."""
    ad = AccountingDomain()
    assert ad.compute_progression([], "N1", [], {}) == {}


def test_build_dynamic_sections_phase1_keys():
    """Phase 1 stub returns dict with 8 keys (compat pipeline existant)."""
    ad = AccountingDomain()
    sections = ad.build_dynamic_sections(None)
    expected_keys = {
        "rubric_for_level",
        "fewshots_block",
        "dosage_block",
        "level_reminder_inject",
        "drift_validation_request",
        "module_context_inject",
        "output_schema_block",
        "concept_hints_json",
    }
    assert set(sections.keys()) == expected_keys
    # All values empty Phase 1 (chatflow Dify autonome ignore)
    assert all(v in ("", "[]") for v in sections.values())


def test_parse_response_phase1_passthrough():
    """Phase 1 = passthrough. Phase 2 Mode A pourrait extraire écritures structurées."""
    ad = AccountingDomain()
    out = ad.parse_response("test response")
    assert out == {"raw": "test response"}


def test_pedagogical_feedback_phase1_stub():
    """Phase 1 Mode B side-chat n'évalue pas backend."""
    ad = AccountingDomain()
    feedback = ad.pedagogical_feedback([{"error_code": "X", "tier": "T1"}], "N1")
    assert feedback == {
        "to_correct": [],
        "silenced": [],
        "dosage_budget": 0,
        "feedback_types": {},
    }


def test_build_system_prompt_phase1_empty():
    """Phase 1 Dify chatflow assemble system_prompt côté Dify."""
    ad = AccountingDomain()
    assert ad.build_system_prompt(None) == ""


def test_snapshot_phase3_not_implemented():
    """snapshot deferred Phase 3+."""
    ad = AccountingDomain()
    with pytest.raises(NotImplementedError, match="Phase 3"):
        ad.snapshot(None, None)


def test_no_regression_language_domain():
    """LanguageDomain coexists with AccountingDomain."""
    ld = LanguageDomain("en")
    ad = AccountingDomain("compta_fr")
    assert ld.id != ad.id
    assert ld.lang_target == "en"
    assert ad.variant == "compta_fr"
