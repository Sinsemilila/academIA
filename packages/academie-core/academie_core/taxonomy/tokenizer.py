"""Tokenizer abstraction — language-dispatched tokenization.

Phase 0.6 infra. EN/ES/IT/DE use a whitespace+punctuation fallback sufficient
for regex-based rule detection. JP/RU raise NotImplementedError with an install
hint; heavy lifting (SudachiPy/Fugashi for JP, pymorphy2 for RU) is wired in
their respective Waves.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    """A single surface token with its character offsets in the source text."""
    text: str
    start: int
    end: int


# ── Fallback tokenizer (EN/ES/IT/DE) ───────────────────────────────

# Matches contiguous runs of word characters (including Unicode letters such as
# á, ñ, ü, ß) OR a single non-space punctuation character. Whitespace is skipped.
_TOKEN_RE = re.compile(r"[^\W\d_]+(?:['\u2019-][^\W\d_]+)*|\d+|[^\s\w]", re.UNICODE)


def _whitespace_tokenize(text: str) -> list[Token]:
    return [
        Token(text=m.group(), start=m.start(), end=m.end())
        for m in _TOKEN_RE.finditer(text)
    ]


# ── Public dispatcher ──────────────────────────────────────────────

_SUPPORTED_FALLBACK = frozenset({"en", "es", "it", "de"})


def tokenize(text: str, lang: str = "en") -> list[Token]:
    """Return a list of `Token` for the given text and language.

    EN/ES/IT/DE use the regex fallback, which is sufficient for rule-based
    detection (the heavier spaCy pipeline is wired at rules-layer, not here).
    JP and RU raise NotImplementedError until their respective Waves land.
    """
    lang = lang.lower()
    if lang in _SUPPORTED_FALLBACK:
        return _whitespace_tokenize(text)
    if lang in {"jp", "ja"}:
        raise NotImplementedError(
            "JP tokenization not wired yet — install fugashi+unidic-lite "
            "and extend tokenizer.py when Wave 3 starts."
        )
    if lang == "ru":
        raise NotImplementedError(
            "RU tokenization not wired yet — install pymorphy2 "
            "and extend tokenizer.py when Wave 4 starts."
        )
    raise ValueError(f"unsupported lang: {lang!r}")
