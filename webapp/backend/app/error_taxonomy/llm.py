"""
AcademIA Error Taxonomy — LLM layers
Step 1: Correction-only (Groq Llama 3.3 70B)
Step 4: Fallback classification for ambiguous spans
"""

import json
import logging
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger("academie-api.error-taxonomy")

LITELLM_URL = "http://litellm-proxy:4000/v1/chat/completions"
ANALYSIS_MODEL = "groq-standard"

# ═══════════════════════════════════════════════════════════
# STEP 1 — Correction-only prompt
# The LLM does what it's good at: correcting English.
# No classification, no JSON structure, no taxonomy.
# ═══════════════════════════════════════════════════════════

CORRECTION_SYSTEM = """You correct a French speaker's English. Fix ALL errors: grammar, spelling, capitalization, punctuation, word choice, word order. Minimal changes only. Output: TURN N: corrected text. One line per message. No explanations.
Key French errors: have 25 years→am 25, since 5 years→for 5 years, depend of→on, confort→comfort, have been+last summer→went, dont→don't, i→I, aswell→as well."""

CORRECTION_USER_TEMPLATE = """Correct each USER message:

{transcript}"""


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=10))
async def get_corrections(transcript: str) -> dict[int, str]:
    """
    Step 1: Ask LLM to correct the text. Returns {turn_number: corrected_text}.
    """
    payload = {
        "model": ANALYSIS_MODEL,
        "messages": [
            {"role": "system", "content": CORRECTION_SYSTEM},
            {"role": "user", "content": CORRECTION_USER_TEMPLATE.format(transcript=transcript)},
        ],
        "temperature": 0.1,
        "max_tokens": 4000,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(LITELLM_URL, json=payload)
        resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"]
    return _parse_corrections(content)


def _parse_corrections(text: str) -> dict[int, str]:
    """Parse 'TURN N: corrected text' lines into a dict."""
    corrections = {}
    for line in text.strip().split("\n"):
        line = line.strip()
        if line.upper().startswith("TURN "):
            try:
                rest = line[5:]  # after "TURN "
                colon_idx = rest.index(":")
                turn_num = int(rest[:colon_idx].strip())
                corrected = rest[colon_idx + 1:].strip()
                if corrected:
                    corrections[turn_num] = corrected
            except (ValueError, IndexError):
                continue
    return corrections


# ═══════════════════════════════════════════════════════════
# STEP 4 — Fallback classification for ambiguous spans
# Called ONLY for edit spans that rules couldn't classify.
# Simple, focused prompt — one span at a time.
# ═══════════════════════════════════════════════════════════

CLASSIFY_SYSTEM = """You classify English learner errors into categories.
The learner's native language is French.
You receive: the wrong text, the correct text, and the sentence context.
Reply with ONLY the error code from this list:

V:TENSE — wrong verb tense (e.g. present perfect instead of past simple)
V:SVA — subject-verb agreement (e.g. "she have")
V:FORM — wrong verb form: gerund/infinitive/participle (e.g. "enjoy to swim")
N:NUM — singular/plural or countability (e.g. "informations")
ART — article error: a/the/zero (e.g. "the life is beautiful")
PREP — wrong preposition, NOT French transfer (e.g. "arrive at home")
PREP:CALQUE — preposition calqued from French (e.g. "depend of" from "dépendre de")
WO — word order (e.g. "speaks very well English")
LEX:CHOICE — wrong word or French calque expression (e.g. "I have 25 years")
OTHER — does not fit any category above

Reply with ONLY the code. Nothing else."""

CLASSIFY_USER_TEMPLATE = """Wrong: "{original}"
Correct: "{corrected}"
Context: "{context}"

Error code:"""


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
async def classify_span(original: str, corrected: str, context: str) -> str | None:
    """
    Step 4 (single): Classify one ambiguous edit span. Returns error code or None.
    """
    payload = {
        "model": ANALYSIS_MODEL,
        "messages": [
            {"role": "system", "content": CLASSIFY_SYSTEM},
            {"role": "user", "content": CLASSIFY_USER_TEMPLATE.format(
                original=original, corrected=corrected, context=context
            )},
        ],
        "temperature": 0.0,
        "max_tokens": 20,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(LITELLM_URL, json=payload)
        resp.raise_for_status()

    code = resp.json()["choices"][0]["message"]["content"].strip()
    code = code.split("\n")[0].split(" ")[0].strip()
    return code if code != "OTHER" else None


BATCH_CLASSIFY_SYSTEM = """You classify English learner errors into categories.
The learner's native language is French.
For each numbered edit, reply with ONLY the error code.

Codes:
V:TENSE — wrong verb tense
V:SVA — subject-verb agreement (she have→has)
V:FORM — gerund/infinitive/participle (enjoy to swim→swimming)
N:NUM — singular/plural or countability (informations→information)
ART — article error (the life→life, I bought car→a car)
PREP — wrong preposition (NOT French transfer)
PREP:CALQUE — French preposition calque (depend of→on, interested by→in)
WO — word order (speaks well English→English well)
LEX:CHOICE — wrong word or French calque (I have 25 years→I am 25)
SPELL — misspelling
OTHER — none of the above

Reply with one line per edit: just the number and code.
Example output:
1. V:TENSE
2. LEX:CHOICE
3. OTHER"""


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
async def classify_spans_batch(spans: list[tuple[str, str, str]]) -> list[str | None]:
    """
    Step 4 (batch): Classify multiple spans in one LLM call.
    Input: list of (original, corrected, context) tuples.
    Returns: list of error codes (or None for unclassifiable).
    """
    if not spans:
        return []

    lines = []
    for i, (orig, corr, ctx) in enumerate(spans, 1):
        lines.append(f'{i}. Wrong: "{orig}" → Correct: "{corr}" (in: "{ctx[:80]}")')

    payload = {
        "model": ANALYSIS_MODEL,
        "messages": [
            {"role": "system", "content": BATCH_CLASSIFY_SYSTEM},
            {"role": "user", "content": "\n".join(lines)},
        ],
        "temperature": 0.0,
        "max_tokens": 200,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(LITELLM_URL, json=payload)
        resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"].strip()

    # Parse "1. V:TENSE\n2. LEX:CHOICE\n..." into a list
    results: list[str | None] = [None] * len(spans)
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Match "1. CODE" or "1: CODE" or just "1 CODE"
        import re
        m = re.match(r"(\d+)[.\s:]+(\S+)", line)
        if m:
            idx = int(m.group(1)) - 1
            code = m.group(2).strip().rstrip(".")
            if 0 <= idx < len(spans):
                results[idx] = code if code != "OTHER" else None

    return results
