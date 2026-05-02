"""Unit tests for compta query pre-processing (A1 ciblé S59)."""
from app.tools.compta_preprocess import (
    extract_ecritures,
    fact_check_ecriture,
    maybe_enrich_query,
)


def test_extract_ecritures_basic_two_lines():
    q = "Vérifie ça : Débit 401 100€, Crédit 607 100€"
    out = extract_ecritures(q)
    assert len(out) == 2
    debits = [e for e in out if "debit" in e]
    credits = [e for e in out if "credit" in e]
    assert len(debits) == 1 and debits[0]["compte"] == "401" and debits[0]["debit"] == 100.0
    assert len(credits) == 1 and credits[0]["compte"] == "607" and credits[0]["credit"] == 100.0


def test_extract_ecritures_with_decimals_and_comma():
    q = "Débit 6061 99,50 € Crédit 401 99,50€"
    out = extract_ecritures(q)
    assert any(e.get("debit") == 99.5 for e in out)
    assert any(e.get("credit") == 99.5 for e in out)


def test_extract_ecritures_short_form_d_c():
    q = "D 401 500 C 607 500"
    out = extract_ecritures(q)
    assert len(out) == 2


def test_extract_ecritures_single_line_returns_empty():
    """Cannot test équilibre from a single line."""
    assert extract_ecritures("Débit 401 100€") == []


def test_extract_ecritures_no_pattern_returns_empty():
    assert extract_ecritures("C'est quoi un amortissement dégressif ?") == []
    assert extract_ecritures("Différence entre 401 et 411 ?") == []


def test_fact_check_balanced_ecriture():
    q = "Vérifie : Débit 401 100€, Crédit 607 100€"
    block = fact_check_ecriture(q)
    assert block is not None
    assert "✅ Équilibrée" in block
    assert "100 €" in block
    assert "ne contredis JAMAIS" in block


def test_fact_check_unbalanced_ecriture():
    q = "Vérifie : Débit 401 100€, Crédit 607 50€"
    block = fact_check_ecriture(q)
    assert block is not None
    assert "❌ Déséquilibrée" in block
    assert "écart" in block


def test_fact_check_no_ecriture_returns_none():
    assert fact_check_ecriture("C'est quoi la TVA ?") is None
    assert fact_check_ecriture("401 c'est quel compte ?") is None


def test_maybe_enrich_query_idempotent():
    q = "Débit 401 100€ Crédit 607 100€"
    enriched = maybe_enrich_query(q)
    assert "[FACT-CHECK BACKEND" in enriched
    assert "[QUESTION MARIE]" in enriched
    assert q in enriched
    # Re-call must not double-prepend
    twice = maybe_enrich_query(enriched)
    assert twice == enriched


def test_maybe_enrich_query_passthrough():
    q = "C'est quoi un amortissement dégressif ?"
    assert maybe_enrich_query(q) == q


def test_extract_ecritures_three_lines():
    q = "Débit 6061 100€ Débit 44566 20€ Crédit 401 120€"
    out = extract_ecritures(q)
    assert len(out) == 3


def test_fact_check_three_lines_balanced():
    """EX1 facture EDF pattern from system prompt."""
    q = "Débit 6061 100€ Débit 44566 20€ Crédit 401 120€"
    block = fact_check_ecriture(q)
    assert block is not None
    assert "✅ Équilibrée" in block
    assert "120 €" in block


# ── S59 P1.1 — extended regex patterns ─────────────────────────────


def test_extract_ecritures_markdown_bullet():
    """Markdown list bullets : '- Débit 401 : 100€'."""
    q = "- Débit 401 : 100€\n- Crédit 607 : 100€"
    out = extract_ecritures(q)
    assert len(out) == 2


def test_extract_ecritures_colon_separator():
    """Colon between compte and montant : 'Débit 401: 100'."""
    q = "Débit 401: 100, Crédit 607: 100"
    out = extract_ecritures(q)
    assert len(out) == 2


def test_extract_ecritures_de_pour_separator():
    """Verbose separators 'de'/'pour' : 'Débit 401 de 100€'."""
    q = "Débit 401 de 100€, Crédit 607 pour 100€"
    out = extract_ecritures(q)
    assert len(out) == 2


def test_extract_ecritures_inversed_compte_first():
    """Conversational French: compte before sens. '401 débit 100'."""
    q = "401 débit 100, 607 crédit 100"
    out = extract_ecritures(q)
    assert len(out) == 2


def test_extract_ecritures_au_sens():
    """'401 au débit 100€'."""
    q = "401 au débit 100€, 607 au crédit 100€"
    out = extract_ecritures(q)
    assert len(out) == 2


def test_extract_ecritures_doit_verb():
    """'401 doit 100' — verbe doit (débit-side)."""
    q = "401 doit 100, 607 crédit 100"
    out = extract_ecritures(q)
    assert len(out) == 2
    debit_lines = [e for e in out if "debit" in e]
    assert len(debit_lines) == 1
    assert debit_lines[0]["compte"] == "401"


def test_extract_ecritures_inversed_verbal():
    """Conjugated verbs : 'débite', 'crédite'."""
    q = "401 débite 100€, 607 crédite 100€"
    out = extract_ecritures(q)
    assert len(out) == 2


def test_extract_ecritures_ambiguous_a_avoir_skipped():
    """'401 a 100' (avoir) intentionally NOT matched (ambiguous)."""
    q = "401 a 100, 607 crédit 100"
    out = extract_ecritures(q)
    # Only the explicit 'crédit' line caught — 1 line < 2 → empty
    assert len(out) == 0


def test_extract_ecritures_no_double_extraction():
    """Same span captured by both patterns must yield 1 line, not 2."""
    # Pattern 1 matches "Débit 401 100€"
    # Pattern 2 doesn't apply (no sens after compte in this exact span)
    q = "Débit 401 100€, Crédit 607 100€"
    out = extract_ecritures(q)
    assert len(out) == 2  # exactly 2 lines, no duplicates
