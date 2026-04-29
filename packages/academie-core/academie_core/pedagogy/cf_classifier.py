"""Tier 2 BIPED Step 1 — CF classifier.

Lightweight LLM classifier that recommends a cf_move for the upcoming Teacher
response. Augments rule-based TIER_TO_FEEDBACK_BY_LEVEL mapping by :
  - Resolving ambiguity when multiple errors detected with conflicting tier→cf_move
  - Self-grading confidence (>=0.7 = use classifier output, else fallback to rule)
  - Identifying target_concept for step 2 generator context

Consumes Lyster 2007 cf-taxonomy.yaml (cf_appropriateness CEFR-stratified,
counter_indications) via load_extracted for prompt grounding.

Architecture (ADR-014 + cf-taxonomy-gap-2026-04-29) :
  - Input : learner_text + errors_detected + level + turn_count + lang
  - LLM call : LiteLLM proxy (gemini-flash-lite default, fast/cheap)
  - Output : {cf_move, target_concept, confidence, reasoning, source}
  - Fallback : if confidence < 0.7 OR LLM fails, rule-based TIER_TO_FEEDBACK_BY_LEVEL

10-class enum (drops explicit_recast, kept in schema for Lyster fidelity) :
  silent, implicit_recast, full_recast, partial_recast,
  clarification_request, repetition, metalinguistic,
  elicitation, prompt_plus_remediation, explicit_correction
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

from academie_core.data.loader import load_extracted

_log = logging.getLogger("cf_classifier")

# 10-class BIPED enum (drops explicit_recast vs Lyster 11; data starvation).
CF_MOVES_BIPED: tuple[str, ...] = (
    "silent",
    "implicit_recast",
    "full_recast",
    "partial_recast",
    "clarification_request",
    "repetition",
    "metalinguistic",
    "elicitation",
    "prompt_plus_remediation",
    "explicit_correction",
)

LITELLM_URL = os.environ.get(
    "LITELLM_URL", "http://127.0.0.1:4000/v1/chat/completions"
)
CLASSIFIER_MODEL = os.environ.get("CF_CLASSIFIER_MODEL", "gemini-3-1-flash-lite")
CONFIDENCE_THRESHOLD = float(os.environ.get("CF_CLASSIFIER_CONFIDENCE_THRESHOLD", "0.7"))


# ── Prompt assembly ─────────────────────────────────────────────────────


def _build_classifier_prompt(level: str, lang: str) -> str:
    """Assemble system prompt with cf-taxonomy.yaml grounding (Lyster 2007).

    Filters cf_moves by cefr_appropriateness[level] != contraindicated to
    reduce classification space at low levels (e.g. A1 excludes most C2
    metalinguistic-heavy moves)."""
    cf_tax = load_extracted("lyster-2007-counterbalanced-content", "cf-taxonomy")
    if cf_tax is None:
        return _minimal_prompt(level, lang)

    level_lower = level.lower()
    # AcademIA policy override : at low levels, explicit_correction is HARD BAN
    # per rubric (anti-pattern), even if Lyster cf_appropriateness reports `low`.
    POLICY_HARD_BAN: dict[str, set[str]] = {
        "a1": {"explicit_correction"},
        "a2": {"explicit_correction"},
        "b1": {"explicit_correction"},
    }
    hard_banned = POLICY_HARD_BAN.get(level_lower, set())

    appropriate_moves: list[dict[str, Any]] = []
    for move in cf_tax.get("cf_moves", []):
        # Drop moves not in BIPED enum (e.g. explicit_recast — Q3 decision)
        if move["id"] not in CF_MOVES_BIPED:
            continue
        # Drop AcademIA hard-ban moves at this level
        if move["id"] in hard_banned:
            continue
        appr = move.get("cefr_appropriateness", {}).get(level_lower, "medium")
        if appr == "contraindicated":
            continue
        appropriate_moves.append(
            {
                "id": move["id"],
                "definition": move["definition"][:240],
                "appropriateness": appr,
                "counter_indications": move.get("counter_indications", [])[:2],
            }
        )

    if not appropriate_moves:
        return _minimal_prompt(level, lang)

    moves_block = "\n".join(
        f"- **{m['id']}** ({m['appropriateness']} at {level}): {m['definition']}"
        + (
            f"\n  COUNTER-INDICATIONS: {'; '.join(m['counter_indications'])}"
            if m["counter_indications"]
            else ""
        )
        for m in appropriate_moves
    )

    return f"""You classify the optimal corrective feedback (CF) move for an AI language tutor.

Target language : {lang.upper()}
Learner level : {level}

Available CF moves at this level (Lyster 2007 taxonomy + AcademIA `silent` policy) :
{moves_block}

Decision protocol :
1. If learner text has no error, or errors are below tolerance threshold for {level} → `silent`
2. If error is on a target structure for {level} → choose move with `high` or `medium` appropriateness
3. If error is on a higher-level structure (above {level}) → prefer `silent` (avoid overwhelming)
4. Apply counter-indications strictly (e.g. avoid recast in meaning-oriented turns at low confidence)
5. T4 communicative breakdown always → `prompt_plus_remediation`

Output STRICT JSON (no prose, no code fences) :
{{
  "cf_move": "<one of the listed moves>",
  "target_concept": "<grammatical concept addressed, e.g. 'past_simple_irregular', 'definite_article', or 'none' if cf_move=silent>",
  "confidence": <float 0.0 to 1.0, your certainty>,
  "reasoning": "<one sentence justification>"
}}"""


def _minimal_prompt(level: str, lang: str) -> str:
    """Fallback prompt when cf-taxonomy.yaml unavailable (lazy ingestion not done)."""
    moves_str = ", ".join(CF_MOVES_BIPED)
    return (
        f"Classify CF move for a {lang.upper()} {level} learner.\n"
        f"Available moves : {moves_str}.\n"
        f"Output strict JSON: {{cf_move, target_concept, confidence, reasoning}}"
    )


# ── Main API ────────────────────────────────────────────────────────────


async def classify_cf(
    learner_text: str,
    errors_detected: list[dict[str, Any]] | None,
    level: str,
    turn_count: int = 0,
    lang: str = "en",
    timeout_s: float = 10.0,
) -> dict[str, Any]:
    """Classify recommended CF move for upcoming Teacher response.

    Returns dict with keys :
      - cf_move : one of CF_MOVES_BIPED
      - target_concept : str (grammatical concept) or "none"
      - confidence : float 0.0 to 1.0
      - reasoning : str (one sentence)
      - source : "llm" if LLM call succeeded with confidence>=threshold ; else "rule"

    On LLM failure (timeout, parse error, invalid enum, low confidence), falls
    back to rule-based TIER_TO_FEEDBACK_BY_LEVEL (defensive — never breaks chain).
    """
    sys_prompt = _build_classifier_prompt(level, lang)
    errors_summary = json.dumps(
        [
            {
                "family": e.get("family"),
                "tier": e.get("tier"),
                "code": e.get("code"),
            }
            for e in (errors_detected or [])
        ]
    )
    user_prompt = (
        f'Learner text : "{learner_text}"\n'
        f"Errors detected (Maestro tagged) : {errors_summary}\n"
        f"Turn count : {turn_count}\n\n"
        f"What CF move should the tutor produce ? Output strict JSON."
    )

    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            resp = await client.post(
                LITELLM_URL,
                json={
                    "model": CLASSIFIER_MODEL,
                    "messages": [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.0,
                    "max_tokens": 250,
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)

            cf_move = parsed.get("cf_move")
            if cf_move not in CF_MOVES_BIPED:
                raise ValueError(f"invalid cf_move enum: {cf_move!r}")

            confidence = float(parsed.get("confidence", 0.5))
            if confidence < CONFIDENCE_THRESHOLD:
                _log.info(
                    f"classifier confidence below threshold ({confidence:.2f} < "
                    f"{CONFIDENCE_THRESHOLD}), falling back to rule"
                )
                return _rule_based_fallback(errors_detected, level, reason="low_confidence")

            return {
                "cf_move": cf_move,
                "target_concept": parsed.get("target_concept", "none"),
                "confidence": confidence,
                "reasoning": parsed.get("reasoning", ""),
                "source": "llm",
            }
    except (
        httpx.HTTPError,
        httpx.TimeoutException,
        json.JSONDecodeError,
        ValueError,
        KeyError,
    ) as e:
        _log.warning(
            f"classifier failed ({type(e).__name__}: {e}), falling back to rule"
        )
        return _rule_based_fallback(errors_detected, level, reason=type(e).__name__)


# ── Rule-based fallback ─────────────────────────────────────────────────


def _rule_based_fallback(
    errors_detected: list[dict[str, Any]] | None,
    level: str,
    reason: str = "unspecified",
) -> dict[str, Any]:
    """Fallback to TIER_TO_FEEDBACK_BY_LEVEL deterministic mapping.

    Never breaks the chain — always returns a valid dict. Imports inline
    to avoid circular dependency with teacher_prompt.
    """
    from academie_core.pedagogy.teacher_prompt import TIER_TO_FEEDBACK_BY_LEVEL

    tier = _highest_tier_in_errors(errors_detected) or "T0"
    cf_move = TIER_TO_FEEDBACK_BY_LEVEL.get(level, {}).get(tier, "silent")

    return {
        "cf_move": cf_move,
        "target_concept": _first_error_family(errors_detected) or "none",
        "confidence": 0.5,
        "reasoning": f"rule-based fallback (level={level}, tier={tier}, reason={reason})",
        "source": "rule",
    }


def _highest_tier_in_errors(errors: list[dict[str, Any]] | None) -> str | None:
    """Return T4 > T3 > T2 > T1 > T0 (highest tier first match)."""
    if not errors:
        return None
    tiers = {e.get("tier", "T0") for e in errors}
    for priority in ("T4", "T3", "T2", "T1", "T0"):
        if priority in tiers:
            return priority
    return None


def _first_error_family(errors: list[dict[str, Any]] | None) -> str | None:
    if not errors:
        return None
    return errors[0].get("family")


# ── Sync wrapper for non-async callers ──────────────────────────────────


def classify_cf_sync(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Sync wrapper for classify_cf — useful for tests or non-async callers.

    Beware : will block the event loop if called from async context.
    """
    import asyncio

    return asyncio.run(classify_cf(*args, **kwargs))
