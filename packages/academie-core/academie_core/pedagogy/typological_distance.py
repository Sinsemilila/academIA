"""Typological distance classification for L1/L2 scaffolding policy.

Grounded in Chiswick & Miller (2005) "Linguistic Distance: A Quantitative
Measure of the Distance Between English and Other Languages" (*J. of
Multilingual and Multicultural Development* 26) and Ringbom (2007)
*Cross-linguistic Similarity in Foreign Language Learning*.

Close pairs share family + shared cognate floor + similar syntax.
Distant pairs differ in script + morphosyntax + lack shared Latin/Greek floor.
"""
from __future__ import annotations

from typing import Literal

Distance = Literal["close", "medium", "distant"]

# Symmetric for any L1 in the key pair. Default "medium" if not listed.
# Bucket assignment rationale:
#   close   — same sub-family, high cognate density, shared morphosyntax
#   medium  — different family but shared script + significant Latinate floor
#   distant — different script/morphosyntax/typology
_DISTANCE_TABLE: dict[frozenset[str], Distance] = {
    # Romance pairs
    frozenset({"fr", "es"}): "close",
    frozenset({"fr", "it"}): "close",
    frozenset({"fr", "pt"}): "close",
    frozenset({"fr", "ca"}): "close",
    frozenset({"fr", "ro"}): "close",
    frozenset({"es", "it"}): "close",
    frozenset({"es", "pt"}): "close",
    frozenset({"es", "ca"}): "close",
    frozenset({"it", "pt"}): "close",
    # Germanic-Romance (medium: shared Latin floor, different morphology)
    frozenset({"fr", "en"}): "medium",
    frozenset({"fr", "de"}): "medium",
    frozenset({"fr", "nl"}): "medium",
    frozenset({"es", "en"}): "medium",
    frozenset({"it", "en"}): "medium",
    frozenset({"pt", "en"}): "medium",
    # Intra-Germanic
    frozenset({"en", "de"}): "close",
    frozenset({"en", "nl"}): "close",
    frozenset({"de", "nl"}): "close",
    # Distant pairs (non-IE or distant-IE with different script/typology)
    frozenset({"fr", "ja"}): "distant",
    frozenset({"fr", "ko"}): "distant",
    frozenset({"fr", "zh"}): "distant",
    frozenset({"fr", "ar"}): "distant",
    frozenset({"fr", "ru"}): "distant",
    frozenset({"fr", "tr"}): "distant",
    frozenset({"fr", "he"}): "distant",
    frozenset({"en", "ja"}): "distant",
    frozenset({"en", "ko"}): "distant",
    frozenset({"en", "zh"}): "distant",
    frozenset({"en", "ar"}): "distant",
    frozenset({"en", "ru"}): "distant",
    frozenset({"es", "ja"}): "distant",
    frozenset({"es", "ru"}): "distant",
    # Slavic-Romance (medium — different script/morpho but shared IE floor)
    frozenset({"fr", "pl"}): "medium",
    frozenset({"fr", "cs"}): "medium",
}


def get_distance(l1: str, target: str) -> Distance:
    """Return typological distance between two ISO-639-1 codes.

    Symmetric. Unknown pairs default to 'medium' (safer than assuming close).
    Case-insensitive.
    """
    if not l1 or not target:
        return "medium"
    pair = frozenset({l1.lower(), target.lower()})
    if len(pair) == 1:
        return "close"
    return _DISTANCE_TABLE.get(pair, "medium")
