"""German deterministic rule layer — surface error detection.

SKELETON — Phase 0.3. Heavily limited without syntax-aware tooling (spaCy-de
wired in Wave 2). Focus on surface-level patterns detectable via regex.

Rules implemented:
- DE:UMLAUT — missing umlauts on common words (mussen → müssen, uber → über)
- DE:FALSE_FRIEND — classic FR→DE false friends (Gymnasium, Chef, Pension)
- DE:COMPOUND_SPACE — incorrect spacing of common compounds (Haus Aufgabe → Hausaufgabe)

NOT covered (LLM layer / Wave 2 spaCy-de):
- DE:CASE — Nom/Akk/Dat/Gen agreement (needs morphological analysis)
- DE:V2 — verb-second position (needs syntax)
- DE:GENDER — article-noun gender agreement (needs lexicon lookup)
- Separable verbs (anfangen, aufstehen) split at sentence boundaries
- Subordinate clause verb-final rule

Shared contract with rules.py : returns `list[RuleDetection]`.
"""
from __future__ import annotations

import re

from .rules import RuleDetection


# ── DE:UMLAUT — missing umlauts on common words ──
# FR keyboards lack ä/ö/ü so learners often type plain a/o/u.
# High-precision list of words that ONLY exist with umlaut.

_UMLAUT_FIXES: dict[str, tuple[str, str]] = {
    # word_without_umlaut: (correct_spelling, reason)
    "mussen": ("müssen", "Umlaut obligatoire: müssen (devoir)"),
    "musste": ("müsste", "Umlaut obligatoire: müsste"),
    "konnen": ("können", "Umlaut obligatoire: können (pouvoir)"),
    "konnte": ("könnte", "Umlaut obligatoire: könnte"),
    "uber": ("über", "Umlaut obligatoire: über (sur/à propos)"),
    "fur": ("für", "Umlaut obligatoire: für (pour)"),
    "wurde": ("würde", "Umlaut obligatoire: würde (conditionnel)"),
    "grusse": ("grüße", "Umlaut obligatoire: grüße"),
    "gruss": ("Gruß", "Umlaut + ß: Gruß"),
    "schon": ("schön", "schön (beau) avec ö — 'schon' (déjà) existe sans umlaut mais contexte différent"),
    "spat": ("spät", "Umlaut obligatoire: spät (tard)"),
    "madchen": ("Mädchen", "Umlaut obligatoire: Mädchen"),
    "hor": ("hör", "Umlaut obligatoire: hör"),
    "ho ren": ("hören", "Umlaut obligatoire: hören"),
    "hören": ("hören", ""),  # kept for roundtrip; filtered below
}


def _detect_missing_umlaut(text: str) -> list[RuleDetection]:
    results: list[RuleDetection] = []
    for wrong, (fix, reason) in _UMLAUT_FIXES.items():
        if wrong == fix or not reason:
            continue  # skip self-matches
        pattern = re.compile(rf"\b{re.escape(wrong)}\b", re.IGNORECASE)
        for _m in pattern.finditer(text):
            results.append(RuleDetection(
                "DE:UMLAUT",
                wrong,
                fix,
                reason,
            ))
            break  # one detection per form is enough
    return results


# ── DE:FALSE_FRIEND — classic FR→DE false friends ──

_FALSE_FRIENDS_DE: dict[str, tuple[str, str]] = {
    "gymnasium": ("Gymnasium = lycée (école) ; 'gymnase' = Sporthalle",
                  "Gymnasium est un lycée, pas une salle de sport."),
    "chef": ("Chef = patron/boss ; 'chef cuisinier' = Koch",
             "Chef = patron. 'Chef' culinaire = Koch."),
    "pension": ("Pension = retraite OU pensions de famille ; vérifier contexte",
                "Pension allemand ≠ 'pension' FR dans tous les cas."),
    "regal": ("Regal = étagère ; 'régal' (délice) = Genuss",
              "Regal = étagère. 'Régal' = Genuss/Delikatesse."),
    "rente": ("Rente = retraite (versement) ; 'rente' placement = Anleihe",
              "Rente = retraite ; 'rente' placement = Anleihe."),
    "kaution": ("Kaution = caution bancaire ; 'caution morale' = Bürgschaft",
                "Kaution = dépôt de garantie financier."),
}


def _detect_false_friends_de(text: str) -> list[RuleDetection]:
    results: list[RuleDetection] = []
    for word, (fix, reason) in _FALSE_FRIENDS_DE.items():
        if re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE):
            results.append(RuleDetection("DE:FALSE_FRIEND", word, fix, reason))
    return results


# ── DE:COMPOUND_SPACE — commonly split compounds ──
# German compounds are written solid. FR learners split them.

_COMPOUNDS: dict[str, str] = {
    "haus aufgabe": "Hausaufgabe",
    "haus aufgaben": "Hausaufgaben",
    "haupt bahnhof": "Hauptbahnhof",
    "kinder garten": "Kindergarten",
    "flug hafen": "Flughafen",
    "geburts tag": "Geburtstag",
    "wochen ende": "Wochenende",
    "fahr rad": "Fahrrad",
}


def _detect_split_compounds(text: str) -> list[RuleDetection]:
    results: list[RuleDetection] = []
    for wrong, fix in _COMPOUNDS.items():
        pattern = re.compile(rf"\b{re.escape(wrong)}\b", re.IGNORECASE)
        for _m in pattern.finditer(text):
            results.append(RuleDetection(
                "DE:COMPOUND_SPACE",
                wrong,
                fix,
                f"Komposita in deutsch zusammen geschrieben: '{wrong}' → '{fix}'.",
            ))
            break
    return results


def detect_errors_de(text: str) -> list[RuleDetection]:
    """Main entry — aggregates all DE rule-based detectors."""
    if not text or not text.strip():
        return []
    results: list[RuleDetection] = []
    results.extend(_detect_missing_umlaut(text))
    results.extend(_detect_false_friends_de(text))
    results.extend(_detect_split_compounds(text))
    return results
