"""
AcademIA Error Taxonomy — Step 3: Rule-based span classification
Classifies edit spans deterministically. High precision, zero cost.
Returns unclassified spans for LLM fallback (Step 4).
"""

import re
from dataclasses import dataclass
from .differ import EditSpan
from .categories import TIER1_CATEGORIES


@dataclass
class ClassifiedError:
    error_code: str
    original_text: str
    suggested_correction: str
    reasoning: str
    source: str = "rules"  # "rules" or "llm-fallback"


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
}

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
