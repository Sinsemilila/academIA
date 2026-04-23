"""
Refactor 2026-H2 Phase A4b polish — WebAuthn / Passkeys scaffolding.

All endpoints return 501 Not Implemented unless `WEBAUTHN_ENABLED=true` is set.
The `webauthn_credentials` table + this router skeleton exist so the API
surface is reserved and the migration is in place. Full implementation is
planned Phase 2 (post-beta) per ADR-001 décision #7.

Future flow (when activated) :
  POST /api/security/webauthn/register-options   → server returns RP info + challenge
  POST /api/security/webauthn/register-verify    → client returns attestation, server stores credential
  POST /api/security/webauthn/auth-options       → server returns challenge + allowed creds
  POST /api/security/webauthn/auth-verify        → client returns assertion, server verifies
"""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import get_current_user

router = APIRouter(prefix="/api", tags=["webauthn"])


def _require_enabled() -> None:
    if os.environ.get("WEBAUTHN_ENABLED", "false").lower() not in ("1", "true", "yes"):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="WebAuthn / Passkeys non activé (feature flag WEBAUTHN_ENABLED off — Phase 2 post-beta).",
        )


@router.post("/security/webauthn/register-options", status_code=501)
async def webauthn_register_options(user: dict = Depends(get_current_user)):
    _require_enabled()
    raise HTTPException(status_code=501, detail="To be implemented Phase 2")


@router.post("/security/webauthn/register-verify", status_code=501)
async def webauthn_register_verify(user: dict = Depends(get_current_user)):
    _require_enabled()
    raise HTTPException(status_code=501, detail="To be implemented Phase 2")


@router.post("/security/webauthn/auth-options", status_code=501)
async def webauthn_auth_options():
    _require_enabled()
    raise HTTPException(status_code=501, detail="To be implemented Phase 2")


@router.post("/security/webauthn/auth-verify", status_code=501)
async def webauthn_auth_verify():
    _require_enabled()
    raise HTTPException(status_code=501, detail="To be implemented Phase 2")
