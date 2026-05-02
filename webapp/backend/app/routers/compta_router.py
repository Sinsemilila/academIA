"""S57 — Internal-only endpoints for Maître Comptable backend tools.

Pattern same as internal_router : exposed only on docker-internal network
(academie-net-bridge), no JWT guard. Dify chatflow worker calls these via
Custom Tools (HTTP POST → backend) for deterministic compta lookups +
verifications.

Endpoints (all POST, JSON body, returns dict) :
- /internal/compta/tools/lookup_pcg
- /internal/compta/tools/verify_partie_double
- /internal/compta/tools/verify_calcul_tva
- /internal/compta/tools/verify_compte_classe
- /internal/compta/tools/lookup_studi_module

Architecture cohérente ADR-017 D3 (rules-first 80% / LLM 20%).
"""
from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..tools.compta_tools import (
    lookup_pcg_account,
    lookup_studi_module,
    verify_calcul_tva,
    verify_compte_classe,
    verify_partie_double,
)

router = APIRouter(prefix="/internal/compta/tools", tags=["compta-internal"])
_log = logging.getLogger("compta.tools")


# ── Pydantic input models (Dify Custom Tool sends JSON) ───────────


class LookupPCGRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    num: str = Field(..., max_length=20, description="Numéro de compte PCG (ex: '401', '4456')")


class EcritureLineModel(BaseModel):
    """Une ligne d'écriture comptable — format canonical strict.

    S59 — `extra="forbid"` to reject LLM payload wobble like
    {compte, montant, type} or {compte, amount, sens} that previously
    silently passed (defaulting debit/credit to 0 → false-positive
    'équilibrée 0=0'). Forced rejection → 422 → LLM retries with canonical.
    """
    model_config = ConfigDict(extra="forbid")
    compte: str = Field(..., max_length=20, description="Numéro de compte PCG, ex '401'")
    libelle: str = Field("", max_length=200, description="Libellé optionnel de la ligne")
    debit: float = Field(0.0, ge=0, description="Montant débit en € (positif). 0 si la ligne est au crédit.")
    credit: float = Field(0.0, ge=0, description="Montant crédit en € (positif). 0 si la ligne est au débit.")

    @model_validator(mode="after")
    def _at_least_one_movement(self):
        if self.debit == 0.0 and self.credit == 0.0:
            raise ValueError(
                "Each ecriture line requires positive 'debit' OR 'credit' (in €). "
                "Got both at 0 — likely format mismatch (e.g. you sent "
                "'montant'+'type' instead of canonical 'debit'/'credit')."
            )
        if self.debit > 0 and self.credit > 0:
            raise ValueError(
                "Each ecriture line must have EITHER 'debit' > 0 OR 'credit' > 0, "
                "not both. Split into two lines if needed."
            )
        return self


class VerifyPartieDoubleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ecritures: list[EcritureLineModel] = Field(..., max_length=50)


class VerifyCalculTVARequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    montant_ht: float = Field(..., ge=0, le=10_000_000)
    taux: float = Field(..., ge=0, le=100)
    actual_tva: float | None = Field(None, ge=0)
    actual_ttc: float | None = Field(None, ge=0)


class VerifyCompteClasseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    num: str = Field(..., max_length=20)
    expected_classe: str = Field(..., max_length=2)


class LookupStudiModuleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(..., max_length=500)


# ── Endpoints ─────────────────────────────────────────────────────


@router.post("/lookup_pcg")
async def endpoint_lookup_pcg(req: LookupPCGRequest) -> dict:
    """Numéro PCG → libellé + classe + suggestions si non trouvé."""
    return lookup_pcg_account(req.num)


@router.post("/verify_partie_double")
async def endpoint_verify_partie_double(req: VerifyPartieDoubleRequest) -> dict:
    """Vérifie sum(débits) == sum(crédits). Tolérance flottant 0.01€."""
    return verify_partie_double([line.model_dump() for line in req.ecritures])


@router.post("/verify_calcul_tva")
async def endpoint_verify_calcul_tva(req: VerifyCalculTVARequest) -> dict:
    """Vérifie calcul TVA standard FR (taux 0/2.1/5.5/10/20)."""
    return verify_calcul_tva(
        montant_ht=req.montant_ht,
        taux=req.taux,
        actual_tva=req.actual_tva,
        actual_ttc=req.actual_ttc,
    )


@router.post("/verify_compte_classe")
async def endpoint_verify_compte_classe(req: VerifyCompteClasseRequest) -> dict:
    """Vérifie qu'un compte appartient à une classe (1-9)."""
    return verify_compte_classe(num=req.num, expected_classe=req.expected_classe)


@router.post("/lookup_studi_module")
async def endpoint_lookup_studi_module(req: LookupStudiModuleRequest) -> dict:
    """Heuristique mapping concept → module Studi BC1.X / BC2.X / BC3.X."""
    return lookup_studi_module(req.query)


# ── OpenAPI summary endpoint (Dify Custom Tool config helper) ────


@router.get("/_openapi_summary", include_in_schema=False)
async def openapi_summary() -> dict:
    """Quick reference des 5 tools pour configurer Dify Custom Tools.

    Dify peut import un OpenAPI/Swagger spec depuis /openapi.json (FastAPI
    auto-genere). Ce endpoint donne juste la liste rapide pour copy-paste.
    """
    return {
        "base_url": "http://academie-api:8000/internal/compta/tools",
        "tools": [
            {"name": "lookup_pcg", "method": "POST", "input_schema": "LookupPCGRequest"},
            {"name": "verify_partie_double", "method": "POST", "input_schema": "VerifyPartieDoubleRequest"},
            {"name": "verify_calcul_tva", "method": "POST", "input_schema": "VerifyCalculTVARequest"},
            {"name": "verify_compte_classe", "method": "POST", "input_schema": "VerifyCompteClasseRequest"},
            {"name": "lookup_studi_module", "method": "POST", "input_schema": "LookupStudiModuleRequest"},
        ],
        "auth": "internal-network only (academie-net-bridge), no JWT",
        "note": "Dify chatflow worker accède via container network. Frontend ne doit jamais appeler directement.",
    }
