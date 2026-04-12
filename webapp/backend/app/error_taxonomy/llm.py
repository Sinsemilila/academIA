"""
AcademIA Error Taxonomy — LLM layer
Monolithic prompt approach: LLM finds AND classifies errors in one pass.
Best F1 on Groq Llama 3.3 70B.
"""

import json
import logging
import re
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel
from .categories import TIER1_CATEGORIES

logger = logging.getLogger("academie-api.error-taxonomy")

LITELLM_URL = "http://litellm-proxy:4000/v1/chat/completions"
# gpt-4o-mini for dev/tuning (1.5M tokens/day free, no rate limit issues)
# Switch to groq-standard for production once tuned
ANALYSIS_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """You analyze French speakers learning English. Identify EVERY error made by the USER. Do NOT analyze TEACHER messages.

═══ ANALYSIS METHOD ═══

For EACH user message, perform a 3-PASS SCAN:

PASS 1 — SURFACE: Is 'i' lowercase? Proper nouns lowercase? Missing apostrophes (dont→don't, cant→can't, its→it's, theyre→they're, shes→she's, whos→who's)? Joined words (aswell, alot)? Misspellings? French spelling (confort→comfort)?

PASS 2 — GRAMMAR: Subject-verb agreement (she have→has)? Wrong tense (present perfect + yesterday/ago/last = use past simple)? Wrong verb form (enjoy to swim→swimming)? Modal error (must to go→must go)? Conditional error (if I would→if I)? Progressive/aspect misuse (I am understanding→I understand)? Auxiliary/do-support missing (I not understand→I don't)? Singular/plural (informations→information)? Articles? Prepositions? French preposition calque (depend of→on)? Word order?

PASS 3 — LEXICAL: Wrong word? French calque expression (I have 25 years→I am 25)?

CRITICAL: A message often has 3-5+ errors. Report ALL. Do not stop after the obvious ones.

Output ONLY valid JSON. No other text."""

USER_PROMPT_TEMPLATE = """Classify errors using ONLY these 63 codes:

V:TENSE — wrong tense (have been + last summer → went)
V:SVA — subject-verb agreement (she have → has)
V:FORM — gerund/infinitive/participle (enjoy to swim → swimming)
V:MODAL — modal verb error (should goes → should go, must to go → must go)
V:COND — conditional structure error (if I would know → if I knew)
V:ASPECT — progressive/continuous misuse (I am understanding → I understand)
V:AUX — auxiliary error, do-support (I not understand → I don't understand)
V:INFL — non-standard verb inflection (goed → went, runned → ran)
V:PASS — passive voice error (The book wrote by → was written by)
V:EXIST — existential construction, French calque (It has many people → There are)
N:NUM — singular/plural/countability (informations → information)
N:POSS — possessive marking (student book → student's book)
N:INFL — non-standard noun inflection (childs → children)
N:CHOICE — wrong noun (a good work → a good job)
N:COUNT — countability error (an advice → a piece of advice)
ART — article error (I bought car → a car)
ART:GENERIC — zero article for generics, French transfer (the life → life, the music → music)
DET — determiner error (this books → these books, much people → many)
PREP — wrong preposition, NOT French (arrive to → in)
PREP:CALQUE — French preposition calque (depend of → on, since 5 years → for)
WO — word order (speaks well English → English well)
WO:QUEST — question word order (Where you go? → Where do you go?)
ADJ:CHOICE — wrong adjective (a big temperature → a high temperature)
ADJ:FORM — comparative/superlative (more big → bigger)
ADJ:ORDER — adjective placement, French (a car red → a red car)
ADV:CHOICE — wrong adverb
ADV:ORDER — adverb misplaced (He drives always → He always drives)
PRON:FORM — pronoun case (Him went → He went)
PRON:CHOICE — wrong pronoun (the man which → who)
PRON:REF — unclear pronoun reference (John told Bill he was wrong — ambiguous)
SENT:RUNON — run-on / comma splice (I like cats I hate dogs)
SENT:FRAG — sentence fragment (Because I was tired.)
SENT:NEG — negation error (don't have nothing → anything)
SENT:MOD — dangling/misplaced modifier (Walking, the trees were nice)
SENT:PARALLEL — parallelism (likes reading, to swim, and biking)
SENT:SUBORD — subordinate clause error
CONJ — conjunction error (and → although)
LEX:CHOICE — wrong word or French calque (I have 25 years → I am 25)
LEX:COLLOC — collocation error (do a mistake → make a mistake)
LEX:FALSE — false friend (actually ≠ actuellement)
LEX:CALQUE — literal French translation (it makes 3 years → it's been)
LEX:IDIOM — idiom error
LEX:ARGSTRUCT — argument structure (explain me → explain to me)
LEX:REGISTER — word-level register (gonna in formal context)
MORPH:DERIV — derivation error (hapiness → happiness)
MORPH:WORDCLASS — wrong word class (I am very happiness → happy)
DISC:TRANS — transition/connector error (missing or wrong linking word)
DISC:COHER — coherence (logical flow problem)
DISC:COHES — cohesion (cross-sentence reference)
DISC:CONNOVER — connector overuse, French essay style (moreover/furthermore spam)
REG:LEVEL — register formality (too formal/informal for context)
REG:PRAGMA — pragmatic error (too direct: Give me the salt → Could you pass)
ORTH:CASE — capitalization (i → I, paris → Paris)
ORTH:SPACE — spacing (aswell → as well)
SPELL — misspelling, NOT French (definately → definitely)
SPELL:COGNATE — French spelling (confort → comfort, gouvernment → government)
PUNCT — punctuation error (period, semicolon)
PUNCT:COMMA — comma error
PUNCT:APOST — missing apostrophe (dont → don't, its=it is → it's)
CONTR — contraction error (n't → not expansion/contraction)
REDUND — redundancy (return back → return)

{{"errors": [{{"turn": N, "original": "quote", "correction": "fix", "codes": ["CODE"], "reasoning": "why"}}]}}

If no errors: {{"errors": []}}

VERB DISAMBIGUATION:
- V:MODAL = error with can/could/should/would/must/may/might + verb (must to go, should goes)
- V:COND = error in if-clause conditional structure (if I would know → if I knew, if I would have → if I had)
- V:ASPECT = using progressive -ing with stative verb OR missing progressive (I am understanding → I understand, She reads right now → She is reading)
- V:AUX = missing/wrong auxiliary, especially do-support (I not understand → I don't understand, You like? → Do you like?)
- V:TENSE = wrong tense choice based on time context (NOT modal/conditional/aspect/auxiliary)
- V:FORM = wrong infinitive/gerund/participle form (NOT tense, NOT modal)
- V:SVA = subject-verb number disagreement (she have → has)

MORE DISAMBIGUATION (READ CAREFULLY):

N:NUM vs N:INFL vs N:COUNT — THREE DIFFERENT THINGS:
- N:NUM = wrong singular/plural of a REGULAR noun (many student → students)
- N:INFL = IRREGULAR plural wrong (childs → children, mouses → mice, foots → feet)
- N:COUNT = UNCOUNTABLE noun given plural/article (informations → information, furnitures → furniture, equipments → equipment, luggages → luggage, homeworks → homework, advices → advice). These are N:COUNT, NOT N:INFL.

V:CHOICE vs LEX:COLLOC — which verb is wrong?
- V:CHOICE = wrong verb entirely (said me → told me, make a travel → take a trip)
- LEX:COLLOC = right verb but wrong verb+noun COMBINATION (do a mistake → make a mistake, do sport → play sport, do a photo → take a photo)

V:PHRASAL = wrong/missing particle in phrasal verb (look in → look into, give up of → give up, look forward the → look forward to the)

PREP vs PREP:CALQUE — is it a French pattern?
- PREP:CALQUE = the preposition matches French usage (depend of=dépendre de, interested by=intéressé par, married with=marié avec, since 5 years=depuis 5 ans)
- PREP = wrong preposition NOT from French (arrive to London, discuss about)

SPELL vs SPELL:COGNATE — is it a French word?
- SPELL:COGNATE = the misspelling IS the French word (confort, appartment, gouvernment, differente, departement, developement)
- SPELL = NOT a French word (definately, enviroment, recieved)

SENT:SUBORD = wrong subordinate clause STRUCTURE (embedded question order: "I dont know that should I go" → "I don't know if I should go"). NOT a word order error — use SENT:SUBORD, not WO.

WO:QUEST = question WITHOUT do-support/inversion (Where you go? → Where do you go?, What time the movie starts? → What time does the movie start?). This is NOT V:AUX.

LEX:FALSE = French false friend USED WITH FRENCH MEANING (actually meaning "currently", library meaning "bookshop", sympathetic meaning "nice"). Only flag if the FRENCH meaning is intended.

LEX:REGISTER = informal WORD in formal context (gonna, wanna, chill in business writing)
REG:LEVEL = overall text FORMALITY mismatch (yo professor, hey dude in formal email)

RULES:
- One entry per distinct error
- A turn can have multiple errors → multiple entries
- Contractions without apostrophes = ALWAYS PUNCT:APOST
- French spelling (confort, adresse, gouvernment) = ALWAYS SPELL:COGNATE not SPELL
- French preposition (depend of, interested by) = ALWAYS PREP:CALQUE not PREP
- V:CHOICE vs LEX:CHOICE: if the VERB itself is wrong (said→told, do→make), use V:CHOICE. If a non-verb word is wrong, use LEX:CHOICE

### Examples:

Turn 1: "i lived in paris since 5 years"
{{"turn":1,"original":"i","correction":"I","codes":["ORTH:CASE"],"reasoning":"Pronoun I must be capitalized"}}
{{"turn":1,"original":"lived","correction":"have lived","codes":["V:TENSE"],"reasoning":"Present perfect needed with since for ongoing duration"}}
{{"turn":1,"original":"paris","correction":"Paris","codes":["ORTH:CASE"],"reasoning":"Proper noun"}}
{{"turn":1,"original":"since 5 years","correction":"for 5 years","codes":["PREP:CALQUE"],"reasoning":"French depuis calque"}}

Turn 2: "She dont depend of her parents"
{{"turn":2,"original":"dont","correction":"doesn't","codes":["PUNCT:APOST"],"reasoning":"Missing apostrophe + 3rd person"}}
{{"turn":2,"original":"depend of","correction":"depend on","codes":["PREP:CALQUE"],"reasoning":"French dépendre de"}}

Turn 3: "She speaks very well English"
{{"turn":3,"original":"speaks very well English","correction":"speaks English very well","codes":["WO"],"reasoning":"Adverb follows object"}}

Turn 4: "He must to go to the hospital right now"
{{"turn":4,"original":"must to go","correction":"must go","codes":["V:MODAL"],"reasoning":"No 'to' after modal verbs"}}

Turn 5: "If I would know the answer I would tell you"
{{"turn":5,"original":"If I would know","correction":"If I knew","codes":["V:COND"],"reasoning":"Conditional 2: if + past simple, not if + would"}}

Turn 6: "I am understanding this lesson very well now"
{{"turn":6,"original":"am understanding","correction":"understand","codes":["V:ASPECT"],"reasoning":"Understand is a stative verb, no progressive"}}

Turn 7: "You like coffee or you prefer tea"
{{"turn":7,"original":"You like coffee","correction":"Do you like coffee","codes":["V:AUX"],"reasoning":"Missing do-support in question"}}

Turn 8: "If I would have known I would have told you"
{{"turn":8,"original":"If I would have known","correction":"If I had known","codes":["V:COND"],"reasoning":"Conditional 3: if + past perfect, not if + would have"}}

Turn 9: "He said me that he was coming to the party"
{{"turn":9,"original":"said me","correction":"told me","codes":["V:CHOICE"],"reasoning":"Say cannot take indirect object, use tell"}}

Turn 10: "I need to look in this problem more carefully"
{{"turn":10,"original":"look in","correction":"look into","codes":["V:PHRASAL"],"reasoning":"Wrong phrasal verb particle"}}

Turn 11: "I did a big mistake at work and got into trouble"
{{"turn":11,"original":"did a big mistake","correction":"made a big mistake","codes":["LEX:COLLOC"],"reasoning":"Collocation: make a mistake, not do a mistake"}}

Turn 12: "She is actually very busy with her new project"
CORRECT — "actually" used correctly here (means "in fact"). Not a false friend error. Return no error for this turn.

Turn 13: "It makes three years that I work in this company"
{{"turn":13,"original":"It makes three years","correction":"It has been three years","codes":["LEX:CALQUE"],"reasoning":"French calque: ça fait 3 ans → it has been 3 years"}}

Turn 14: "I very much like this restaurant near my place"
{{"turn":14,"original":"I very much like","correction":"I like very much","codes":["WO"],"reasoning":"Adverb phrase should follow the verb, not precede it"}}

Turn 15: "Where you go every Saturday morning for shopping"
{{"turn":15,"original":"Where you go","correction":"Where do you go","codes":["WO:QUEST"],"reasoning":"Questions need do-support: Where do you go"}}

Turn 16: "I need to return back home before dark tonight"
{{"turn":16,"original":"return back","correction":"return","codes":["REDUND"],"reasoning":"Return already means go back — back is redundant"}}

Turn 17: "I dont know that should I go to the meeting or not"
{{"turn":17,"original":"dont","correction":"don't","codes":["PUNCT:APOST"],"reasoning":"Missing apostrophe"}}
{{"turn":17,"original":"that should I go","correction":"if I should go","codes":["SENT:SUBORD"],"reasoning":"Embedded question: if + normal order, not that + inverted"}}

Turn 18: "She bought new furnitures for the living room"
{{"turn":18,"original":"furnitures","correction":"furniture","codes":["N:COUNT"],"reasoning":"Furniture is uncountable — no plural form"}}

Turn 19: "I did a big mistake and she does a lot of sport"
{{"turn":19,"original":"did a big mistake","correction":"made a big mistake","codes":["LEX:COLLOC"],"reasoning":"Collocation: make a mistake, not do"}}
{{"turn":19,"original":"does a lot of sport","correction":"plays a lot of sport","codes":["LEX:COLLOC"],"reasoning":"Collocation: play sport, not do"}}

Turn 20: "What time the movie starts at the cinema tonight"
{{"turn":20,"original":"What time the movie starts","correction":"What time does the movie start","codes":["WO:QUEST"],"reasoning":"Question needs do-support + base form"}}

Turn 21 (MULTI): "i have 25 years and i cant find a good appartment"
{{"turn":21,"original":"i","correction":"I","codes":["ORTH:CASE"],"reasoning":"Pronoun I"}}
{{"turn":21,"original":"I have 25 years","correction":"I am 25 years old","codes":["LEX:CALQUE"],"reasoning":"French j ai 25 ans calque"}}
{{"turn":21,"original":"cant","correction":"can't","codes":["PUNCT:APOST"],"reasoning":"Missing apostrophe"}}
{{"turn":21,"original":"appartment","correction":"apartment","codes":["SPELL:COGNATE"],"reasoning":"French appartement"}}

### Transcript:
{transcript}"""


class LLMError(BaseModel):
    turn: int | None = None
    original: str
    correction: str | None = None
    codes: list[str]
    reasoning: str | None = None


class LLMAnalysisResult(BaseModel):
    errors: list[LLMError]


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=10))
async def analyze_transcript(transcript: str) -> LLMAnalysisResult:
    """Monolithic: LLM finds AND classifies errors in one pass."""
    payload = {
        "model": ANALYSIS_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(transcript=transcript)},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
        "max_tokens": 4000,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(LITELLM_URL, json=payload)
        resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    result = LLMAnalysisResult(**parsed)

    # Filter invalid codes
    valid_errors = []
    for error in result.errors:
        valid_codes = [c for c in error.codes if c in TIER1_CATEGORIES]
        if valid_codes:
            error.codes = valid_codes
            valid_errors.append(error)

    return LLMAnalysisResult(errors=valid_errors)
