"""
AcademIA Error Taxonomy — Tier 1 categories (Phase 1)
15 categories for launch. Expand toward 63 with data validation.
"""

TIER1_CATEGORIES = {
    # Grammar
    "V:TENSE", "V:SVA", "V:FORM", "N:NUM", "ART", "PREP", "WO",
    # Surface
    "ORTH:CASE", "ORTH:SPACE", "SPELL", "PUNCT:APOST",
    # Lexical (LEX:CALQUE merged into LEX:CHOICE — 2026-04-12 Phase 1b)
    "LEX:CHOICE",
    # L1 Transfer (French-specific)
    "PREP:CALQUE", "SPELL:COGNATE",
}

TIER1_DOMAINS = {
    "grammar": ["V:TENSE", "V:SVA", "V:FORM", "N:NUM", "ART", "PREP", "WO"],
    "surface": ["ORTH:CASE", "ORTH:SPACE", "SPELL", "PUNCT:APOST"],
    "lexical": ["LEX:CHOICE"],
    "l1_transfer": ["PREP:CALQUE", "SPELL:COGNATE"],
}


def is_valid_code(code: str) -> bool:
    return code in TIER1_CATEGORIES
