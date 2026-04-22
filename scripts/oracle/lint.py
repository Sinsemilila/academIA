"""Session 40 Phase A — Oracle lint layer.

Fast deterministic checks on a bot response. Cheap (~0 LLM calls), used
as `block 8` of RUN_RECENT_BATTERY.sh for structural regression catch.

4 checks :
  - json_wrapper : <output>{...}</output> present and parses
  - observed_level : CEFR field non-empty (from turn 3+)
  - a1_no_jargon : no metalinguistic terms at CEFR A1
  - no_priority_leak : bot doesn't literally announce priority_concepts

Adding a new check = one function returning LintResult + register in
`LINT_CHECKS`. Regex blocklists are class-level constants for easy
audit.
"""
from __future__ import annotations

import json
import re

from .schemas import LintResult, ScenarioSchema

OUTPUT_RE = re.compile(r"<output>\s*(\{.*?\})\s*</output>", re.DOTALL)

A1_BANNED_TERMS = [
    # English metalinguistic
    "past simple", "past participle", "auxiliary", "modal verb",
    "present perfect", "gerund", "subjunctive",
    # Spanish equivalents (in case teacher responds on cross-lang scenario)
    "propiedades inherentes", "clasificatorias", "pretérito",
]

PRIORITY_LEAK_PATTERNS = [
    r"today we(?:'ll| will) focus on",
    r"priority concepts?\s*:",
    r"let's work on\s+\w+.*?(,\s*\w+){1,}",  # "let's work on X, Y, Z"
    r"focus (?:today|for now) on\s+\w+.*?(,\s*\w+){1,}",
    # French variants
    r"aujourd'?hui on (?:va )?se concentrer sur",
    r"concepts? prioritaires?\s*:",
]


def check_json_wrapper(response: str, required: bool = False) -> LintResult:
    """Opt-in via scenario.expected_dimensions.output_wrapper.required=true.
    Most V1 scenarios use fresh conversation_id → Dify responds in plain
    text (onboarding/welcome flow) and doesn't wrap. Only deep-session
    scenarios should require the wrapper."""
    if not required:
        return LintResult(check="json_wrapper", passed=True,
                          detail="skipped (not required by scenario)")
    match = OUTPUT_RE.search(response or "")
    if not match:
        return LintResult(check="json_wrapper", passed=False,
                          detail="<output>{JSON}</output> not found")
    try:
        json.loads(match.group(1))
    except json.JSONDecodeError as e:
        return LintResult(check="json_wrapper", passed=False,
                          detail=f"JSON parse error: {e}")
    return LintResult(check="json_wrapper", passed=True)


def check_observed_level_emitted(response: str, turn_number: int, required: bool = False) -> LintResult:
    """observed_level required only when the wrapper is expected AND turn_number >= 3."""
    if not required or turn_number < 3:
        return LintResult(check="observed_level", passed=True,
                          detail=f"skipped (required={required}, turn={turn_number})")
    match = OUTPUT_RE.search(response or "")
    if not match:
        return LintResult(check="observed_level", passed=False,
                          detail="no JSON wrapper to inspect")
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return LintResult(check="observed_level", passed=False,
                          detail="JSON invalid")
    lvl = (data.get("observed_level") or "").strip()
    if not lvl:
        return LintResult(check="observed_level", passed=False,
                          detail="observed_level empty")
    if not re.match(r"^[A-C][12]\+?$", lvl):
        return LintResult(check="observed_level", passed=False,
                          detail=f"observed_level malformed: {lvl!r}")
    return LintResult(check="observed_level", passed=True, detail=f"level={lvl}")


def check_a1_no_jargon(response: str, cefr: str) -> LintResult:
    """At CEFR A1, metalinguistic terms are banned (Lyster-compliant rubric).
    Other CEFR levels skip this check."""
    if cefr.upper() != "A1":
        return LintResult(check="a1_no_jargon", passed=True,
                          detail=f"skipped (CEFR={cefr})")
    low = (response or "").lower()
    hits = [t for t in A1_BANNED_TERMS if t in low]
    if hits:
        return LintResult(check="a1_no_jargon", passed=False,
                          detail=f"banned term(s): {hits}")
    return LintResult(check="a1_no_jargon", passed=True)


def check_no_priority_leak(response: str) -> LintResult:
    """Bot must not literally announce priority_concepts list."""
    low = (response or "").lower()
    for pat in PRIORITY_LEAK_PATTERNS:
        m = re.search(pat, low)
        if m:
            return LintResult(check="no_priority_leak", passed=False,
                              detail=f"matched pattern {pat!r} at {m.start()}")
    return LintResult(check="no_priority_leak", passed=True)


def run_lint(scenario: ScenarioSchema, response: str) -> list[LintResult]:
    """Run all lint checks on a bot response for a given scenario.
    Returns list of LintResult, caller aggregates pass/fail.

    Required-wrapper opt-in : scenario.expected_dimensions.output_wrapper.required
    defaults to False (plain-text Dify response accepted). Scenarios that
    simulate a deep-session bot (QCM'd user, turn >=3) can set it true.
    """
    turn_number = scenario.turns[0].turn_number if scenario.turns else 1
    cefr = scenario.scenario_key.cefr
    wrapper_spec = (scenario.expected_dimensions or {}).get("output_wrapper") or {}
    wrapper_required = bool(wrapper_spec.get("required", False))
    return [
        check_json_wrapper(response, required=wrapper_required),
        check_observed_level_emitted(response, turn_number, required=wrapper_required),
        check_a1_no_jargon(response, cefr),
        check_no_priority_leak(response),
    ]
