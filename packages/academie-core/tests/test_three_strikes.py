"""Unit tests for three_strikes detection + micro-lesson block rendering.

The SQL path is exercised via a stub `conn` object (no live Postgres
dependency) — keeps unit tests hermetic. The E2E test in
`scripts/sprint6/10_e2e_micro_lesson_test.py` covers the real DB.
"""
from __future__ import annotations

import asyncio

import pytest

from academie_core.pedagogy.three_strikes import (
    cefr_band,
    detect_three_strikes_family,
)
from academie_core.pedagogy.teacher_prompt import build_micro_lesson_block


# ── cefr_band mapping ─────────────────────────────────────────────────

@pytest.mark.parametrize("level,expected", [
    ("A1", "A1"), ("A1+", "A1"),
    ("A2", "A2"), ("A2+", "A2"),
    ("B1", "B1"), ("B1+", "B1"), ("B2", "B1"), ("C1", "B1"), ("C2", "B1"),
    ("", "B1"), (None, "B1"),
])
def test_cefr_band_mapping(level, expected):
    assert cefr_band(level) == expected


# ── Stub conn for detect_three_strikes_family ────────────────────────

class _StubConn:
    """Minimal asyncpg.Connection stub — fetch returns canned rows, fetchval
    returns canned value. Accepts any SQL + args."""
    def __init__(self, fetch_rows=None, fetchval_result=None):
        self._fetch_rows = fetch_rows or []
        self._fetchval_result = fetchval_result

    async def fetch(self, sql, *args):
        # Mimic asyncpg Record access via __getitem__
        return [{"error_code": code} for code in self._fetch_rows]

    async def fetchval(self, sql, *args):
        return self._fetchval_result


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Detection ─────────────────────────────────────────────────────────

def test_detect_no_errors_returns_none():
    conn = _StubConn(fetch_rows=[])
    result = _run(detect_three_strikes_family(conn, eleve_id=1, domain="en"))
    assert result is None


def test_detect_fewer_than_threshold_returns_none():
    conn = _StubConn(fetch_rows=["V:TENSE", "V:TENSE"])  # only 2
    result = _run(detect_three_strikes_family(conn, eleve_id=1, domain="en"))
    assert result is None


def test_detect_three_same_family_returns_family():
    conn = _StubConn(fetch_rows=["V:TENSE", "V:SVA", "V:FORM"])
    # All three map to 'verb_tense' family
    result = _run(detect_three_strikes_family(conn, eleve_id=1, domain="en"))
    assert result == "verb_tense"


def test_detect_mixed_families_returns_none():
    conn = _StubConn(fetch_rows=["V:TENSE", "N:COUNT", "V:FORM"])
    result = _run(detect_three_strikes_family(conn, eleve_id=1, domain="en"))
    assert result is None


def test_detect_dedup_suppresses_recent_injection():
    conn = _StubConn(
        fetch_rows=["V:TENSE", "V:TENSE", "V:TENSE"],
        fetchval_result=1,  # simulate a recent log row
    )
    result = _run(detect_three_strikes_family(conn, eleve_id=1, domain="en"))
    assert result is None


def test_detect_unknown_code_returns_none():
    conn = _StubConn(fetch_rows=["ZZZ:UNKNOWN", "ZZZ:UNKNOWN", "ZZZ:UNKNOWN"])
    result = _run(detect_three_strikes_family(conn, eleve_id=1, domain="en"))
    assert result is None


def test_detect_only_looks_at_threshold_window():
    # First 3 rows share verb_tense ; later rows are noise and should be ignored
    conn = _StubConn(fetch_rows=["V:TENSE", "V:SVA", "V:FORM", "N:COUNT", "PREP"])
    result = _run(detect_three_strikes_family(conn, eleve_id=1, domain="en"))
    assert result == "verb_tense"


# ── build_micro_lesson_block ──────────────────────────────────────────

def test_block_empty_when_no_family():
    assert build_micro_lesson_block(None, "A1", "en") == ""
    assert build_micro_lesson_block("", "A1", "en") == ""


def test_block_empty_for_unknown_family():
    assert build_micro_lesson_block("totally_made_up", "B1", "en") == ""


def test_block_renders_a1_example_only_no_metalinguistic_terms_en():
    block = build_micro_lesson_block("verb_tense", "A1", "en")
    assert block != ""
    # A1 variant must NOT contain full metalinguistic jargon
    body = block.lower()
    assert "past simple" not in body  # term reserved for B1+
    assert "auxiliary" not in body
    assert "past simple marks" not in body
    # But MUST contain a concrete example
    assert "went" in body


def test_block_renders_b1_full_metalinguistic_en():
    block = build_micro_lesson_block("verb_tense", "B1", "en")
    assert "past simple" in block.lower()
    assert "irregular verbs" in block.lower()


def test_block_falls_back_to_b1_for_c2():
    # cefr_band collapses C1/C2 into B1 bucket
    block_c2 = build_micro_lesson_block("verb_tense", "C2", "en")
    block_b1 = build_micro_lesson_block("verb_tense", "B1", "en")
    assert block_c2 == block_b1


def test_block_spanish_ser_estar_a1_no_metalanguage():
    # ES-specific family emitted by rules_es
    block = build_micro_lesson_block("V:SER_ESTAR", "A1", "es")
    assert block != ""
    assert "ser" in block.lower()
    assert "estar" in block.lower()
    # A1 ES also avoids technical terms (PCIC A1 rule)
    assert "propiedades inherentes" not in block.lower()
    assert "clasificatorias" not in block.lower()


def test_block_contains_marker_fences():
    block = build_micro_lesson_block("verb_tense", "B1", "en")
    assert "=== MICRO-LEÇON CIBLÉE" in block
    assert "=== END MICRO-LEÇON ===" in block


def test_block_contains_directive_integrate_once():
    # The tutor directive must tell the LLM to integrate ONCE naturally
    block = build_micro_lesson_block("verb_tense", "B1", "en")
    assert "UNE fois" in block or "une fois" in block.lower()
