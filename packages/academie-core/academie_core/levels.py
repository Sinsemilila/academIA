"""Niveaux natifs ↔ CEFR — mapping abstraction par domaine.

Storage interne : CEFR a1-c2 (unifié cross-lang).
Affichage/prompts : système natif par domaine (CEFR pour EN/ES/IT/DE,
JLPT N5-N1 pour JP, TORFL TEU-IV pour RU).

Sources :
- JLPT↔CEFR score bridge officiel (Japan Foundation, déc. 2025) :
  https://www.jlpt.jp/e/about/cefr_reference.html
- TORFL levels : Gosstandart ТРКИ (Russian Ministry of Education).
"""
from __future__ import annotations

# ── CEFR canonical set ─────────────────────────────────────────────

CEFR_LEVELS = ("a1", "a2", "b1", "b2", "c1", "c2")

# ── JLPT ── simple level-to-CEFR modal mapping (for display) ────────
#
# "A learner who just passes level X" maps to this CEFR level.
# Used for `display_level()` / `cefr_to_native()` round-trips.

JLPT_TO_CEFR: dict[str, str] = {
    "N5": "a1",
    "N4": "a2",
    "N3": "b1",
    "N2": "b2",
    "N1": "c1",
    "beyond_N1": "c2",
}

CEFR_TO_JLPT: dict[str, str] = {
    "a1": "N5",
    "a2": "N4",
    "b1": "N3",
    "b2": "N2",
    "c1": "N1",
    "c2": "beyond_N1",
}

# ── JLPT ── score-based precise bridge (Japan Foundation déc 2025) ─
#
# When a learner's raw score is known, use `jlpt_score_to_cefr()` for a more
# precise translation. Thresholds are cumulative: "first threshold ≥ score".

_JLPT_SCORE_THRESHOLDS: dict[str, list[tuple[int, str]]] = {
    "N5": [(80, "a1")],
    "N4": [(90, "a2")],
    "N3": [(95, "a2"), (104, "b1")],
    "N2": [(90, "b1"), (112, "b2")],
    "N1": [(100, "b2"), (142, "c1")],
}

# ── TORFL (ТРКИ) ── level mapping (Gosstandart RU) ─────────────────

TORFL_TO_CEFR: dict[str, str] = {
    "TEU": "a1",
    "TBU": "a2",
    "TORFL-I": "b1",
    "TORFL-II": "b2",
    "TORFL-III": "c1",
    "TORFL-IV": "c2",
}

CEFR_TO_TORFL: dict[str, str] = {v: k for k, v in TORFL_TO_CEFR.items()}

# ── Domain → level system dispatch ─────────────────────────────────
#
# Keys must match agent names used in chat_router._DOMAIN_REGISTRY.

LEVEL_SYSTEM_BY_DOMAIN: dict[str, str] = {
    "teacher": "cefr",
    "maestro": "cefr",
    "professore": "cefr",
    "lehrer": "cefr",
    "sensei": "jlpt",
    "uchitel": "torfl",
}


# ── Public API ─────────────────────────────────────────────────────

def display_level(cefr_level: str, domain: str) -> str:
    """Return the user-facing level label for a given internal CEFR level.

    Japanese (sensei) sees N5-N1, Russian (uchitel) sees TEU/TBU/TORFL-I-IV,
    all others see A1-C2.
    """
    level = cefr_level.lower()
    if level not in CEFR_LEVELS:
        raise ValueError(f"unknown CEFR level: {cefr_level!r}")

    system = LEVEL_SYSTEM_BY_DOMAIN.get(domain, "cefr")
    if system == "jlpt":
        return CEFR_TO_JLPT[level]
    if system == "torfl":
        return CEFR_TO_TORFL[level]
    return level.upper()


def parse_user_level(raw: str, domain: str) -> str:
    """Parse a user-provided level label into internal CEFR a1-c2.

    Accepts native notation (N4, TORFL-II) or CEFR (B1, b1).
    """
    if not raw:
        raise ValueError("empty level string")

    normalized = raw.strip()
    lowered = normalized.lower()

    if lowered in CEFR_LEVELS:
        return lowered

    system = LEVEL_SYSTEM_BY_DOMAIN.get(domain, "cefr")
    if system == "jlpt" and normalized in JLPT_TO_CEFR:
        return JLPT_TO_CEFR[normalized]
    if system == "torfl" and normalized in TORFL_TO_CEFR:
        return TORFL_TO_CEFR[normalized]

    # Cross-system fallback: try all mappings before failing.
    if normalized in JLPT_TO_CEFR:
        return JLPT_TO_CEFR[normalized]
    if normalized in TORFL_TO_CEFR:
        return TORFL_TO_CEFR[normalized]

    raise ValueError(f"cannot parse level {raw!r} for domain {domain!r}")


def cefr_to_native(cefr_level: str, domain: str) -> str:
    """Alias for display_level() — more semantic when the intent is conversion."""
    return display_level(cefr_level, domain)


def jlpt_score_to_cefr(jlpt_level: str, score: int) -> str:
    """Translate a JLPT raw score into CEFR using the official bridge.

    Use this when a learner's precise score is known (e.g. from JLPT certificate),
    for finer-grained placement than the modal `JLPT_TO_CEFR` mapping.
    """
    thresholds = _JLPT_SCORE_THRESHOLDS.get(jlpt_level)
    if thresholds is None:
        raise ValueError(f"unknown JLPT level: {jlpt_level!r}")

    result = None
    for threshold, cefr in thresholds:
        if score >= threshold:
            result = cefr
    if result is None:
        raise ValueError(
            f"score {score} below minimum pass threshold for {jlpt_level}"
        )
    return result
