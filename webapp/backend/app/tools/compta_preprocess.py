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

# Detect lines like "Débit 401 100€", "Crédit 607 100€", "D 401 100", "C 607 100€"
# - sens : Débit/Crédit/D/C (case-insensitive)
# - compte : 3-5 digits PCG number
# - montant : decimal (with optional comma/period as separator)
# - euro symbol : optional
_ECRITURE_LINE_RE = re.compile(
    r"\b(D[ée]bit|Cr[ée]dit|D|C)\s*[: ]?\s*(\d{3,5})\s+(\d+(?:[.,]\d+)?)\s*€?",
    re.IGNORECASE,
)


def extract_ecritures(query: str) -> list[dict[str, Any]]:
    """Extract list of EcritureLine-shaped dicts from user query.

    Returns list of {compte, debit | credit, libelle} matching the
    EcritureLine TypedDict expected by verify_partie_double. Empty list if
    no pattern detected (requires ≥2 lines; one-line ecriture cannot be
    tested for équilibre).
    """
    lines = []
    for m in _ECRITURE_LINE_RE.finditer(query):
        sens_raw = m.group(1).lower()
        sens = "debit" if sens_raw.startswith("d") else "credit"
        compte = m.group(2)
        montant_raw = m.group(3).replace(",", ".")
        try:
            montant = float(montant_raw)
        except ValueError:
            continue
        if montant <= 0:
            continue
        line: dict[str, Any] = {"compte": compte, "libelle": ""}
        line[sens] = montant
        lines.append(line)
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
