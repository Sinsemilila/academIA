"""S57 — Tests for compta_router internal endpoints.

Tests endpoint validation + delegation to tools (déjà testées dans test_compta_tools).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

# Lightweight FastAPI app pour tester compta_router en isolation
from fastapi import FastAPI  # noqa: E402

from app.routers import compta_router  # noqa: E402


_app = FastAPI()
_app.include_router(compta_router.router)
client = TestClient(_app)


# ── lookup_pcg ──────────────────────────────────────────


def test_endpoint_lookup_pcg_known():
    r = client.post("/internal/compta/tools/lookup_pcg", json={"num": "401"})
    assert r.status_code == 200
    assert r.json()["found"] is True
    assert "Fournisseurs" in r.json()["libelle"]


def test_endpoint_lookup_pcg_unknown():
    r = client.post("/internal/compta/tools/lookup_pcg", json={"num": "9999"})
    assert r.status_code == 200
    assert r.json()["found"] is False


def test_endpoint_lookup_pcg_extra_field_rejected():
    """extra='forbid' refuse fields inattendus."""
    r = client.post("/internal/compta/tools/lookup_pcg", json={"num": "401", "extra": "x"})
    assert r.status_code == 422


# ── verify_partie_double ──────────────────────────────────


def test_endpoint_partie_double_balanced():
    r = client.post(
        "/internal/compta/tools/verify_partie_double",
        json={
            "ecritures": [
                {"compte": "607", "libelle": "Achats", "debit": 100.0, "credit": 0.0},
                {"compte": "401", "libelle": "Fournisseur", "debit": 0.0, "credit": 100.0},
            ]
        },
    )
    assert r.status_code == 200
    assert r.json()["valid"] is True
    assert r.json()["sum_debits"] == 100.0


def test_endpoint_partie_double_unbalanced():
    r = client.post(
        "/internal/compta/tools/verify_partie_double",
        json={
            "ecritures": [
                {"compte": "607", "debit": 100.0, "credit": 0.0},
                {"compte": "401", "debit": 0.0, "credit": 90.0},
            ]
        },
    )
    assert r.status_code == 200
    assert r.json()["valid"] is False


def test_endpoint_partie_double_format_wobble_rejected_422():
    """S59 — LLM payload format mismatch ({montant, type} instead of canonical
    {debit | credit}) must be rejected by Pydantic with 422 (extra='forbid' +
    model_validator). Previously silently passed via extra='ignore' →
    valid:true sum:0 false-positive."""
    r = client.post(
        "/internal/compta/tools/verify_partie_double",
        json={
            "ecritures": [
                {"compte": "401", "montant": 100, "type": "débit"},
                {"compte": "607", "montant": 100, "type": "crédit"},
            ]
        },
    )
    assert r.status_code == 422
    body = r.json()
    # FastAPI 422 wraps Pydantic errors in {"detail": [...]}
    detail_str = str(body)
    assert "extra" in detail_str.lower() or "forbid" in detail_str.lower() or "montant" in detail_str.lower()


def test_endpoint_partie_double_both_zero_rejected_422():
    """Each line must have debit > 0 OR credit > 0, not both at 0."""
    r = client.post(
        "/internal/compta/tools/verify_partie_double",
        json={
            "ecritures": [
                {"compte": "401", "debit": 0, "credit": 0},
                {"compte": "607", "debit": 100, "credit": 0},
            ]
        },
    )
    assert r.status_code == 422


def test_endpoint_partie_double_both_positive_rejected_422():
    """Each line must have debit XOR credit, not both > 0."""
    r = client.post(
        "/internal/compta/tools/verify_partie_double",
        json={
            "ecritures": [
                {"compte": "401", "debit": 50, "credit": 50},
                {"compte": "607", "debit": 100, "credit": 0},
            ]
        },
    )
    assert r.status_code == 422


# ── verify_calcul_tva ──────────────────────────────────


def test_endpoint_tva_correct():
    r = client.post(
        "/internal/compta/tools/verify_calcul_tva",
        json={"montant_ht": 100.0, "taux": 20.0, "actual_tva": 20.0, "actual_ttc": 120.0},
    )
    assert r.status_code == 200
    assert r.json()["valid"] is True


def test_endpoint_tva_just_calcul():
    r = client.post(
        "/internal/compta/tools/verify_calcul_tva",
        json={"montant_ht": 250.0, "taux": 20.0},
    )
    assert r.status_code == 200
    assert r.json()["expected_tva"] == 50.0
    assert r.json()["expected_ttc"] == 300.0


def test_endpoint_tva_negative_montant_rejected():
    r = client.post(
        "/internal/compta/tools/verify_calcul_tva",
        json={"montant_ht": -10.0, "taux": 20.0},
    )
    assert r.status_code == 422  # ge=0 validation


# ── verify_compte_classe ──────────────────────────────


def test_endpoint_compte_classe_correct():
    r = client.post(
        "/internal/compta/tools/verify_compte_classe",
        json={"num": "607", "expected_classe": "6"},
    )
    assert r.status_code == 200
    assert r.json()["valid"] is True


# ── lookup_studi_module ──────────────────────────────


def test_endpoint_studi_module_tva():
    r = client.post(
        "/internal/compta/tools/lookup_studi_module",
        json={"query": "calcul TVA déductible"},
    )
    assert r.status_code == 200
    assert r.json()["found"] is True


def test_endpoint_studi_module_too_long_rejected():
    r = client.post(
        "/internal/compta/tools/lookup_studi_module",
        json={"query": "x" * 600},
    )
    assert r.status_code == 422  # max_length=500


# ── _openapi_summary helper ──────────────────────────


def test_openapi_summary():
    r = client.get("/internal/compta/tools/_openapi_summary")
    assert r.status_code == 200
    body = r.json()
    assert "base_url" in body
    assert len(body["tools"]) == 5
