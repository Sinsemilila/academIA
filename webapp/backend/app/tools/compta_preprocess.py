"""A1 ciblé S59 — pre-process Marie's query to fact-check via verify_partie_double.

Workaround for blocked P1.1 (Dify agent node + plugin daemon URL bug).
Backend extracts "Débit X N€ Crédit Y N€" patterns in user query, calls the
deterministic tool, prepends tool result to query as authoritative fact-check.

Covers ~80% of Marie cases that show an écriture for verification (cf
hallucination Q09 detected S59 auto-test).

Single tool focus : verify_partie_double. Other compta tools (lookup_pcg,
verify_calcul_tva) deferred until proper agent loop available (P1.1 unblocked
via Dify plugin daemon upgrade or full agent refactor).
"""
from __future__ import annotations
import re
from typing import Any

from app.tools.compta_tools import verify_partie_double

# Pattern 1 — sens before compte ("Débit 401 100€", "Crédit 607 : 100€",
# "D 401 100", "- Débit 401 : 100€" markdown bullet, etc.)
# - sens : Débit/Crédit/D/C (case-insensitive)
# - compte : 3-5 digits PCG number
# - montant : decimal with comma/period
# - flexible separators between compte and montant (space, colon, "de", "pour")
_ECRITURE_LINE_RE = re.compile(
    r"\b(D[ée]bit|Cr[ée]dit|D|C)\s*[: ]?\s*"
    r"(\d{3,5})\s*"
    r"(?:[: ]|de\s+|pour\s+)+\s*"
    r"(\d+(?:[.,]\d+)?)\s*€?",
    re.IGNORECASE,
)

# Pattern 2 (S59 P1.1) — compte before sens ("401 débit 100", "401 au crédit 100€",
# "607 doit 50", "401 en débit de 100"). Matches conversational French.
# Excludes ambiguous "a" (avoir) and bare montant — needs explicit débit/crédit/doit verb.
_ECRITURE_INVERSED_RE = re.compile(
    r"\b(\d{3,5})\s+(?:au\s+|en\s+)?"
    r"(d[ée]bit(?:e|é|er)?|cr[ée]dit(?:e|é|er)?|doit)"
    r"(?:\s+(?:de|pour|:))?\s+"
    r"(\d+(?:[.,]\d+)?)\s*€?",
    re.IGNORECASE,
)


def _classify_sens(verb: str) -> str:
    """Map verb token to canonical 'debit' or 'credit'."""
    v = verb.lower()
    if v.startswith("d"):  # débit, débite, débité, débiter, doit
        return "debit"
    return "credit"


def extract_ecritures(query: str) -> list[dict[str, Any]]:
    """Extract list of EcritureLine-shaped dicts from user query.

    Returns list of {compte, debit | credit, libelle} matching the
    EcritureLine TypedDict expected by verify_partie_double. Empty list if
    no pattern detected (requires ≥2 lines; one-line ecriture cannot be
    tested for équilibre).
    """
    lines: list[dict[str, Any]] = []
    seen_spans: list[tuple[int, int]] = []  # avoid double-extraction overlap

    def _push(span: tuple[int, int], compte: str, sens: str, montant: float) -> None:
        # Skip if span overlaps an already-extracted line (same query region
        # captured by both regexes)
        for s, e in seen_spans:
            if span[0] < e and span[1] > s:
                return
        seen_spans.append(span)
        line: dict[str, Any] = {"compte": compte, "libelle": ""}
        line[sens] = montant
        lines.append(line)

    # Pattern 1 — sens before compte
    for m in _ECRITURE_LINE_RE.finditer(query):
        sens = _classify_sens(m.group(1))
        compte = m.group(2)
        try:
            montant = float(m.group(3).replace(",", "."))
        except ValueError:
            continue
        if montant <= 0:
            continue
        _push(m.span(), compte, sens, montant)

    # Pattern 2 — compte before sens (conversational French)
    for m in _ECRITURE_INVERSED_RE.finditer(query):
        compte = m.group(1)
        sens = _classify_sens(m.group(2))
        try:
            montant = float(m.group(3).replace(",", "."))
        except ValueError:
            continue
        if montant <= 0:
            continue
        _push(m.span(), compte, sens, montant)

    return lines if len(lines) >= 2 else []


def fact_check_ecriture(query: str) -> str | None:
    """If query contains an ecriture, return a French fact-check block to
    prepend to the user query. Returns None if no ecriture detected.

    The block is formatted to be unambiguous for the LLM : explicit ✅/❌
    verdict + numeric justification. The LLM (with system prompt few-shots)
    will then scaffold on the *real* pedagogical issue (e.g. sens débit/crédit
    inversion vs équilibre confusion).
    """
    ecritures = extract_ecritures(query)
    if not ecritures:
        return None
    try:
        result = verify_partie_double(ecritures)
    except Exception:
        return None
    sd = result.get("sum_debits", 0)
    sc = result.get("sum_credits", 0)
    if result.get("valid"):
        verdict = f"✅ Équilibrée (somme débits = {sd:g} €, somme crédits = {sc:g} €, écart = 0 €)."
    else:
        ecart = sd - sc
        verdict = f"❌ Déséquilibrée (somme débits = {sd:g} €, somme crédits = {sc:g} €, écart = {ecart:+g} €)."
    block = (
        "[FACT-CHECK BACKEND — utilise comme vérité absolue]\n"
        f"Vérification équilibre partie double : {verdict}\n"
        "Si l'écriture est équilibrée mais que tu suspectes un autre problème "
        "(sens débit/crédit, classe de compte, sous-compte), utilise les scaffolds "
        "Lyster pour le faire découvrir à Marie — ne contredis JAMAIS le verdict "
        "ci-dessus sur l'équilibre.\n\n"
        "[QUESTION MARIE]\n"
    )
    return block


def maybe_enrich_query(query: str) -> str:
    """Prepend fact-check block if applicable; return query as-is otherwise.

    Idempotent (safe to call multiple times — won't double-prepend if block
    already present)."""
    if "[FACT-CHECK BACKEND" in query:
        return query
    block = fact_check_ecriture(query)
    if block is None:
        return query
    return block + query
