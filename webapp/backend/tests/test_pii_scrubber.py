"""
Refactor 2026-H2 Phase A5 — PII scrubber tests.

Run via :
    docker exec academie-api python -m pytest /app/tests/test_pii_scrubber.py -v
or :
    cd webapp/backend && PYTHONPATH=. python -m pytest tests/test_pii_scrubber.py -v
"""
from __future__ import annotations

import pytest

from app.security.pii_scrubber import scrub, scrub_payload_strings


@pytest.mark.parametrize(
    "raw, expected_sub, expected_count",
    [
        ("mon email c'est jean.dupont@example.com merci", "[EMAIL]", 1),
        ("contact a+b.c@sub.exemple.fr ou autre", "[EMAIL]", 1),
        ("Mail multiple a@x.io et b@y.com", "[EMAIL]", 2),
    ],
)
def test_scrub_email(raw, expected_sub, expected_count):
    out, hits = scrub(raw)
    assert expected_sub in out
    assert hits["email"] == expected_count
    assert "@" not in out  # belt-and-braces


@pytest.mark.parametrize(
    "raw, expected_count",
    [
        ("appelle 0612345678", 1),
        ("appelle 06 12 34 56 78", 1),
        ("tél : 01.23.45.67.89", 1),
        ("from france +33 6 12 34 56 78", 1),
        ("intl 0033612345678", 1),
        ("two phones 0612345678 et 0712345678", 2),
        ("no phone here, just 12345", 0),
    ],
)
def test_scrub_phone(raw, expected_count):
    out, hits = scrub(raw)
    assert hits["phone"] == expected_count
    if expected_count:
        assert "[PHONE]" in out


@pytest.mark.parametrize(
    "raw, expected_count",
    [
        ("mon iban FR76 3000 6000 0112 3456 7890 189", 1),
        ("DE89370400440532013000", 1),
        ("not an iban: ABCD1234", 0),
    ],
)
def test_scrub_iban(raw, expected_count):
    out, hits = scrub(raw)
    assert hits["iban"] == expected_count
    if expected_count:
        assert "[IBAN]" in out


def test_scrub_nir():
    raw = "mon NIR 1 84 12 75 114 273 36"
    out, hits = scrub(raw)
    assert hits["nir"] == 1
    assert "[NIR]" in out


@pytest.mark.parametrize(
    "raw, expected_card",
    [
        # Visa test number — Luhn-valid
        ("ma carte 4532015112830366 expire 12/27", True),
        # Mastercard test number — Luhn-valid
        ("5425233430109903", True),
        # 16 digits but Luhn-invalid → not scrubbed
        ("ref 1234567890123456 dossier", False),
        # Random 14-digit not luhn → not scrubbed
        ("commande 12345678901234", False),
    ],
)
def test_scrub_card_luhn(raw, expected_card):
    out, hits = scrub(raw)
    if expected_card:
        assert hits["card"] >= 1
        assert "[CARD]" in out
    else:
        assert hits["card"] == 0
        assert "[CARD]" not in out


def test_scrub_idempotent_on_empty_or_none():
    assert scrub("") == ("", {})
    assert scrub(None) == ("", {})


def test_scrub_multi_pii_in_one_message():
    raw = (
        "Bonjour, mon email est test@example.com, "
        "tél 0612345678, IBAN FR76 1234 5678 9012 3456 7890 123."
    )
    out, hits = scrub(raw)
    assert hits["email"] == 1
    assert hits["phone"] == 1
    assert hits["iban"] == 1
    assert "[EMAIL]" in out
    assert "[PHONE]" in out
    assert "[IBAN]" in out
    assert "test@example.com" not in out
    assert "0612345678" not in out


def test_scrub_preserves_pedagogical_text():
    """The scrubber must not damage normal language-learning content."""
    raw = "Hello, I learn French because it's beautiful."
    out, hits = scrub(raw)
    assert out == raw
    assert sum(hits.values()) == 0


def test_scrub_payload_strings_query_and_inputs():
    payload = {
        "query": "mon email c'est foo@bar.com",
        "inputs": {
            "learner_profile_summary": "élève niveau B1, motivé",
            "scaffolding_block": "appelle 06 12 34 56 78 si besoin",
        },
        "user": "user_42",
        "response_mode": "streaming",
    }
    hits = scrub_payload_strings(payload, fields=("query",))
    assert hits["email"] == 1
    assert hits["phone"] == 1
    assert "[EMAIL]" in payload["query"]
    assert "[PHONE]" in payload["inputs"]["scaffolding_block"]
    assert payload["user"] == "user_42"  # untouched
    assert payload["response_mode"] == "streaming"


def test_scrub_payload_strings_no_inputs_dict():
    payload = {"query": "no email"}
    hits = scrub_payload_strings(payload, fields=("query",))
    assert sum(hits.values()) == 0
    assert payload["query"] == "no email"
