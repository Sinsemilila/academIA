"""Sprint 5 Phase 4 — Content pack ES validation tests.

Verifies all ES YAML data loads cleanly and LanguageDomain('es') instantiates.
These tests ensure the content pack doesn't break when merged (even before
native speaker review activates the flag).

Run: pytest packages/academie-core/tests/test_es_content_pack.py
"""
from __future__ import annotations

import pytest

pytest.importorskip("yaml")
pytest.importorskip("pydantic")


def test_rubrics_es_loads():
    from academie_core.data.loader import load_rubrics
    rubrics = load_rubrics("es")
    assert rubrics is not None, "rubrics/es.yaml missing"
    assert set(rubrics.keys()) >= {"A1", "A2", "B1", "B2", "C1", "C2"}, \
        f"rubrics es must cover A1-C2, got {list(rubrics.keys())}"
    # Sanity: each rubric has at least 200 chars
    for level, content in rubrics.items():
        assert len(content) >= 200, f"rubric {level} too short: {len(content)} chars"


def test_fewshots_es_loads():
    from academie_core.data.loader import load_fewshots
    fewshots = load_fewshots("es")
    assert fewshots is not None
    assert len(fewshots) >= 10, f"expected ≥10 fewshots, got {len(fewshots)}"
    # Every fewshot has required fields
    for fs in fewshots:
        assert {"id", "level", "type", "learner", "teacher"} <= set(fs.keys()), \
            f"fewshot missing fields: {fs}"


def test_concept_hints_es_loads():
    from academie_core.data.loader import load_concept_hints
    hints = load_concept_hints("es")
    assert len(hints) >= 20, f"expected ≥20 concept hints, got {len(hints)}"
    # Some key ES concepts must be present
    for required in ["ser_estar_basico", "subjuntivo_presente", "por_para"]:
        assert required in hints, f"missing key concept: {required}"


def test_cefr_diagnostics_es_loads():
    from academie_core.data.loader import load_cefr_diagnostics
    diags = load_cefr_diagnostics("es")
    assert "paliers_first_question" in diags
    assert "paliers_reference" in diags
    assert "microtasks" in diags
    assert "persona" in diags
    assert diags["persona"]["target_name"] == "Español"
    assert "español" in diags["persona"]["target_prof"].lower()


def test_l1_transfers_fr_to_es_loads():
    from academie_core.data.loader import load_l1_transfers
    transfers = load_l1_transfers("fr", "es")
    assert len(transfers) >= 5, f"expected ≥5 transfer patterns, got {len(transfers)}"
    families = [t[0] for t in transfers]
    assert "por_para" in families or "ser_estar" in families, \
        "expected FR→ES core patterns present"


def test_curriculum_es_yaml_present():
    from pathlib import Path
    path = Path(__file__).parent.parent / "academie_core" / "data" / "curriculum_es.yaml"
    assert path.exists(), f"curriculum_es.yaml missing at {path}"
    import yaml
    data = yaml.safe_load(path.read_text())
    assert data["domain"] == "es"
    assert set(data.keys()) >= {"domain", "A1", "A2", "B1", "B2", "C1", "C2"}


def test_rules_es_detects_core_errors():
    """Verify rules_es.py detects the 6-7 baseline FR→ES errors."""
    from academie_core.taxonomy.rules_es import detect_errors_es

    # Ser/estar confusion
    r = detect_errors_es("Yo soy cansado hoy")
    assert any(x.error_code == "V:SER_ESTAR" for x in r)

    # Article before profession
    r = detect_errors_es("Soy un profesor")
    assert any(x.error_code == "ART:PROF" for x in r)

    # por/para
    r = detect_errors_es("gracias para tu ayuda")
    assert any(x.error_code == "PREP:POR_PARA" for x in r)

    # Missing ñ
    r = detect_errors_es("Estoy aqui manana")
    assert any(x.error_code == "ORTH:NY" for x in r)

    # Missing ¿
    r = detect_errors_es("Cuanto cuesta?")
    assert any(x.error_code == "PUNCT:INTERROG" for x in r)

    # False friend
    r = detect_errors_es("Estoy embarazada delante de todos")
    assert any(x.error_code == "LEX:FALSE" for x in r)


def test_language_domain_es_instantiates():
    from academie_core.domain.language import LanguageDomain
    d = LanguageDomain("es")
    assert d.lang_target == "es"
    assert d.id == "lang:es"


def test_rules_dispatch_routes_es_to_rules_es():
    from academie_core.taxonomy.rules import detect_errors
    # Sanity: the dispatch in rules.detect_errors forwards to rules_es
    results = detect_errors("gracias para tu ayuda", lang="es")
    assert any(r.error_code == "PREP:POR_PARA" for r in results)


def test_llm_dispatch_es_uses_base_model():
    from academie_core.taxonomy.llm import (
        ANALYSIS_MODEL_BY_LANG, SYSTEM_PROMPT_BY_LANG, USER_PROMPT_TEMPLATE_BY_LANG,
    )
    assert ANALYSIS_MODEL_BY_LANG.get("es") == "gpt-4o-mini"
    assert "es" in SYSTEM_PROMPT_BY_LANG
    assert "es" in USER_PROMPT_TEMPLATE_BY_LANG
    assert "español" in SYSTEM_PROMPT_BY_LANG["es"].lower() or \
           "spanish" in SYSTEM_PROMPT_BY_LANG["es"].lower()
