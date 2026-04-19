"""Japanese deterministic rule layer — skeleton.

SKELETON — Phase 0.3. Severely limited without morphological analysis
(fugashi/unidic wired in Wave 3). Most JP errors require tokenization.

Error-type priority based on empirical distribution for JP beginners
(Oyama, Polyglossia vol. 18): particles 33%, kana-writing 20%,
special-phoneme/long-vowel 13%, sentence-structure 11%, verb-conjugation 8%,
adjective/affix 3%.

Rules implemented:
- JP:SCRIPT_MIX — Latin/half-width characters mixed inside Japanese words
- JP:DOUBLE_PARTICLE — classic duplicated particles (をを, にに, はは)
- JP:FR_ARTICLE_LEAK — FR article leaking before Japanese word (le neko, la sakura)

NOT covered (requires tokenizer — Wave 3):
- JP:PARTICLE — は/が/を/に confusion (the 33% bucket)
- JP:COUNTER — wrong counter for object class (一つ vs 一人 vs 一本)
- JP:CONJ — verb conjugation errors (食べます → 食べました)
- JP:KEIGO — polite/humble/respectful registers (best-effort even with tokenizer)

Shared contract with rules.py : returns `list[RuleDetection]`.
"""
from __future__ import annotations

import re

from .rules import RuleDetection


# ── JP:SCRIPT_MIX — Latin letter inside a kanji/kana run ──
# Common keyboard slip: typing "konnichi ha" instead of full Japanese input.
# Detect Latin letter(s) surrounded by CJK characters.

_CJK_LATIN_MIX_RE = re.compile(
    r"[\u3040-\u30ff\u4e00-\u9fff]+[a-zA-Z]+|[a-zA-Z]+[\u3040-\u30ff\u4e00-\u9fff]+"
)


def _detect_script_mix(text: str) -> list[RuleDetection]:
    results: list[RuleDetection] = []
    for m in _CJK_LATIN_MIX_RE.finditer(text):
        snippet = m.group(0)
        # Skip common legitimate romaji brand names and proper nouns by length heuristic
        if len(snippet) > 20:
            continue
        results.append(RuleDetection(
            "JP:SCRIPT_MIX",
            snippet,
            snippet,
            "Mélange caractères latins et japonais — utiliser l'IME pour saisir "
            "en hiragana/katakana/kanji complet.",
        ))
    return results


# ── JP:DOUBLE_PARTICLE — duplicated particles ──
# Learners sometimes double-type a particle when hesitating.

_DOUBLED_PARTICLES = ["をを", "にに", "はは", "がが", "での", "へへ"]
# Note: はは and がが CAN be legitimate (mother 母 is read 'haha', がが used for contrast).
# We only flag pure hiragana doublings in a short word context.


def _detect_double_particle(text: str) -> list[RuleDetection]:
    results: list[RuleDetection] = []
    for doubled in ["をを", "にに", "がが", "へへ"]:
        for m in re.finditer(doubled, text):
            results.append(RuleDetection(
                "JP:DOUBLE_PARTICLE",
                doubled,
                doubled[0],
                f"Particule doublée involontairement : '{doubled}' → '{doubled[0]}'.",
            ))
    return results


# ── JP:FR_ARTICLE_LEAK — French article leaking before Japanese noun ──
# Beginners' typo: "le neko", "la sakura", "un kimono" — article leak from L1.

_FR_ARTICLES = ("le", "la", "les", "un", "une", "des", "du", "de la")


def _detect_fr_article_leak(text: str) -> list[RuleDetection]:
    results: list[RuleDetection] = []
    # Pattern: FR article + space + Latin-romaji word that's likely a JP noun
    # This is fuzzy; keep it high-precision by requiring the article + known JP romaji
    _JP_ROMAJI_HINTS = r"(neko|inu|sakura|kimono|sensei|gakkou|hon|mizu|tabemono|ie)"
    for art in _FR_ARTICLES:
        pattern = re.compile(rf"\b{art}\s+{_JP_ROMAJI_HINTS}\b", re.IGNORECASE)
        for m in pattern.finditer(text):
            snippet = m.group(0)
            noun = m.group(1)
            results.append(RuleDetection(
                "JP:FR_ARTICLE_LEAK",
                snippet,
                noun,
                f"Pas d'article en japonais : '{snippet}' → simplement '{noun}'.",
            ))
    return results


def detect_errors_jp(text: str) -> list[RuleDetection]:
    """Main entry — aggregates all JP rule-based detectors.

    Very limited without tokenizer (Wave 3). The LLM layer carries the bulk
    of error analysis at the moment.
    """
    if not text or not text.strip():
        return []
    results: list[RuleDetection] = []
    results.extend(_detect_script_mix(text))
    results.extend(_detect_double_particle(text))
    results.extend(_detect_fr_article_leak(text))
    return results
