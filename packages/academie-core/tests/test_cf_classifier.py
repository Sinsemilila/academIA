"""Tier 2 BIPED Step 1 — CF classifier tests.

Covers :
- Prompt assembly with cf-taxonomy.yaml grounding
- Rule-based fallback when LLM unavailable
- Tier extraction from errors_detected
- Output schema validation

Does NOT make live LLM calls (mocks httpx) — keeps test suite fast + offline.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from academie_core.pedagogy.cf_classifier import (
    CF_MOVES_BIPED,
    _build_classifier_prompt,
    _first_error_family,
    _highest_tier_in_errors,
    _rule_based_fallback,
    classify_cf,
    classify_cf_sync,
)


# ── Static helpers ──────────────────────────────────────────────────────


def test_cf_moves_biped_is_10_class():
    assert len(CF_MOVES_BIPED) == 10
    assert "silent" in CF_MOVES_BIPED
    assert "implicit_recast" in CF_MOVES_BIPED
    assert "prompt_plus_remediation" in CF_MOVES_BIPED
    assert "explicit_correction" in CF_MOVES_BIPED
    # explicit_recast dropped per Q3 decision (data starvation, handled step 2)
    assert "explicit_recast" not in CF_MOVES_BIPED
    # old name dropped (Q1 rename)
    assert "metalinguistic_feedback" not in CF_MOVES_BIPED


def test_highest_tier_priority():
    errors = [{"tier": "T2"}, {"tier": "T3"}, {"tier": "T1"}]
    assert _highest_tier_in_errors(errors) == "T3"
    assert _highest_tier_in_errors([{"tier": "T4"}, {"tier": "T1"}]) == "T4"
    assert _highest_tier_in_errors([]) is None
    assert _highest_tier_in_errors(None) is None


def test_first_error_family():
    assert _first_error_family([{"family": "verb_tense"}]) == "verb_tense"
    assert _first_error_family([]) is None
    assert _first_error_family(None) is None


# ── Prompt assembly ─────────────────────────────────────────────────────


def test_build_classifier_prompt_uses_cf_taxonomy():
    """When cf-taxonomy.yaml is loaded, prompt should reference Lyster moves."""
    prompt = _build_classifier_prompt("A1", "en")
    assert "A1" in prompt
    assert "EN" in prompt
    # Expect at least 1 cf_move from taxonomy in the prompt
    found_moves = [m for m in CF_MOVES_BIPED if m in prompt]
    assert len(found_moves) >= 3, f"Expected ≥3 moves in prompt, got: {found_moves}"


def test_build_classifier_prompt_filters_contraindicated():
    """At A1, explicit_correction is contraindicated per cf-taxonomy.yaml."""
    prompt = _build_classifier_prompt("A1", "en")
    # explicit_correction at A1 should be filtered out (contraindicated)
    # Check : it should NOT appear as a "move available" line
    # (might appear in counter_indications context from another move, but as a primary listing it should be absent)
    # Heuristic : count occurrences of the exact "**explicit_correction**" markdown bold marker
    assert prompt.count("**explicit_correction**") == 0


# ── Rule-based fallback ─────────────────────────────────────────────────


def test_rule_fallback_no_errors_returns_silent():
    result = _rule_based_fallback(errors_detected=None, level="A1")
    assert result["cf_move"] == "silent"
    assert result["source"] == "rule"
    assert result["target_concept"] == "none"


def test_rule_fallback_a1_t3_returns_implicit_recast():
    """Per TIER_TO_FEEDBACK_BY_LEVEL: A1 + T3 → implicit_recast."""
    errors = [{"family": "verb_tense", "tier": "T3", "code": "V:TENSE"}]
    result = _rule_based_fallback(errors_detected=errors, level="A1")
    assert result["cf_move"] == "implicit_recast"
    assert result["target_concept"] == "verb_tense"


def test_rule_fallback_b2_t4_returns_prompt_plus_remediation():
    """T4 always → prompt_plus_remediation per rubric."""
    errors = [{"family": "word_order", "tier": "T4", "code": "WO"}]
    result = _rule_based_fallback(errors_detected=errors, level="B2")
    assert result["cf_move"] == "prompt_plus_remediation"


def test_rule_fallback_c1_t3_returns_metalinguistic():
    """C1 + T3 → metalinguistic per CEFR-stratified rubric."""
    errors = [{"family": "verb_tense", "tier": "T3"}]
    result = _rule_based_fallback(errors_detected=errors, level="C1")
    assert result["cf_move"] == "metalinguistic"


def test_rule_fallback_unknown_level_returns_silent():
    result = _rule_based_fallback(errors_detected=[], level="UNKNOWN")
    assert result["cf_move"] == "silent"


# ── classify_cf with mocked LLM (sync wrapper, no pytest-asyncio needed) ───


def _make_mock_response(content: str):
    """Build a mock httpx response with the given message content."""
    mock = AsyncMock()
    mock.json = lambda: {"choices": [{"message": {"content": content}}]}
    mock.raise_for_status = lambda: None
    return mock


def test_classify_cf_llm_success_high_confidence():
    """When LLM returns high-confidence valid JSON, use LLM output."""
    mock_response = _make_mock_response(
        '{"cf_move": "implicit_recast", "target_concept": "past_simple",'
        ' "confidence": 0.9, "reasoning": "A2 T2 verb tense"}'
    )

    async def mock_post(*args, **kwargs):
        return mock_response

    with patch("httpx.AsyncClient.post", new=mock_post):
        result = classify_cf_sync(
            learner_text="Yesterday I goed",
            errors_detected=[{"family": "verb_tense", "tier": "T2"}],
            level="A2",
            lang="en",
        )

    assert result["cf_move"] == "implicit_recast"
    assert result["source"] == "llm"
    assert result["confidence"] == 0.9


def test_classify_cf_llm_low_confidence_fallback_to_rule():
    """When LLM confidence below threshold, fall back to rule-based."""
    mock_response = _make_mock_response(
        '{"cf_move": "elicitation", "target_concept": "x",'
        ' "confidence": 0.4, "reasoning": "uncertain"}'
    )

    async def mock_post(*args, **kwargs):
        return mock_response

    with patch("httpx.AsyncClient.post", new=mock_post):
        result = classify_cf_sync(
            learner_text="Yesterday I goed",
            errors_detected=[{"family": "verb_tense", "tier": "T2"}],
            level="A2",
            lang="en",
        )

    # Fell back to rule : A2 + T2 → implicit_recast (per TIER_TO_FEEDBACK_BY_LEVEL)
    assert result["cf_move"] == "implicit_recast"
    assert result["source"] == "rule"
    assert "low_confidence" in result["reasoning"]


def test_classify_cf_llm_invalid_enum_fallback():
    """When LLM returns invalid cf_move enum value, fall back to rule."""
    mock_response = _make_mock_response(
        '{"cf_move": "fictional_move", "target_concept": "x",'
        ' "confidence": 0.95, "reasoning": "y"}'
    )

    async def mock_post(*args, **kwargs):
        return mock_response

    with patch("httpx.AsyncClient.post", new=mock_post):
        result = classify_cf_sync(
            learner_text="...",
            errors_detected=[{"family": "x", "tier": "T3"}],
            level="B1",
            lang="en",
        )

    assert result["cf_move"] in CF_MOVES_BIPED  # rule-based output is valid
    assert result["source"] == "rule"
    assert "ValueError" in result["reasoning"]


def test_classify_cf_http_error_fallback():
    """When HTTP call fails (timeout, 5xx), fall back to rule."""
    import httpx

    async def mock_post_raises(*args, **kwargs):
        raise httpx.TimeoutException("simulated timeout")

    with patch("httpx.AsyncClient.post", new=mock_post_raises):
        result = classify_cf_sync(
            learner_text="...",
            errors_detected=[{"tier": "T3", "family": "verb_tense"}],
            level="A2",
            lang="en",
        )

    assert result["source"] == "rule"
    # A2 + T3 → elicitation per rule
    assert result["cf_move"] == "elicitation"


# ── Sync wrapper ─────────────────────────────────────────────────────────


def test_classify_cf_sync_runs_async():
    """Sync wrapper should work in non-async context."""
    import httpx

    async def mock_post_raises(*args, **kwargs):
        raise httpx.TimeoutException("offline")

    with patch("httpx.AsyncClient.post", new=mock_post_raises):
        result = classify_cf_sync(
            learner_text="test",
            errors_detected=None,
            level="A1",
            lang="en",
        )
    # Falls back, A1 + no errors → silent
    assert result["cf_move"] == "silent"
    assert result["source"] == "rule"
