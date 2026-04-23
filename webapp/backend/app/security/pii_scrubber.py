"""
Refactor 2026-H2 Phase A5 — PII scrubber.

Removes the most sensitive personally identifiable information from text
*before* it leaves the backend toward LLM sub-processors (Dify → OpenAI / Groq).

Patterns covered (FR-first context) :
  * Email addresses                               → [EMAIL]
  * French phone numbers (mobile + fixe + intl)   → [PHONE]
  * IBAN (any country)                            → [IBAN]
  * NIR (French social security number)           → [NIR]
  * Credit/debit cards (Luhn-validated 13–19)     → [CARD]

The scrubber is intentionally conservative on false positives :
- emails matched on a greedy local part + at least one dot in domain.
- phones require ≥10 digits in a recognizable FR format (we do not scrub
  random number sequences).
- cards re-validated via Luhn checksum to avoid scrubbing arbitrary digit
  strings (long order numbers, exam IDs, etc.).

Design choice : run on every outbound LLM payload string. False negatives
are acceptable (this is defense in depth, not a sole control), false
positives are not (the LLM still needs readable input to teach languages).

Invocation :
    from app.security.pii_scrubber import scrub
    scrubbed_query, hits = scrub("mon email c'est jean@example.com")
    # → ("mon email c'est [EMAIL]", {"email": 1})
"""
from __future__ import annotations

import re
from typing import Iterable

EMAIL_RE = re.compile(
    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
)

# FR-first phone : +33 / 0033 / 0X followed by 9 digits, separators optional
PHONE_FR_RE = re.compile(
    r"(?:(?:\+|00)33[\s.\-]?|\b0)[1-9](?:[\s.\-]?\d{2}){4}\b",
)

IBAN_RE = re.compile(
    r"\b[A-Z]{2}\d{2}(?:[\s]?[A-Z0-9]{4}){2,7}(?:[\s]?[A-Z0-9]{1,4})\b",
)

# NIR FR : sex (1|2|7|8) + year (2) + month (01-12 or 20|30|3X|4X) + dept (2 chars incl 2A/2B)
# + commune (3) + serial (3) + control key (2)
NIR_RE = re.compile(
    r"\b[12]\s?\d{2}\s?(?:0[1-9]|1[0-2]|2\d|3\d|4\d|5\d)\s?(?:\d{2}|2A|2B)\s?\d{3}\s?\d{3}\s?\d{2}\b",
)

# Card pre-filter : 13-19 digits, optional separators every 4. Luhn validated below.
CARD_RE = re.compile(
    r"\b(?:\d[ \-]?){13,19}\b",
)


def _luhn_valid(digits: str) -> bool:
    """Luhn algorithm — returns True for valid card-style number."""
    s = [int(d) for d in digits if d.isdigit()]
    if not 13 <= len(s) <= 19:
        return False
    checksum = 0
    for i, d in enumerate(reversed(s)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def _replace_card(match: re.Match) -> str:
    raw = match.group(0)
    digits_only = re.sub(r"\D", "", raw)
    if _luhn_valid(digits_only):
        return "[CARD]"
    return raw


def scrub(text: str | None) -> tuple[str, dict[str, int]]:
    """Return (scrubbed_text, hits_per_pattern). Idempotent on None / empty."""
    if not text:
        return text or "", {}
    hits = {"email": 0, "phone": 0, "iban": 0, "nir": 0, "card": 0}

    out = text
    out, n = EMAIL_RE.subn("[EMAIL]", out)
    hits["email"] = n
    out, n = PHONE_FR_RE.subn("[PHONE]", out)
    hits["phone"] = n
    out, n = IBAN_RE.subn("[IBAN]", out)
    hits["iban"] = n
    out, n = NIR_RE.subn("[NIR]", out)
    hits["nir"] = n

    # Cards : substitute via callback (Luhn check), count by diffing
    before_cards = out
    out = CARD_RE.sub(_replace_card, out)
    hits["card"] = before_cards.count(" ") - out.count(" ")  # rough heuristic
    if "[CARD]" in out:
        hits["card"] = out.count("[CARD]")
    else:
        hits["card"] = 0

    return out, hits


def scrub_payload_strings(payload: dict, fields: Iterable[str] = ("query",)) -> dict[str, int]:
    """Scrub specific top-level string fields of a dict in place + nested
    `inputs` dict values that are strings. Returns aggregate hit counts.

    Used by chat_router.py before POSTing to Dify.
    """
    aggregate = {"email": 0, "phone": 0, "iban": 0, "nir": 0, "card": 0}

    for field in fields:
        v = payload.get(field)
        if isinstance(v, str):
            scrubbed, hits = scrub(v)
            payload[field] = scrubbed
            for k, n in hits.items():
                aggregate[k] += n

    inputs = payload.get("inputs")
    if isinstance(inputs, dict):
        for k, v in list(inputs.items()):
            if isinstance(v, str):
                scrubbed, hits = scrub(v)
                inputs[k] = scrubbed
                for kk, n in hits.items():
                    aggregate[kk] += n

    return aggregate
