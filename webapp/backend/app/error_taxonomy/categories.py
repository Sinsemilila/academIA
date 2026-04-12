"""
AcademIA Error Taxonomy — Tier 1 categories (Phase 1)
15 categories for launch. Expand toward 63 with data validation.
"""

TIER1_CATEGORIES = {
    # Grammar — Verb (12)
    "V:TENSE", "V:SVA", "V:FORM", "V:MODAL", "V:COND", "V:ASPECT", "V:AUX",
    "V:INFL", "V:PASS", "V:EXIST", "V:CHOICE", "V:PHRASAL",
    # Grammar — Noun (5)
    "N:NUM", "N:POSS", "N:INFL", "N:CHOICE", "N:COUNT",
    # Grammar — Article/Det (3)
    "ART", "ART:GENERIC", "DET",
    # Grammar — Pronoun (3)
    "PRON:FORM", "PRON:CHOICE", "PRON:REF",
    # Grammar — Preposition (2)
    "PREP", "PREP:CALQUE",
    # Grammar — Adjective (3)
    "ADJ:CHOICE", "ADJ:FORM", "ADJ:ORDER",
    # Grammar — Adverb (2)
    "ADV:CHOICE", "ADV:ORDER",
    # Grammar — Conjunction (1)
    "CONJ",
    # Grammar — Word Order (2)
    "WO", "WO:QUEST",
    # Lexical (7)
    "LEX:CHOICE", "LEX:COLLOC", "LEX:FALSE", "LEX:CALQUE",
    "LEX:IDIOM", "LEX:ARGSTRUCT", "LEX:REGISTER",
    # Morphology (2)
    "MORPH:DERIV", "MORPH:WORDCLASS",
    # Sentence structure (6)
    "SENT:RUNON", "SENT:FRAG", "SENT:NEG", "SENT:MOD", "SENT:PARALLEL", "SENT:SUBORD",
    # Discourse (4)
    "DISC:TRANS", "DISC:COHER", "DISC:COHES", "DISC:CONNOVER",
    # Register (2)
    "REG:LEVEL", "REG:PRAGMA",
    # Surface — Spelling (4)
    "SPELL", "SPELL:COGNATE", "ORTH:CASE", "ORTH:SPACE",
    # Surface — Punctuation (3)
    "PUNCT", "PUNCT:COMMA", "PUNCT:APOST",
    # Other (2)
    "CONTR", "REDUND",
}

TIER1_DOMAINS = {
    "grammar_verb": ["V:TENSE", "V:SVA", "V:FORM", "V:MODAL", "V:COND", "V:ASPECT", "V:AUX", "V:INFL", "V:PASS", "V:EXIST"],
    "grammar_other": ["N:NUM", "N:POSS", "N:INFL", "ART", "PREP", "WO", "ADJ:ORDER", "ADV:ORDER", "PRON:FORM", "PRON:CHOICE"],
    "sentence": ["SENT:RUNON", "SENT:FRAG", "SENT:NEG", "CONJ"],
    "surface": ["ORTH:CASE", "ORTH:SPACE", "SPELL", "PUNCT:APOST"],
    "lexical": ["LEX:CHOICE"],
    "l1_transfer": ["PREP:CALQUE", "SPELL:COGNATE"],
}


def is_valid_code(code: str) -> bool:
    return code in TIER1_CATEGORIES
