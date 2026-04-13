"""
AcademIA Error Taxonomy — 57 effective categories (63 model outputs, 6 fused)
Fusions applied in llm.py post-mapping: ADV:ORDER→WO, N:NUM→N:COUNT,
LEX:REGISTER→REG:LEVEL, DISC:COHES→DISC:COHER, DISC:CONNOVER→DISC:COHER, CONJ→SENT:RUNON
"""

TIER1_CATEGORIES = {
    # Grammar — Verb (12)
    "V:TENSE", "V:SVA", "V:FORM", "V:MODAL", "V:COND", "V:ASPECT", "V:AUX",
    "V:INFL", "V:PASS", "V:EXIST", "V:CHOICE", "V:PHRASAL",
    # Grammar — Noun (4) — N:NUM fused into N:COUNT
    "N:POSS", "N:INFL", "N:CHOICE", "N:COUNT",
    # Grammar — Article/Det (3)
    "ART", "ART:GENERIC", "DET",
    # Grammar — Pronoun (3)
    "PRON:FORM", "PRON:CHOICE", "PRON:REF",
    # Grammar — Preposition (2)
    "PREP", "PREP:CALQUE",
    # Grammar — Adjective (3)
    "ADJ:CHOICE", "ADJ:FORM", "ADJ:ORDER",
    # Grammar — Adverb (1) — ADV:ORDER fused into WO
    "ADV:CHOICE",
    # Grammar — Word Order (2) — absorbs ADV:ORDER
    "WO", "WO:QUEST",
    # Lexical (6) — LEX:REGISTER fused into REG:LEVEL
    "LEX:CHOICE", "LEX:COLLOC", "LEX:FALSE", "LEX:CALQUE",
    "LEX:IDIOM", "LEX:ARGSTRUCT",
    # Morphology (2)
    "MORPH:DERIV", "MORPH:WORDCLASS",
    # Sentence structure (6) — CONJ fused into SENT:RUNON
    "SENT:RUNON", "SENT:FRAG", "SENT:NEG", "SENT:MOD", "SENT:PARALLEL", "SENT:SUBORD",
    # Discourse (2) — DISC:COHES + DISC:CONNOVER fused into DISC:COHER
    "DISC:TRANS", "DISC:COHER",
    # Register (2) — absorbs LEX:REGISTER
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
    "grammar_other": ["N:POSS", "N:INFL", "ART", "PREP", "WO", "ADJ:ORDER", "PRON:FORM", "PRON:CHOICE"],
    "sentence": ["SENT:RUNON", "SENT:FRAG", "SENT:NEG"],
    "surface": ["ORTH:CASE", "ORTH:SPACE", "SPELL", "PUNCT:APOST"],
    "lexical": ["LEX:CHOICE"],
    "l1_transfer": ["PREP:CALQUE", "SPELL:COGNATE"],
}


def is_valid_code(code: str) -> bool:
    return code in TIER1_CATEGORIES
