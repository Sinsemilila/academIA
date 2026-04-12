"""
AcademIA Error Taxonomy — Tier 1 categories (Phase 1)
15 categories for launch. Expand toward 63 with data validation.
"""

TIER1_CATEGORIES = {
    # Grammar — Verb
    "V:TENSE", "V:SVA", "V:FORM", "V:MODAL", "V:COND", "V:ASPECT", "V:AUX",
    # Grammar — Other
    "N:NUM", "ART", "PREP", "WO",
    # Adjective/Adverb
    "ADJ:ORDER", "ADV:ORDER",
    # Pronoun
    "PRON:FORM", "PRON:CHOICE",
    # Sentence structure
    "SENT:RUNON", "SENT:FRAG", "SENT:NEG", "CONJ",
    # Surface
    "ORTH:CASE", "ORTH:SPACE", "SPELL", "PUNCT:APOST",
    # Lexical
    "LEX:CHOICE",
    # L1 Transfer (French-specific)
    "PREP:CALQUE", "SPELL:COGNATE",
}

TIER1_DOMAINS = {
    "grammar_verb": ["V:TENSE", "V:SVA", "V:FORM", "V:MODAL", "V:COND", "V:ASPECT", "V:AUX"],
    "grammar_other": ["N:NUM", "ART", "PREP", "WO", "ADJ:ORDER", "ADV:ORDER", "PRON:FORM", "PRON:CHOICE"],
    "sentence": ["SENT:RUNON", "SENT:FRAG", "SENT:NEG", "CONJ"],
    "surface": ["ORTH:CASE", "ORTH:SPACE", "SPELL", "PUNCT:APOST"],
    "lexical": ["LEX:CHOICE"],
    "l1_transfer": ["PREP:CALQUE", "SPELL:COGNATE"],
}


def is_valid_code(code: str) -> bool:
    return code in TIER1_CATEGORIES
