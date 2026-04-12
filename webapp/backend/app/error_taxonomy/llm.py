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
# groq-standard (Llama 3.3 70B) — best quality for classification
# 2 API keys configured in LiteLLM = double quota
ANALYSIS_MODEL = "groq-standard"

SYSTEM_PROMPT = """You analyze French speakers learning English. Identify EVERY error made by the USER. Do NOT analyze TEACHER messages.

═══ ANALYSIS METHOD ═══

For EACH user message, perform a 3-PASS SCAN:

PASS 1 — SURFACE: Is 'i' lowercase? Proper nouns lowercase? Missing apostrophes (dont→don't, cant→can't, its→it's, theyre→they're, shes→she's, whos→who's)? Joined words (aswell, alot)? Misspellings? French spelling (confort→comfort)?

PASS 2 — GRAMMAR: Subject-verb agreement (she have→has)? Wrong tense (present perfect + yesterday/ago/last = use past simple)? Wrong verb form (enjoy to swim→swimming)? Singular/plural (informations→information)? Articles? Prepositions? French preposition calque (depend of→on)? Word order?

PASS 3 — LEXICAL: Wrong word? French calque expression (I have 25 years→I am 25)?

CRITICAL: A message often has 3-5+ errors. Report ALL. Do not stop after the obvious ones.

Output ONLY valid JSON. No other text."""

USER_PROMPT_TEMPLATE = """Classify errors using ONLY these 14 codes:

V:TENSE — wrong tense (have been + last summer → went)
V:SVA — subject-verb agreement (she have → has)
V:FORM — gerund/infinitive/participle (enjoy to swim → swimming)
N:NUM — singular/plural/countability (informations → information)
ART — article error (the life → life)
PREP — wrong preposition, NOT French (arrive to → in)
PREP:CALQUE — French preposition calque (depend of → on, interested by → in, since 5 years → for)
WO — word order (speaks well English → English well)
ORTH:CASE — capitalization (i → I, paris → Paris)
ORTH:SPACE — spacing (aswell → as well)
SPELL — misspelling, NOT French (definately → definitely)
SPELL:COGNATE — French spelling (confort → comfort, appartment → apartment, gouvernment → government)
PUNCT:APOST — missing apostrophe (dont → don't, cant → can't, its=it is → it's)
LEX:CHOICE — wrong word or French calque (I have 25 years → I am 25, say me → tell me)

{{"errors": [{{"turn": N, "original": "quote", "correction": "fix", "codes": ["CODE"], "reasoning": "why"}}]}}

If no errors: {{"errors": []}}

RULES:
- One entry per distinct error
- A turn can have multiple errors → multiple entries
- Contractions without apostrophes = ALWAYS PUNCT:APOST
- French spelling (confort, adresse, gouvernment) = ALWAYS SPELL:COGNATE not SPELL
- French preposition (depend of, interested by) = ALWAYS PREP:CALQUE not PREP

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

Turn 4 (MULTI-ERROR): "i have 25 years and i cant find a good appartment"
{{"turn":4,"original":"i","correction":"I","codes":["ORTH:CASE"],"reasoning":"Pronoun I"}}
{{"turn":4,"original":"I have 25 years","correction":"I am 25 years old","codes":["LEX:CHOICE"],"reasoning":"French j ai 25 ans calque"}}
{{"turn":4,"original":"cant","correction":"can't","codes":["PUNCT:APOST"],"reasoning":"Missing apostrophe"}}
{{"turn":4,"original":"appartment","correction":"apartment","codes":["SPELL:COGNATE"],"reasoning":"French appartement"}}

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
