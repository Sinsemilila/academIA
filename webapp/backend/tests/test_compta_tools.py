"""S57 — Tests for AccountingDomain backend tools (Phase 1 Mode B).

Tests rules-first detection : lookup_pcg, verify_partie_double, verify_calcul_tva,
verify_compte_classe, lookup_studi_module.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure app/ on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.tools.compta_tools import (  # noqa: E402
    lookup_pcg_account,
    lookup_studi_module,
    verify_calcul_tva,
    verify_compte_classe,
    verify_partie_double,
)


# ── lookup_pcg_account ────────────────────────────────────────────


def test_lookup_pcg_known_compte():
    """Compte connu retourne libellé + classe."""
    r = lookup_pcg_account("401")
    assert r["found"] is True
    assert r["compte"] == "401"
    assert "Fournisseurs" in r["libelle"]
    assert r["classe"] == "4"


def test_lookup_pcg_normalise_input():
    """Input variations normalisées : '0401', '401 ', '401.0' → 401."""
    r1 = lookup_pcg_account("0401")
    r2 = lookup_pcg_account("401 ")
    r3 = lookup_pcg_account("401.0")
    assert r1["compte"] == "401"
    assert r2["compte"] == "401"
    assert r3["compte"] == "401"


def test_lookup_pcg_unknown_with_suggestions():
    """Compte inconnu avec préfixe → suggestions sous-comptes."""
    r = lookup_pcg_account("4456999")
    assert r["found"] is False
    # Doit proposer des comptes 4456*
    assert any(s.startswith("4456") for s in r["suggestions"])


def test_lookup_pcg_classe_inferred():
    """Classe inférée depuis premier chiffre."""
    r = lookup_pcg_account("607")
    assert r["classe"] == "6"
    assert "charges" in r["classe_libelle"].lower()


def test_lookup_pcg_tva_collectee():
    """44571 = TVA collectée."""
    r = lookup_pcg_account("44571")
    assert r["found"] is True
    assert "collectée" in r["libelle"].lower()


def test_lookup_pcg_tva_deductible():
    """44566 = TVA déductible sur autres biens et services."""
    r = lookup_pcg_account("44566")
    assert r["found"] is True
    assert "déductible" in r["libelle"].lower()


# ── verify_partie_double ──────────────────────────────────────────


def test_partie_double_balanced_simple():
    """Écriture simple équilibrée."""
    ecritures = [
        {"compte": "607", "libelle": "Achats marchandises", "debit": 100.0, "credit": 0.0},
        {"compte": "401", "libelle": "Fournisseur", "debit": 0.0, "credit": 100.0},
    ]
    r = verify_partie_double(ecritures)
    assert r["valid"] is True
    assert r["sum_debits"] == 100.0
    assert r["sum_credits"] == 100.0
    assert r["diff"] == 0.0
    assert "équilibrée" in r["detail"]


def test_partie_double_balanced_facture_tva():
    """Facture HT + TVA = TTC, équilibrée."""
    ecritures = [
        {"compte": "607", "debit": 100.0, "credit": 0.0, "libelle": "Achat HT"},
        {"compte": "44566", "debit": 20.0, "credit": 0.0, "libelle": "TVA déductible 20%"},
        {"compte": "401", "debit": 0.0, "credit": 120.0, "libelle": "Fournisseur TTC"},
    ]
    r = verify_partie_double(ecritures)
    assert r["valid"] is True
    assert r["sum_debits"] == 120.0
    assert r["sum_credits"] == 120.0


def test_partie_double_unbalanced():
    """Déséquilibre détecté + message clair."""
    ecritures = [
        {"compte": "607", "debit": 100.0, "credit": 0.0, "libelle": "Achat"},
        {"compte": "401", "debit": 0.0, "credit": 110.0, "libelle": "Fournisseur trop"},
    ]
    r = verify_partie_double(ecritures)
    assert r["valid"] is False
    assert r["diff"] == -10.0  # debits < credits
    assert "Différence" in r["detail"] or "déséquilibrée" in r["detail"]


def test_partie_double_empty():
    """Aucune écriture = invalid."""
    r = verify_partie_double([])
    assert r["valid"] is False
    assert r["n_lines"] == 0


def test_partie_double_tolerance_arrondi():
    """Tolérance flottant 0.01€."""
    ecritures = [
        {"compte": "607", "debit": 100.005, "credit": 0.0, "libelle": ""},
        {"compte": "401", "debit": 0.0, "credit": 100.005, "libelle": ""},
    ]
    r = verify_partie_double(ecritures)
    assert r["valid"] is True


def test_partie_double_silent_zero_format_mismatch_returns_invalid():
    """S59 — LLM sends {compte, montant, type} instead of canonical
    {compte, debit | credit}, both default 0 → must NOT silently return
    valid:true sum:0. Tool must explicit-error to guide LLM retry."""
    # Simulate dict with non-canonical keys (after extra='ignore' would have
    # stripped them, leaving debit=0+credit=0).
    ecritures_format_wobble = [
        {"compte": "401", "debit": 0.0, "credit": 0.0, "libelle": ""},
        {"compte": "607", "debit": 0.0, "credit": 0.0, "libelle": ""},
    ]
    r = verify_partie_double(ecritures_format_wobble)
    assert r["valid"] is False
    assert r["sum_debits"] == 0.0
    assert r["sum_credits"] == 0.0
    assert "Format payload incorrect" in r["detail"]
    assert "canonical" in r["detail"].lower()
    # Detail must show the canonical example to guide LLM retry
    assert "debit" in r["detail"]
    assert "credit" in r["detail"]


# ── verify_calcul_tva ──────────────────────────────────────────


def test_tva_calcul_correct_20():
    """Calcul TVA 20% correct."""
    r = verify_calcul_tva(100.0, 20.0, actual_tva=20.0, actual_ttc=120.0)
    assert r["valid"] is True
    assert r["expected_tva"] == 20.0
    assert r["expected_ttc"] == 120.0


def test_tva_calcul_correct_5_5():
    """Calcul TVA 5.5% correct (livres, alimentaire)."""
    r = verify_calcul_tva(100.0, 5.5, actual_tva=5.5, actual_ttc=105.5)
    assert r["valid"] is True


def test_tva_taux_invalide():
    """Taux non standard FR flagué."""
    r = verify_calcul_tva(100.0, 17.5)  # taux UK
    assert r["taux_valide"] is False
    assert "non standard" in r["detail"]


def test_tva_calcul_actual_incorrect():
    """Learner propose mauvais montant TVA → flagué."""
    r = verify_calcul_tva(100.0, 20.0, actual_tva=19.0)
    assert r["valid"] is False
    assert "incorrecte" in r["detail"]


def test_tva_no_actual_just_calcul():
    """Pas de actual fourni = juste calcul info."""
    r = verify_calcul_tva(250.0, 20.0)
    assert r["expected_tva"] == 50.0
    assert r["expected_ttc"] == 300.0


# ── verify_compte_classe ──────────────────────────────────────────


def test_compte_classe_correct():
    """607 dans classe 6 ✓."""
    r = verify_compte_classe("607", "6")
    assert r["valid"] is True


def test_compte_classe_incorrect():
    """401 dans classe 4 mais on attendait 6 → invalid + message clair."""
    r = verify_compte_classe("401", "6")
    assert r["valid"] is False
    assert "classe 4" in r["detail"]
    assert "classe 6" in r["detail"]


# ── lookup_studi_module ──────────────────────────────────────────


def test_studi_module_tva():
    """Question TVA → BC1.4."""
    r = lookup_studi_module("Comment calculer la TVA déductible ?")
    assert r["found"] is True
    assert "BC1.4" in r["module"]


def test_studi_module_paie():
    """Question paie → BC2."""
    r = lookup_studi_module("Comment lire un bulletin de salaire ?")
    assert r["found"] is True
    assert "BC2" in r["module"]


def test_studi_module_unknown():
    """Question hors scope → not found, propose dropdown."""
    r = lookup_studi_module("Quelle est la météo ?")
    assert r["found"] is False
    assert "dropdown" in r["detail"].lower()
