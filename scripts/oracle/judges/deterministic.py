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

# Cross-lang CF move regex banks. Session 55 fix : ES smoke 6/6 fail
# scaffolding_l2_ratio was an EN-only judge artefact, not Maestro pedagogy issue.
# `agent` field in ScenarioKey follows pattern `<role>_<lang>` (teacher_en,
# maestro_es, ...) — extract lang via `scenario.key.agent.split("_")[-1]`.

# Metalinguistic = "explain the grammar rule" CF move.
METALINGUISTIC_PATTERNS_BY_LANG: dict[str, list[str]] = {
    "en": [
        r"past (?:simple|tense|participle)",
        r"auxiliary (?:verb|do|be)",
        r"subject[-\s]?verb agreement",
        r"the rule (?:is|here is)",
        r"conjugat(?:ion|ed|e)",
        r"\bmarker\b",
        r"present perfect",
    ],
    "es": [
        r"presente (?:de )?(?:indicativo|subjuntivo|simple)",
        r"pret[eé]rito (?:indefinido|perfecto|imperfecto|pluscuamperfecto)",
        r"verbo auxiliar",
        r"concordancia (?:de )?(?:g[eé]nero|n[uú]mero|sujeto)",
        r"la regla (?:es|aqu[ií] es)",
        r"conjuga(?:ci[oó]n|do|r|mos)",
        r"modo (?:subjuntivo|indicativo|imperativo|condicional)",
        r"acentuaci[oó]n",
        r"forma (?:verbal|del verbo)",
    ],
}

# Explicit correction = "you said wrong, the correct form is X" CF move.
EXPLICIT_CORRECTION_PATTERNS_BY_LANG: dict[str, list[str]] = {
    "en": [
        r"the correct (?:form|word|way) is",
        r"you should (?:say|write|use)",
        r"this is wrong",
        r"correct[:\s]+[\"'`]",
    ],
    "es": [
        r"la (?:forma|palabra|manera) correcta es",
        r"deber[ií]as (?:decir|escribir|usar)",
        r"esto (?:est[aá] mal|no es correcto)",
        r"se dice (?:as[ií]|de esta forma)",
        r"correcto[:\s]+[\"'`]",
        r"\bno (?:se dice|se escribe)\b",
    ],
}

# Backward compat aliases (consumed by tests / external callers).
METALINGUISTIC_PATTERNS = METALINGUISTIC_PATTERNS_BY_LANG["en"]
EXPLICIT_CORRECTION_PATTERNS = EXPLICIT_CORRECTION_PATTERNS_BY_LANG["en"]

MICRO_LESSON_MARKER = "=== MICRO-LEÇON CIBLÉE"


def _scenario_lang(scenario: ScenarioSchema) -> str:
    """Extract target lang code from scenario.scenario_key.agent
    (e.g. maestro_es → 'es', teacher_en → 'en')."""
    try:
        return scenario.scenario_key.agent.split("_")[-1].lower()
    except Exception:
        return "en"


def _count_lines(response: str) -> int:
    return len([l for l in response.split("\n") if l.strip()])


def _count_questions(response: str) -> int:
    # Count `?` only outside markdown code/JSON envelopes
    clean = re.sub(r"<output>.*?</output>", "", response, flags=re.DOTALL)
    return clean.count("?")


# Per-target-language sets of FR-leaking stopwords (words that are common in
# FR L1 but NOT typical in target L2). Keeping the EN list as historical
# baseline ; ES/IT/DE drop overlapping stopwords ("la"/"de"/"a"/"un"/"est"...
# all exist in Romance languages too — using them as FR markers triggers
# false positives that wreck L2_ratio scoring for ES/IT learners).
_FR_LEAK_STOPWORDS_BY_TARGET: dict[str, set[str]] = {
    "en": {
        "le", "la", "les", "un", "une", "des", "du", "de",
        "et", "ou", "mais", "avec", "pour", "dans", "sur",
        "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
        "qu", "d", "l", "j", "n", "m", "t", "c",
        "parce", "quand", "aussi", "très", "bien", "plus",
        "non", "oui", "est", "as", "ai", "ont", "a",
    },
    "es": {
        # ES overlap-removed : "la","le","les","de","a","un","una","est","as","ai","ont","bien","plus","non","tu","qu" all conflict.
        "et", "ou", "mais", "avec", "pour", "dans", "sur",
        "je", "il", "elle", "nous", "vous", "ils", "elles",
        "parce", "quand", "aussi", "très", "oui",
        "j", "n", "m", "c",  # apostrophe particles still safe markers
    },
    "it": {
        "et", "ou", "mais", "avec", "pour", "dans", "sur",
        "je", "il", "elle", "nous", "vous", "ils", "elles",
        "parce", "quand", "aussi", "très", "oui", "qu",
        "j", "n", "m", "t", "c",
    },
    "de": {
        "le", "la", "les", "un", "une", "des", "du", "de",
        "et", "ou", "mais", "avec", "pour", "dans", "sur",
        "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
        "qu", "parce", "quand", "aussi", "très", "bien", "plus", "non", "oui",
    },
}

# Per-target accent set : chars considered FR-leaking for THIS L2.
# - EN target : EN has no diacritics → all FR accents are FR markers.
# - ES target : ES uses á é í ó ú ü ñ — only FR-only accents (ç + circumflex
#   + diaeresis on i/u) are unambiguous FR leak signals.
# - IT target : IT uses à è é ì ò ù — same restrictive set as ES.
# - DE target : DE uses ä ö ü ß — FR accents are FR.
_FR_ACCENT_RE_BY_TARGET: dict[str, "re.Pattern[str]"] = {
    "en": re.compile(r"[éèêëàâîïôûùüç]"),
    "es": re.compile(r"[çêëîïôûù]"),
    "it": re.compile(r"[çêëîïôûù]"),
    "de": re.compile(r"[éèêëàâîïôûùç]"),
}


def _l2_word_ratio(response: str, l2_code: str = "en") -> float:
    """Heuristic L2 word ratio : fraction of words NOT looking like FR L1 leak.

    Cross-lang fix S55 : EN-only logic was misclassifying ES/IT accentuated
    tokens (está, después, también, también, niños...) as FR. Now :
    - Stopword set is target-lang specific (ES/IT drop overlaps with FR).
    - Accent check is FR-ONLY (circumflex + diaeresis-on-i/u + ç) — ES acutes
      and ñ are NOT counted as FR.
    """
    text = re.sub(r"<output>.*?</output>", "", response or "", flags=re.DOTALL).lower()
    # Unicode-friendly word regex (latin set covering FR/ES/IT/DE diacritics).
    words = re.findall(r"[a-záàâäéèêëíìîïóòôöúùûüçñß]+", text)
    if not words:
        return 1.0
    fr_stopwords = _FR_LEAK_STOPWORDS_BY_TARGET.get(
        l2_code, _FR_LEAK_STOPWORDS_BY_TARGET["en"]
    )
    accent_re = _FR_ACCENT_RE_BY_TARGET.get(
        l2_code, _FR_ACCENT_RE_BY_TARGET["en"]
    )
    fr_hits = 0
    for w in words:
        if w in fr_stopwords:
            fr_hits += 1
            continue
        if accent_re.search(w):
            fr_hits += 1
    return (len(words) - fr_hits) / len(words)


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
    Ambiguous cases fall through to unknown (LLM judge takes over).

    Cross-lang S55 : pattern banks switched per scenario target lang.
    """
    spec = (scenario.expected_dimensions or {}).get("cf_move_set_valid") or {}
    forbidden = set(spec.get("forbidden", []))
    if not forbidden:
        return DimVerdict(dim="cf_move_set_valid_partial", verdict="unknown",
                          reasoning="no forbidden set defined")

    lang = _scenario_lang(scenario)
    meta_patterns = METALINGUISTIC_PATTERNS_BY_LANG.get(lang, METALINGUISTIC_PATTERNS_BY_LANG["en"])
    expl_patterns = EXPLICIT_CORRECTION_PATTERNS_BY_LANG.get(lang, EXPLICIT_CORRECTION_PATTERNS_BY_LANG["en"])

    low = (response or "").lower()
    detected = set()
    for p in meta_patterns:
        if re.search(p, low):
            detected.add("metalinguistic")
            break
    for p in expl_patterns:
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
    ratio = _l2_word_ratio(response, l2_code=_scenario_lang(scenario))
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
