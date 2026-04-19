"""Russian deterministic rule layer — skeleton.

SKELETON — Phase 0.3. Most RU error detection requires pymorphy2 morphological
analysis (wired in Wave 4). Surface regex catches a few obvious patterns.

Rules implemented:
- RU:SCRIPT_MIX — Latin letter inside a Cyrillic word (keyboard slip)
- RU:FR_ARTICLE_LEAK — FR article leaking before Russian romanized noun
- RU:HARD_SOFT_SIGN — common ь/ъ confusion in frequent words

NOT covered (requires pymorphy2 / Wave 4):
- RU:CASE — 6-case declension (nominative/accusative/genitive/dative/instrumental/prepositional)
- RU:ASPECT — perfective/imperfective verb pairs
- RU:GENDER — masculine/feminine/neuter agreement
- RU:MOTION — идти/ходить/ехать directional verbs
- RU:WORD_ORDER — relatively free but with pragmatic constraints

Shared contract with rules.py : returns `list[RuleDetection]`.
"""
from __future__ import annotations

import re

from .rules import RuleDetection


# ── RU:SCRIPT_MIX — Latin letter inside Cyrillic ──
# Common on FR keyboards: typing "Mосква" (Latin M + Cyrillic) instead of "Москва".

_CYR_LATIN_MIX_RE = re.compile(
    r"[\u0400-\u04ff]+[a-zA-Z]+|[a-zA-Z]+[\u0400-\u04ff]+"
)


def _detect_script_mix(text: str) -> list[RuleDetection]:
    results: list[RuleDetection] = []
    for m in _CYR_LATIN_MIX_RE.finditer(text):
        snippet = m.group(0)
        if len(snippet) > 25:
            continue
        results.append(RuleDetection(
            "RU:SCRIPT_MIX",
            snippet,
            snippet,
            "Caractères latins dans un mot russe — vérifier la disposition "
            "clavier cyrillique.",
        ))
    return results


# ── RU:FR_ARTICLE_LEAK — French article leaking before Russian romanized noun ──
# Beginners' typo: "le Moskva", "un Pushkin" — L1 article leak.

_FR_ARTICLES = ("le", "la", "les", "un", "une", "des", "du")


def _detect_fr_article_leak(text: str) -> list[RuleDetection]:
    results: list[RuleDetection] = []
    _RU_ROMAJI_HINTS = (
        r"(dom|kniga|gorod|chelovek|stol|mama|papa|drug|voda|moskva|"
        r"pushkin|tolstoy|sobaka|kot)"
    )
    for art in _FR_ARTICLES:
        pattern = re.compile(rf"\b{art}\s+{_RU_ROMAJI_HINTS}\b", re.IGNORECASE)
        for m in pattern.finditer(text):
            snippet = m.group(0)
            noun = m.group(1)
            results.append(RuleDetection(
                "RU:FR_ARTICLE_LEAK",
                snippet,
                noun,
                f"Pas d'article en russe : '{snippet}' → simplement '{noun}'.",
            ))
    return results


# ── RU:HARD_SOFT_SIGN — common ь/ъ confusion in frequent words ──
# ь (soft sign) softens preceding consonant ; ъ (hard sign) is rare, mostly after prefixes.
# FR learners often omit ь or mix them up.

_SOFT_SIGN_FIXES: dict[str, tuple[str, str]] = {
    # word_wrong: (correct, reason)
    "мат": ("мать", "mère = мать (avec ь)"),
    "ноч": ("ночь", "nuit = ночь (avec ь)"),
    "ден": ("день", "jour = день (avec ь)"),
    "мыс": ("мысль", "pensée = мысль (avec ь)"),
    "соль": ("соль", ""),  # filter
}


def _detect_missing_soft_sign(text: str) -> list[RuleDetection]:
    results: list[RuleDetection] = []
    for wrong, (fix, reason) in _SOFT_SIGN_FIXES.items():
        if wrong == fix or not reason:
            continue
        pattern = re.compile(rf"\b{re.escape(wrong)}\b", re.IGNORECASE)
        for _m in pattern.finditer(text):
            results.append(RuleDetection(
                "RU:HARD_SOFT_SIGN",
                wrong,
                fix,
                reason,
            ))
            break
    return results


def detect_errors_ru(text: str) -> list[RuleDetection]:
    """Main entry — aggregates all RU rule-based detectors.

    Very limited without pymorphy2 (Wave 4). LLM layer handles the bulk.
    """
    if not text or not text.strip():
        return []
    results: list[RuleDetection] = []
    results.extend(_detect_script_mix(text))
    results.extend(_detect_fr_article_leak(text))
    results.extend(_detect_missing_soft_sign(text))
    return results
