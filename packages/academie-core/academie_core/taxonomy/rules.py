"""
AcademIA Error Taxonomy — Step 3: Rule-based span classification
Classifies edit spans deterministically. High precision, zero cost.
Returns unclassified spans for LLM fallback (Step 4).
"""

import re
from dataclasses import dataclass
from .differ import EditSpan
from .categories import TIER1_CATEGORIES


# ── Constants for detect_errors (monolithic pipeline) ──
SPACING_ERRORS = {
    "aswell", "alot", "infact", "eventhough", "nevermind",
    "atleast", "abit", "infront", "eachother", "noone",
}

SPACING_FIX = {
    "aswell": "as well", "alot": "a lot", "infact": "in fact",
    "eventhough": "even though", "nevermind": "never mind",
    "atleast": "at least", "abit": "a bit", "infront": "in front",
    "eachother": "each other", "noone": "no one",
}

PROPER_NOUNS = {
    "english", "french", "spanish", "japanese", "german", "italian",
    "europe", "france", "paris", "lyon", "london", "japan", "china",
    "america", "africa", "asia",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
}


@dataclass
class RuleDetection:
    """A single rule-detected error (for monolithic pipeline)."""
    error_code: str
    original_text: str
    suggested_correction: str
    reasoning: str


@dataclass
class ClassifiedError:
    error_code: str
    original_text: str
    suggested_correction: str
    reasoning: str
    source: str = "rules"


# ── French cognate spelling map (French → English) ──
FRENCH_COGNATES = {
    "confort": "comfort", "confortable": "comfortable",
    "appartment": "apartment", "appartement": "apartment",
    "adress": "address", "adresse": "address",
    "developement": "development", "developpement": "development",
    "gouvernment": "government", "gouvernement": "government",
    "differente": "different", "différente": "different",
    "departement": "department", "département": "department",
    "interessant": "interesting", "intéressant": "interesting",
    "programme": "program",
    "ameliorate": "improve", "améliorer": "improve",
    "responsable": "responsible",
    "independance": "independence",
    "existance": "existence",
    "correspondance": "correspondence",
    "environnement": "environment", "environement": "environment",
    "langage": "language",
    "exemple": "example",
    "examen": "exam",
    "definitly": "definitely", "definately": "definitely",
    "necesary": "necessary", "necessaire": "necessary",
    "occasion": "occasion",
    "personnality": "personality", "personnalité": "personality",
    "carreer": "career", "carrière": "career",
    "prefere": "prefer", "préférer": "prefer",
    "recommand": "recommend", "recommander": "recommend",
    "ressource": "resource",
    "occurence": "occurrence",
    "accomodation": "accommodation",
    "agressive": "aggressive",
    "concience": "conscience",
    "milion": "million",
    "profesional": "professional",
    "recieve": "receive",
    "seperate": "separate",
    "succesful": "successful",
}

# ── Spacing errors ──
SPACING_ERRORS = {
    "aswell", "alot", "infact", "eventhough", "nevermind",
    "atleast", "abit", "infront", "eachother", "noone",
}

# ── French preposition calque patterns ──
PREP_CALQUES = {
    ("depend", "of"): ("depend", "on"),
    ("interested", "by"): ("interested", "in"),
    ("married", "with"): ("married", "to"),
    ("responsible", "of"): ("responsible", "for"),
    ("good", "in"): ("good", "at"),
    ("congratulated", "for"): ("congratulated", "on"),
    ("listen", "the"): ("listen", "to the"),
    ("explain", "me"): ("explain", "to me"),
    ("arrive", "to"): ("arrive", "in/at"),
    ("discuss", "about"): ("discuss", ""),
    ("enter", "in"): ("enter", ""),
    ("assist", "to"): ("attend", ""),
}

# ── Contraction map (no apostrophe → correct) ──
CONTRACTION_MAP = {
    "dont": "don't", "doesnt": "doesn't", "didnt": "didn't",
    "cant": "can't", "couldnt": "couldn't", "wouldnt": "wouldn't",
    "shouldnt": "shouldn't", "isnt": "isn't", "arent": "aren't",
    "wasnt": "wasn't", "werent": "weren't", "hasnt": "hasn't",
    "havent": "haven't", "hadnt": "hadn't", "wont": "won't",
    "thats": "that's", "whos": "who's", "whats": "what's",
    "hes": "he's", "shes": "she's", "theyre": "they're",
    "youre": "you're", "youve": "you've", "weve": "we've",
    "theyve": "they've", "ive": "I've", "im": "I'm",
    "lets": "let's",
}

# ── French lexical calque patterns (regex, fix, reasoning) ──
LEX_CALQUE_PATTERNS = [
    (r"\bi have (\d+) years?\b", "I am \\1 years old", "French calque: 'j'ai X ans' → 'I am X years old'."),
    (r"\bit makes (\d+) (years?|months?|weeks?)\b", "it has been \\1 \\2", "French calque: 'ça fait X ans' → 'it has been X years'."),
    (r"\bi am agree\b", "I agree", "French calque: 'je suis d'accord' → 'I agree'."),
    (r"\b(?:do|does|did|doing) a (walk|trip|travel|journey)\b", "take a \\1", "French calque: 'faire une promenade' → 'take a walk'."),
    (r"\b(?:do|does|did|doing)\s+a\s+(?:\w+\s+)?mistake\b", "make a mistake", "French calque: 'faire une erreur' → 'make a mistake'."),
    (r"\b(?:do|does|did|doing) (?:a |the )?photo\b", "take a photo", "French calque: 'faire une photo' → 'take a photo'."),
    (r"\b(?:do|does|did|doing) (?:a lot of |some )?sport\b", "play sport", "French calque: 'faire du sport' → 'play/do sport'."),
    (r"\bpass(?:ed|es|ing)? (?:an |the |my |his |her )?exam\b", "take an exam", "French calque: 'passer un examen' → 'take an exam' (pass = réussir)."),
    (r"\bmade? a (?:long |big )?travel\b", "took a trip", "French calque: 'faire un voyage' → 'take a trip'."),
    (r"\bopen(?:s|ed|ing)? the light\b", "turn on the light", "French calque: 'ouvrir la lumière' → 'turn on the light'."),
    (r"\bclose[ds]? the light\b", "turn off the light", "French calque: 'fermer la lumière' → 'turn off the light'."),
    (r"\bprofit of\b", "take advantage of", "French calque: 'profiter de' → 'take advantage of'."),
    (r"\bsupport (him|her|them|it|this|that)\b", "stand \\1", "Possible false friend: 'supporter' (FR) = 'to stand/bear', not 'to support'."),
]

# ── Uncountable nouns (plural → singular) ──
# ── Common preposition errors (non-French) ──
PREP_ERRORS = [
    (r"\barrive to\b", "arrive to", "arrive in/at", "Wrong preposition: 'arrive to' → 'arrive in/at'."),
    (r"\bdiscuss about\b", "discuss about", "discuss", "No preposition needed: 'discuss about' → 'discuss'."),
    (r"\benter in\b", "enter in", "enter", "No preposition needed: 'enter in' → 'enter'."),
    (r"\blisten (?!to\b)[a-z]", "listen", "listen to", "Missing preposition: 'listen' → 'listen to'."),
]

UNCOUNTABLE_NOUNS = {
    "informations": "information", "advices": "advice",
    "furnitures": "furniture", "luggages": "luggage",
    "homeworks": "homework", "equipments": "equipment",
    "knowledges": "knowledge", "researches": "research",
    "feedbacks": "feedback", "evidences": "evidence",
    "musics": "music", "moneys": "money",
    "behaviours": "behaviour", "behaviors": "behavior",
}

# ── A1: Irregular past tense (regularized forms) ──
IRREGULAR_PAST_ERRORS = {
    "goed": "went", "comed": "came", "taked": "took", "maked": "made",
    "runned": "ran", "bringed": "brought", "buyed": "bought", "teached": "taught",
    "catched": "caught", "thinked": "thought", "feeled": "felt", "leaved": "left",
    "builded": "built", "sended": "sent", "spended": "spent", "keeped": "kept",
    "finded": "found", "knowed": "knew", "growed": "grew", "drived": "drove",
    "writed": "wrote", "speaked": "spoke", "breaked": "broke", "choosed": "chose",
    "eated": "ate", "drinked": "drank", "gived": "gave", "hided": "hid",
    "holded": "held", "leaded": "led", "meeted": "met", "payed": "paid",
    "rided": "rode", "selled": "sold", "standed": "stood", "swimmed": "swam",
    "weared": "wore", "winned": "won",
}

# ── B1: Gerund-only verbs (verb + to → should be + -ing) ──
GERUND_VERBS = [
    "enjoy", "avoid", "consider", "finish", "imagine", "mind", "miss",
    "practice", "quit", "risk", "suggest", "deny", "keep", "appreciate",
    "postpone", "recommend", "resist",
]

# ── B1-B2: Double comparative/superlative adjectives ──
SHORT_COMPARATIVES = [
    "bigger", "smaller", "taller", "shorter", "faster", "slower", "easier",
    "harder", "nicer", "older", "younger", "cheaper", "richer", "poorer",
    "simpler", "louder", "quieter", "stronger", "weaker", "longer", "wider",
    "thinner", "darker", "lighter", "warmer", "colder", "closer", "newer",
]
SHORT_SUPERLATIVES = [
    "biggest", "smallest", "tallest", "shortest", "fastest", "slowest",
    "easiest", "hardest", "nicest", "oldest", "youngest", "cheapest",
    "simplest", "strongest", "weakest", "longest", "widest", "newest",
]

# ── B1-C1: Make/Do collocations ──
MAKE_NOT_DO = [
    "mistake", "decision", "effort", "progress", "money", "noise",
    "difference", "appointment", "complaint", "suggestion", "arrangement",
    "choice", "promise", "plan", "offer", "comment", "contribution",
]
DO_NOT_MAKE = [
    "homework", "housework", "exercise", "business", "research",
    "damage", "work", "favor", "favour", "harm", "justice", "duty",
]

# ── Error code → family mapping (for tolerance_matrix filtering) ──
ERROR_CODE_TO_FAMILY = {
    "V:TENSE": "verb_tense", "V:SVA": "verb_tense", "V:FORM": "verb_tense",
    "V:COND": "verb_tense", "V:ASPECT": "verb_tense", "V:AUX": "verb_tense",
    "V:INFL": "verb_tense",
    "V:MODAL": "verb_usage", "V:PASS": "verb_usage", "V:EXIST": "verb_usage",
    "V:CHOICE": "verb_usage", "V:PHRASAL": "verb_usage",
    "N:COUNT": "noun_det", "N:INFL": "noun_det", "N:POSS": "noun_det",
    "N:CHOICE": "noun_det", "ART": "noun_det", "ART:GENERIC": "noun_det",
    "DET": "noun_det",
    "PRON:FORM": "pronoun", "PRON:CHOICE": "pronoun", "PRON:REF": "pronoun",
    "WO": "word_order", "WO:QUEST": "word_order",
    "SENT:RUNON": "sentence", "SENT:FRAG": "sentence", "SENT:NEG": "sentence",
    "SENT:MOD": "sentence", "SENT:PARALLEL": "sentence", "SENT:SUBORD": "sentence",
    "MORPH:DERIV": "morphology", "MORPH:WORDCLASS": "morphology",
    "ADJ:CHOICE": "morphology", "ADJ:FORM": "morphology", "ADJ:ORDER": "morphology",
    "ADV:CHOICE": "morphology",
    "SPELL": "surface", "SPELL:COGNATE": "surface", "ORTH:CASE": "surface",
    "ORTH:SPACE": "surface", "PUNCT": "surface", "PUNCT:COMMA": "surface",
    "PUNCT:APOST": "surface", "CONTR": "surface", "REDUND": "surface",
    "PREP": "preposition", "PREP:CALQUE": "calque", "LEX:CALQUE": "calque",
    "LEX:CHOICE": "vocabulary", "LEX:COLLOC": "vocabulary",
    "LEX:FALSE": "vocabulary", "LEX:IDIOM": "vocabulary",
    "LEX:ARGSTRUCT": "vocabulary",
    "DISC:TRANS": "discourse", "DISC:COHER": "discourse",
    "REG:LEVEL": "discourse", "REG:PRAGMA": "discourse",
}

def detect_errors(text: str, lang: str = "en") -> list[RuleDetection]:
    """Run deterministic rules on raw user text. For monolithic pipeline.

    Sprint 5 Phase 4 — dispatch by lang. EN implemented in this file,
    ES lives in rules_es.py (SKELETON). Unknown langs return empty list
    (LLM fallback handles error detection until per-language rules exist).
    """
    if lang == "es":
        from .rules_es import detect_errors_es
        return detect_errors_es(text)
    if lang == "it":
        from .rules_it import detect_errors_it
        return detect_errors_it(text)
    if lang == "de":
        from .rules_de import detect_errors_de
        return detect_errors_de(text)
    if lang in ("jp", "ja"):
        from .rules_jp import detect_errors_jp
        return detect_errors_jp(text)
    if lang == "ru":
        from .rules_ru import detect_errors_ru
        return detect_errors_ru(text)
    if lang != "en":
        return []
    results = []
    text_lower = text.lower()

    # ── ORTH:CASE — Lowercase 'i' as pronoun ──
    if re.search(r"(?<![a-zA-Z])i(?=[\s''])", text):
        results.append(RuleDetection("ORTH:CASE", "i", "I", "Pronoun 'I' must be capitalized."))

    # ── ORTH:CASE — Proper nouns ──
    for word in re.findall(r"\b[a-z]+\b", text):
        if word in PROPER_NOUNS and text.find(word) > 0:
            results.append(RuleDetection("ORTH:CASE", word, word.capitalize(), f"'{word.capitalize()}' is a proper noun."))
            break

    # ── ORTH:SPACE — Joined words ──
    for wrong in SPACING_ERRORS:
        if re.search(rf"\b{re.escape(wrong)}\b", text_lower):
            fix = SPACING_FIX.get(wrong, wrong)
            results.append(RuleDetection("ORTH:SPACE", wrong, fix, f"'{wrong}' should be written as '{fix}'."))

    # ── PUNCT:APOST — Missing apostrophes in contractions ──
    for wrong, fix in CONTRACTION_MAP.items():
        if re.search(rf"\b{re.escape(wrong)}\b", text_lower):
            results.append(RuleDetection("PUNCT:APOST", wrong, fix, f"Missing apostrophe: '{wrong}' → '{fix}'."))

    # ── SPELL:COGNATE — French cognate spelling ──
    for french, english in FRENCH_COGNATES.items():
        if re.search(rf"\b{re.escape(french)}\b", text_lower):
            results.append(RuleDetection("SPELL:COGNATE", french, english, f"French spelling '{french}' → English '{english}'."))

    # ── PREP:CALQUE — French preposition calques ──
    for (word, fr_prep), (_, en_prep) in PREP_CALQUES.items():
        if re.search(rf"\b{re.escape(word)}\s+{re.escape(fr_prep)}\b", text_lower):
            results.append(RuleDetection("PREP:CALQUE", f"{word} {fr_prep}", f"{word} {en_prep}",
                f"French calque: '{word} {fr_prep}' → '{word} {en_prep}'."))
    # "since X years/months" → "for X years/months"
    m = re.search(r"\bsince\s+(\d+)\s+(years?|months?|weeks?|days?|hours?)", text_lower)
    if m:
        results.append(RuleDetection("PREP:CALQUE", f"since {m.group(0).split('since ')[1]}", f"for {m.group(0).split('since ')[1]}",
            "French calque: 'depuis X ans' → use 'for' for duration, not 'since'."))

    # ── LEX:CALQUE — French expression calques ──
    for pattern, fix, reasoning in LEX_CALQUE_PATTERNS:
        if re.search(pattern, text_lower):
            m = re.search(pattern, text_lower)
            results.append(RuleDetection("LEX:CALQUE", m.group(0), fix, reasoning))

    # ── N:COUNT — Uncountable nouns with plural ──
    for wrong, fix in UNCOUNTABLE_NOUNS.items():
        if re.search(rf"\b{re.escape(wrong)}\b", text_lower):
            results.append(RuleDetection("N:COUNT", wrong, fix, f"'{fix}' is uncountable — no plural form."))

    # ── V:MODAL — modal + to (French "devoir de" pattern) ──
    for modal in ["must", "can", "could", "should", "would", "may", "might", "will", "shall"]:
        if re.search(rf"\b{modal}\s+to\s+[a-z]", text_lower):
            results.append(RuleDetection("V:MODAL", f"{modal} to", modal,
                f"No 'to' after modal verb: '{modal} to' → '{modal}'."))
            break

    # ── PREP — common non-French preposition errors ──
    for pattern, orig, fix, reason in PREP_ERRORS:
        if re.search(pattern, text_lower):
            results.append(RuleDetection("PREP", orig, fix, reason))

    # ── PREP — "despite of" ──
    if re.search(r"\bdespite\s+of\b", text_lower):
        results.append(RuleDetection("PREP", "despite of", "despite",
            "No 'of' after 'despite': 'despite of' → 'despite'."))

    # ── V:SVA — Subject-verb agreement (A1) ──
    for subj in ["he", "she", "it"]:
        for verb in ["go", "have", "do", "like", "want", "need", "come", "make", "take", "say",
                      "know", "think", "live", "work", "play", "eat", "drink", "read", "write", "speak"]:
            if re.search(rf"\b{subj}\s+{verb}\b", text_lower):
                if verb == "have":
                    fix = "has"
                elif verb == "do":
                    fix = "does"
                elif verb == "go":
                    fix = "goes"
                elif verb.endswith("y") and verb not in ("play", "say"):
                    fix = verb[:-1] + "ies"
                else:
                    fix = verb + "s"
                results.append(RuleDetection("V:SVA", f"{subj} {verb}", f"{subj} {fix}",
                    f"3rd person singular: '{subj} {verb}' → '{subj} {fix}'."))
                break
        else:
            continue
        break

    # "he/she/it don't" → "doesn't"
    if re.search(r"\b(he|she|it)\s+don'?t\b", text_lower):
        m = re.search(r"\b(he|she|it)\s+don'?t\b", text_lower)
        results.append(RuleDetection("V:SVA", m.group(0), f"{m.group(1)} doesn't",
            "3rd person: 'don't' → 'doesn't'."))

    # "I/you/we/they doesn't" → "don't"
    if re.search(r"\b(i|you|we|they)\s+doesn'?t\b", text_lower):
        m = re.search(r"\b(i|you|we|they)\s+doesn'?t\b", text_lower)
        results.append(RuleDetection("V:SVA", m.group(0), f"{m.group(1)} don't",
            "Plural subject: 'doesn't' → 'don't'."))

    # "there is many/several" → "there are"
    if re.search(r"\bthere\s+is\s+(many|several|numerous|a lot of|lots of|few|some)\b", text_lower):
        results.append(RuleDetection("V:SVA", "there is", "there are",
            "Plural noun: 'there is many' → 'there are many'."))

    # ── V:FORM — Irregular past tense (A1-A2) ──
    for wrong, correct in IRREGULAR_PAST_ERRORS.items():
        if re.search(rf"\b{re.escape(wrong)}\b", text_lower):
            results.append(RuleDetection("V:FORM", wrong, correct,
                f"Irregular past: '{wrong}' → '{correct}'."))

    # ── V:FORM — Gerund verbs + to (B1) ──
    for verb in GERUND_VERBS:
        if re.search(rf"\b{verb}(?:s|ed|ing)?\s+to\s+[a-z]", text_lower):
            m = re.search(rf"\b({verb}(?:s|ed|ing)?)\s+to\s+([a-z]+)", text_lower)
            if m:
                results.append(RuleDetection("V:FORM", f"{m.group(1)} to {m.group(2)}",
                    f"{m.group(1)} {m.group(2)}ing",
                    f"'{m.group(1)}' takes -ing, not 'to': '{m.group(1)} to {m.group(2)}' → '{m.group(1)} {m.group(2)}ing'."))
                break

    # ── V:FORM — "look forward to + base form" (B1) ──
    m = re.search(r"\blook(?:s|ed|ing)?\s+forward\s+to\s+([a-z]+)\b", text_lower)
    if m and not m.group(1).endswith("ing"):
        results.append(RuleDetection("V:FORM", f"forward to {m.group(1)}",
            f"forward to {m.group(1)}ing",
            f"'look forward to' + -ing: 'look forward to {m.group(1)}' → 'look forward to {m.group(1)}ing'."))

    # ── V:FORM — "be used to / get used to + base form" (B1-B2) ──
    m = re.search(r"\b(?:am|is|are|was|were|get|got|getting)\s+used\s+to\s+([a-z]+)\b", text_lower)
    if m and not m.group(1).endswith("ing"):
        results.append(RuleDetection("V:FORM", f"used to {m.group(1)}",
            f"used to {m.group(1)}ing",
            f"'be/get used to' + -ing: 'used to {m.group(1)}' → 'used to {m.group(1)}ing'."))

    # ── V:COND — "if + would/will" in conditional clause (B1) ──
    if re.search(r"\bif\s+(?:i|he|she|it|we|they|you)\s+would\s+(?!like|prefer|rather|mind)", text_lower):
        results.append(RuleDetection("V:COND", "if ... would", "if ... had/past tense",
            "Don't use 'would' in if-clause. Use past tense or past perfect."))
    if re.search(r"\bif\s+(?:i|he|she|it|we|they|you)\s+will\s+", text_lower):
        results.append(RuleDetection("V:COND", "if ... will", "if ... present tense",
            "Don't use 'will' in if-clause. Use present tense."))

    # ── WO:QUEST — Questions without auxiliary (A2) ──
    m = re.search(r"\b(where|when|why|how|what)\s+(you|he|she|they|we)\s+"
                  r"(go|went|like|liked|want|wanted|think|thought|buy|bought|eat|ate|see|saw|get|got)\b",
                  text_lower)
    if m:
        results.append(RuleDetection("WO:QUEST", f"{m.group(1)} {m.group(2)} {m.group(3)}",
            f"{m.group(1)} did {m.group(2)} {m.group(3)}",
            f"Missing auxiliary: '{m.group(1)} {m.group(2)} {m.group(3)}' → '{m.group(1)} did {m.group(2)} ...'."))

    # ── ADJ:FORM — Double comparative/superlative (B2) ──
    comp_pattern = "|".join(re.escape(c) for c in SHORT_COMPARATIVES)
    if re.search(rf"\bmore\s+({comp_pattern})\b", text_lower):
        m = re.search(rf"\bmore\s+({comp_pattern})\b", text_lower)
        results.append(RuleDetection("ADJ:FORM", f"more {m.group(1)}", m.group(1),
            f"Double comparative: 'more {m.group(1)}' → '{m.group(1)}'."))
    sup_pattern = "|".join(re.escape(s) for s in SHORT_SUPERLATIVES)
    if re.search(rf"\bmost\s+({sup_pattern})\b", text_lower):
        m = re.search(rf"\bmost\s+({sup_pattern})\b", text_lower)
        results.append(RuleDetection("ADJ:FORM", f"most {m.group(1)}", m.group(1),
            f"Double superlative: 'most {m.group(1)}' → '{m.group(1)}'."))

    # ── LEX:COLLOC — Make/Do confusion (B1-C1) ──
    for noun in MAKE_NOT_DO:
        if re.search(rf"\b(?:do|does|did|doing)\s+(?:a\s+|an\s+|the\s+)?{re.escape(noun)}\b", text_lower):
            results.append(RuleDetection("LEX:COLLOC", f"do a {noun}", f"make a {noun}",
                f"Collocation: 'do a {noun}' → 'make a {noun}'."))
            break
    for noun in DO_NOT_MAKE:
        if re.search(rf"\b(?:make|makes|made|making)\s+(?:a\s+|an\s+|the\s+|my\s+|his\s+|her\s+)?{re.escape(noun)}\b", text_lower):
            results.append(RuleDetection("LEX:COLLOC", f"make {noun}", f"do {noun}",
                f"Collocation: 'make {noun}' → 'do {noun}'."))
            break

    # ── V:CHOICE — Say/Tell confusion (B1-C1) ──
    if re.search(r"\b(?:said|say|says)\s+(?:me|him|her|us|them)\s+(?:to|that)\b", text_lower):
        m = re.search(r"\b(said|say|says)\s+(me|him|her|us|them)", text_lower)
        results.append(RuleDetection("V:CHOICE", f"{m.group(1)} {m.group(2)}",
            f"told {m.group(2)}",
            f"'say' doesn't take a person: '{m.group(1)} {m.group(2)}' → 'told {m.group(2)}'."))
    if re.search(r"\btold\s+that\b", text_lower):
        results.append(RuleDetection("V:CHOICE", "told that", "said that / told [someone] that",
            "'told' needs a person: 'told that' → 'said that' or 'told [someone] that'."))

    # ── LEX:ARGSTRUCT — "suggest me to" (B1) ──
    if re.search(r"\bsuggest(?:ed|s)?\s+(?:me|him|her|us|them)\s+to\b", text_lower):
        results.append(RuleDetection("LEX:ARGSTRUCT", "suggest ... to", "suggest + -ing / suggest that",
            "'suggest' doesn't take 'someone + to': use 'suggest + -ing' or 'suggest that...'."))

    return results


# ── Time markers that signal V:TENSE with present perfect ──
FINISHED_TIME_MARKERS = [
    "yesterday", "last week", "last month", "last year", "last summer",
    "last night", "last friday", "last monday", "last tuesday",
    "ago", "in 2020", "in 2021", "in 2022", "in 2023", "in 2024", "in 2025",
    "before moving", "before leaving", "when i was", "when she was", "when he was",
]


def classify_edits(edits: list[EditSpan], full_original: str = "") -> tuple[list[ClassifiedError], list[EditSpan]]:
    """
    Classify edit spans using deterministic rules.
    Returns (classified_errors, unclassified_spans_for_llm_fallback).
    """
    classified = []
    unclassified = []

    for edit in edits:
        result = _try_classify(edit, full_original)
        if result:
            classified.append(result)
        else:
            unclassified.append(edit)

    return classified, unclassified


def _try_classify(edit: EditSpan, full_original: str) -> ClassifiedError | None:
    """Try all classification rules on an edit span. Return first match or None."""
    orig = edit.original
    corr = edit.corrected

    # Skip empty diffs
    if not orig and not corr:
        return None

    # ── ORTH:CASE — same text, different case ──
    if orig and corr and orig.lower() == corr.lower() and orig != corr:
        return ClassifiedError(
            error_code="ORTH:CASE",
            original_text=orig,
            suggested_correction=corr,
            reasoning=_case_reasoning(orig, corr),
        )

    # ── ORTH:SPACE — word was split or joined ──
    if orig and corr and orig.lower().replace(" ", "") == corr.lower().replace(" ", ""):
        if " " in corr and " " not in orig:
            return ClassifiedError(
                error_code="ORTH:SPACE",
                original_text=orig,
                suggested_correction=corr,
                reasoning=f"'{orig}' should be written as '{corr}' (two words).",
            )
    if orig.lower() in SPACING_ERRORS:
        return ClassifiedError(
            error_code="ORTH:SPACE",
            original_text=orig,
            suggested_correction=corr,
            reasoning=f"'{orig}' should be written as separate words.",
        )

    # ── PUNCT:APOST — missing apostrophe ──
    apost = _check_apostrophe(orig, corr)
    if apost:
        return apost

    # ── SPELL:COGNATE — French spelling ──
    if orig.lower() in FRENCH_COGNATES:
        return ClassifiedError(
            error_code="SPELL:COGNATE",
            original_text=orig,
            suggested_correction=corr,
            reasoning=f"French spelling '{orig}' → English '{corr}'.",
        )

    # ── SPELL — misspelling (not French cognate) ──
    spell = _check_spelling(orig, corr)
    if spell:
        return spell

    # ── N:NUM — countability/plural ──
    num = _check_noun_number(orig, corr)
    if num:
        return num

    # ── V:TENSE — tense change with time marker ──
    tense = _check_tense(orig, corr, edit.context)
    if tense:
        return tense

    # ── V:SVA — agreement change ──
    sva = _check_sva(orig, corr)
    if sva:
        return sva

    # ── PREP:CALQUE — French preposition pattern ──
    prep_calque = _check_prep_calque(orig, corr, edit.context)
    if prep_calque:
        return prep_calque

    # Not classified by rules → send to LLM fallback
    return None


# ══════════════════════════════════════════════════════════
# Individual rule implementations
# ══════════════════════════════════════════════════════════

def _case_reasoning(orig: str, corr: str) -> str:
    if orig == "i" and corr == "I":
        return "Pronoun 'I' must always be capitalized."
    if orig[0].islower() and corr[0].isupper():
        return f"'{corr}' should be capitalized (proper noun or sentence start)."
    return f"Capitalization: '{orig}' → '{corr}'."


def _check_apostrophe(orig: str, corr: str) -> ClassifiedError | None:
    """Detect missing apostrophes in contractions."""
    # Map of no-apostrophe form → correct form
    contraction_map = {
        "dont": "don't", "doesnt": "doesn't", "didnt": "didn't",
        "cant": "can't", "couldnt": "couldn't", "wouldnt": "wouldn't",
        "shouldnt": "shouldn't", "isnt": "isn't", "arent": "aren't",
        "wasnt": "wasn't", "werent": "weren't", "hasnt": "hasn't",
        "havent": "haven't", "hadnt": "hadn't", "wont": "won't",
        "its": "it's",  # only when corrected to it's (not possessive)
        "thats": "that's", "whos": "who's", "whats": "what's",
        "hes": "he's", "shes": "she's", "theyre": "they're",
        "youre": "you're", "were": "we're",  # careful: "were" can be past tense
        "youve": "you've", "weve": "we've", "theyve": "they've",
        "ive": "I've", "ill": "I'll", "im": "I'm",
    }
    orig_lower = orig.lower()
    if orig_lower in contraction_map and corr and "'" in corr:
        return ClassifiedError(
            error_code="PUNCT:APOST",
            original_text=orig,
            suggested_correction=corr,
            reasoning=f"Missing apostrophe: '{orig}' → '{corr}'.",
        )
    # Also catch: original has no apostrophe, correction does, same letters
    if orig and corr and "'" not in orig and "'" in corr:
        if orig.lower().replace("'", "") == corr.lower().replace("'", ""):
            return ClassifiedError(
                error_code="PUNCT:APOST",
                original_text=orig,
                suggested_correction=corr,
                reasoning=f"Missing apostrophe: '{orig}' → '{corr}'.",
            )
    return None


def _check_spelling(orig: str, corr: str) -> ClassifiedError | None:
    """
    Detect OBVIOUS misspellings only. Very conservative to avoid false positives.
    Only flags: same length ±1, same first 2 letters, high similarity (>75%).
    Different words (play→plays, have→has) are NOT spelling errors.
    """
    if not orig or not corr:
        return None
    o, c = orig.lower(), corr.lower()
    if o == c:
        return None
    if len(o) < 4 or len(c) < 4:
        return None
    # Reject if it looks like a morphological change (verb conjugation, plural, etc.)
    # If one is a substring of the other + 1-2 chars, it's likely morphology not spelling
    if o.startswith(c) or c.startswith(o):
        return None
    if o.endswith("s") and c == o[:-1]:  # plays → play = not spelling
        return None
    if c.endswith("s") and o == c[:-1]:  # play → plays = not spelling
        return None
    # Must have same first 2 letters and very high similarity
    if o[:2] != c[:2]:
        return None
    if abs(len(o) - len(c)) > 2:
        return None
    common = sum(1 for a, b in zip(o, c) if a == b)
    similarity = common / max(len(o), len(c))
    if similarity < 0.75:
        return None
    # Not a French cognate, not a contraction
    if o in FRENCH_COGNATES or "'" in corr:
        return None
    return ClassifiedError(
        error_code="SPELL",
        original_text=orig,
        suggested_correction=corr,
        reasoning=f"Misspelling: '{orig}' → '{corr}'.",
    )


def _check_noun_number(orig: str, corr: str) -> ClassifiedError | None:
    """Detect countability/plural errors."""
    uncountables = {
        "informations": "information", "advices": "advice",
        "furnitures": "furniture", "luggages": "luggage",
        "homeworks": "homework", "equipments": "equipment",
        "knowledges": "knowledge", "researches": "research",
        "feedbacks": "feedback", "evidences": "evidence",
        "newses": "news", "progresses": "progress",
        "behaviours": "behaviour", "behaviors": "behavior",
        "musics": "music", "moneys": "money",
    }
    if orig.lower() in uncountables:
        return ClassifiedError(
            error_code="N:NUM",
            original_text=orig,
            suggested_correction=corr,
            reasoning=f"'{corr}' is uncountable in English (no plural -s).",
        )
    return None


def _check_tense(orig: str, corr: str, context: str) -> ClassifiedError | None:
    """Detect tense errors, especially present perfect + finished time."""
    if not orig or not corr:
        return None

    o, c = orig.lower(), corr.lower()
    ctx = context.lower()

    # Present perfect → past simple (with finished time marker)
    has_time_marker = any(marker in ctx for marker in FINISHED_TIME_MARKERS)

    # Check: "have/has + past participle" in original, simple past in correction
    pp_patterns = [
        (r"\bhave\b", r"\b(went|saw|ate|did|made|came|got|took|gave|said)\b"),
        (r"\bhas\b", r"\b(went|saw|ate|did|made|came|got|took|gave|said)\b"),
        (r"\bhave been\b", r"\b(went|was)\b"),
        (r"\bhas been\b", r"\b(went|was)\b"),
        (r"\bhave seen\b", r"\bsaw\b"),
        (r"\bhave eaten\b", r"\bate\b"),
        (r"\bhave visited\b", r"\bvisited\b"),
        (r"\bhave finished\b", r"\bfinished\b"),
        (r"\bhave played\b", r"\bplayed\b"),
    ]

    for pp_pat, past_pat in pp_patterns:
        if re.search(pp_pat, o) and re.search(past_pat, c) and has_time_marker:
            return ClassifiedError(
                error_code="V:TENSE",
                original_text=orig,
                suggested_correction=corr,
                reasoning="Present perfect used with a finished time marker — simple past required.",
            )

    # Reverse: simple past → present perfect (with since/for/already)
    ongoing_markers = ["since", "already", "just", "yet", "ever", "never"]
    has_ongoing = any(marker in ctx for marker in ongoing_markers)
    if has_ongoing and "have" in c and "have" not in o:
        return ClassifiedError(
            error_code="V:TENSE",
            original_text=orig,
            suggested_correction=corr,
            reasoning="Simple past used with ongoing time marker — present perfect required.",
        )

    return None


def _check_sva(orig: str, corr: str) -> ClassifiedError | None:
    """Detect subject-verb agreement errors."""
    sva_pairs = {
        ("have", "has"), ("has", "have"),
        ("was", "were"), ("were", "was"),
        ("is", "are"), ("are", "is"),
        ("do", "does"), ("does", "do"),
        ("play", "plays"), ("plays", "play"),
        ("go", "goes"), ("goes", "go"),
        ("depend", "depends"), ("depends", "depend"),
        ("work", "works"), ("works", "work"),
        ("live", "lives"), ("lives", "live"),
        ("like", "likes"), ("likes", "like"),
        ("want", "wants"), ("wants", "want"),
        ("need", "needs"), ("needs", "need"),
        ("think", "thinks"), ("thinks", "think"),
        ("come", "comes"), ("comes", "come"),
        ("make", "makes"), ("makes", "make"),
        ("take", "takes"), ("takes", "take"),
        ("know", "knows"), ("knows", "know"),
        ("seem", "seems"), ("seems", "seem"),
    }
    pair = (orig.lower(), corr.lower())
    if pair in sva_pairs:
        return ClassifiedError(
            error_code="V:SVA",
            original_text=orig,
            suggested_correction=corr,
            reasoning=f"Subject-verb agreement: '{orig}' → '{corr}'.",
        )
    return None


def _check_prep_calque(orig: str, corr: str, context: str) -> ClassifiedError | None:
    """Detect French preposition calques."""
    ctx_lower = context.lower()
    for (word, fr_prep), (_, en_prep) in PREP_CALQUES.items():
        pattern = rf"\b{re.escape(word)}\s+{re.escape(fr_prep)}\b"
        if re.search(pattern, ctx_lower):
            if orig.lower() == fr_prep and corr.lower() == en_prep:
                return ClassifiedError(
                    error_code="PREP:CALQUE",
                    original_text=f"{word} {fr_prep}",
                    suggested_correction=f"{word} {en_prep}",
                    reasoning=f"French calque: '{word} {fr_prep}' (FR: {word} {fr_prep}) → '{word} {en_prep}'.",
                )
    # Also catch "since X years" → "for X years"
    if orig.lower() == "since" and corr.lower() == "for":
        if re.search(r"since\s+\d+\s+(year|month|week|day|hour)", ctx_lower):
            return ClassifiedError(
                error_code="PREP:CALQUE",
                original_text=orig,
                suggested_correction=corr,
                reasoning="French calque: 'depuis X ans' → 'since' is wrong for duration, use 'for'.",
            )
    return None
