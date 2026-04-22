"""Session 40 Phase B1 — Deterministic dim scoring (regex + policy lookup).

Scores dims where pattern matching or policy lookup gives a reliable answer
without an LLM :
  - recast_saliency_and_dosage : line count, `?` count, mini-lesson marker
  - partial signal for cf_move_set_valid : detect clear
    metalinguistic/explicit_correction patterns (LLM fills the ambiguous gap)
  - scaffolding_flags_honored (partial) : L2 word ratio via ASCII heuristic

Dims fully covered by LLM judge : register_cefr_alignment, semantic_fidelity_pairwise.
"""
from __future__ import annotations

import re

from ..schemas import DimVerdict, ScenarioSchema

# Patterns that indicate a metalinguistic CF move (explain the rule).
METALINGUISTIC_PATTERNS = [
    r"past (?:simple|tense|participle)",
    r"auxiliary (?:verb|do|be)",
    r"subject[-\s]?verb agreement",
    r"the rule (?:is|here is)",
    r"conjugat(?:ion|ed|e)",
    r"\bmarker\b",
    r"present perfect",
]

# Explicit correction patterns
EXPLICIT_CORRECTION_PATTERNS = [
    r"the correct (?:form|word|way) is",
    r"you should (?:say|write|use)",
    r"this is wrong",
    r"correct[:\s]+[\"'`]",
]

MICRO_LESSON_MARKER = "=== MICRO-LEÇON CIBLÉE"


def _count_lines(response: str) -> int:
    return len([l for l in response.split("\n") if l.strip()])


def _count_questions(response: str) -> int:
    # Count `?` only outside markdown code/JSON envelopes
    clean = re.sub(r"<output>.*?</output>", "", response, flags=re.DOTALL)
    return clean.count("?")


def _l2_word_ratio(response: str, l2_code: str = "en") -> float:
    """Quick ASCII-only heuristic : fraction of words that look like L2.
    For EN target, words matching [a-zA-Z]+ with len >= 2 are assumed L2.
    French-origin tokens are detected via common FR patterns.
    """
    # Strip JSON envelope
    text = re.sub(r"<output>.*?</output>", "", response or "", flags=re.DOTALL).lower()
    words = re.findall(r"[a-zéàèêëïîôûùüçñ]+", text)
    if not words:
        return 1.0
    fr_stopwords = {
        "le", "la", "les", "un", "une", "des", "du", "de",
        "et", "ou", "mais", "avec", "pour", "dans", "sur",
        "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
        "qu", "d", "l", "j", "n", "m", "t", "c",  # apostrophe-stripped particles
        "parce", "quand", "aussi", "très", "bien", "plus",
        "non", "oui", "est", "as", "ai", "ont", "a",
    }
    accent_re = re.compile(r"[éèêëàâîïôûùüç]")
    fr_hits = sum(
        1 for w in words if w in fr_stopwords or accent_re.search(w)
    )
    l2_hits = len(words) - fr_hits
    return l2_hits / len(words)


def _score_recast_saliency(scenario: ScenarioSchema, response: str) -> DimVerdict:
    spec = (scenario.expected_dimensions or {}).get("recast_saliency_and_dosage") or {}
    max_lines = spec.get("max_lines", 5)
    max_questions = spec.get("max_questions", 2)
    mini_lesson_allowed = spec.get("mini_lesson_allowed", False)

    lines = _count_lines(response)
    questions = _count_questions(response)
    has_marker = MICRO_LESSON_MARKER in response
    extra_budget = 3 if has_marker and mini_lesson_allowed else 0

    problems = []
    if lines > max_lines + extra_budget:
        problems.append(f"lines={lines} > max={max_lines + extra_budget}")
    if questions > max_questions:
        problems.append(f"questions={questions} > max={max_questions}")
    if has_marker and not mini_lesson_allowed:
        problems.append("micro-lesson marker present but not allowed for this scenario")

    if problems:
        return DimVerdict(dim="recast_saliency_and_dosage", verdict="fail",
                          reasoning="; ".join(problems))
    return DimVerdict(dim="recast_saliency_and_dosage", verdict="pass",
                      reasoning=f"lines={lines}, ?={questions}, marker={has_marker}")


def _score_cf_move_partial(scenario: ScenarioSchema, response: str) -> DimVerdict:
    """Detect only CLEAR metalinguistic/explicit_correction patterns.
    Ambiguous cases fall through to unknown (LLM judge takes over)."""
    spec = (scenario.expected_dimensions or {}).get("cf_move_set_valid") or {}
    forbidden = set(spec.get("forbidden", []))
    if not forbidden:
        return DimVerdict(dim="cf_move_set_valid_partial", verdict="unknown",
                          reasoning="no forbidden set defined")

    low = (response or "").lower()
    detected = set()
    for p in METALINGUISTIC_PATTERNS:
        if re.search(p, low):
            detected.add("metalinguistic")
            break
    for p in EXPLICIT_CORRECTION_PATTERNS:
        if re.search(p, low):
            detected.add("explicit_correction")
            break

    violations = detected & forbidden
    if violations:
        return DimVerdict(dim="cf_move_set_valid_partial", verdict="fail",
                          reasoning=f"forbidden CF move detected: {sorted(violations)}")
    # Nothing clearly violates → defer to LLM (unknown = pass-through)
    return DimVerdict(dim="cf_move_set_valid_partial", verdict="unknown",
                      reasoning="no clear violation in regex pass")


def _score_scaffolding_l2_ratio(scenario: ScenarioSchema, response: str) -> DimVerdict:
    spec = (scenario.expected_dimensions or {}).get("scaffolding_flags_honored") or {}
    band = spec.get("l2_ratio_band")
    if not band or len(band) != 2:
        return DimVerdict(dim="scaffolding_flags_l2_ratio", verdict="unknown",
                          reasoning="no l2_ratio_band defined")
    lo, hi = band
    ratio = _l2_word_ratio(response)
    if lo <= ratio <= hi:
        return DimVerdict(dim="scaffolding_flags_l2_ratio", verdict="pass",
                          reasoning=f"L2_ratio={ratio:.2f} in [{lo},{hi}]",
                          score=ratio)
    return DimVerdict(dim="scaffolding_flags_l2_ratio", verdict="fail",
                      reasoning=f"L2_ratio={ratio:.2f} outside [{lo},{hi}]",
                      score=ratio)


def score_all(scenario: ScenarioSchema, response: str) -> list[DimVerdict]:
    """All deterministic dims we can score in this response."""
    if not response:
        return []
    return [
        _score_recast_saliency(scenario, response),
        _score_cf_move_partial(scenario, response),
        _score_scaffolding_l2_ratio(scenario, response),
    ]
