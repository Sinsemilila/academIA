"""
Refactor 2026-H2 Phase A3 — Security headers + CSP violation collector.

POST /api/csp-report
  Un-authed endpoint receiving Content-Security-Policy-Report-Only
  violation reports from browsers. Accepts both legacy
  `application/csp-report` and modern `application/reports+json`.

  Rate-limited 60r/min/IP (browsers can spam violations on a single
  page load if many resources fail).

  Stores into `csp_violations` table for 90 days, with PII-stripped
  URIs and SHA256-hashed daily-salted IPs.
"""

import hashlib
import json
import logging
from datetime import date
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from fastapi import APIRouter, HTTPException, Request, status

from .. import database as db
from ..rate_limit import limiter

logger = logging.getLogger("academie-api.security")
router = APIRouter(prefix="/api", tags=["security"])


def _strip_query(uri: str | None) -> str | None:
    if not uri:
        return uri
    try:
        parts = urlsplit(uri)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    except Exception:
        return uri


def _hash_ip(ip: str) -> str:
    salt = date.today().isoformat()
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()[:32]


def _normalize_report(payload: Any) -> list[dict[str, Any]]:
    """Accept both legacy { "csp-report": {...} } and modern Reporting API list."""
    if isinstance(payload, dict) and "csp-report" in payload:
        return [payload["csp-report"]]
    if isinstance(payload, list):
        out = []
        for r in payload:
            if isinstance(r, dict):
                body = r.get("body") or r
                out.append(body)
        return out
    if isinstance(payload, dict):
        return [payload]
    return []


@router.post("/csp-report", status_code=status.HTTP_204_NO_CONTENT)
async def csp_report(request: Request):
    limiter.check(request, max_requests=60, window_seconds=60)

    try:
        body = await request.body()
        if not body:
            return
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    forwarded = request.headers.get("x-forwarded-for")
    ip = (forwarded.split(",")[0].strip() if forwarded
          else request.client.host if request.client else "unknown")
    ip_hash = _hash_ip(ip)
    user_agent = (request.headers.get("user-agent") or "")[:512]

    reports = _normalize_report(payload)
    if not reports:
        return

    rows = []
    for r in reports[:10]:
        rows.append((
            ip_hash,
            user_agent,
            _strip_query(r.get("document-uri") or r.get("documentURL")),
            _strip_query(r.get("referrer")),
            r.get("violated-directive") or r.get("violatedDirective"),
            r.get("effective-directive") or r.get("effectiveDirective"),
            _strip_query(r.get("blocked-uri") or r.get("blockedURL")),
            r.get("source-file") or r.get("sourceFile"),
            r.get("line-number") or r.get("lineNumber"),
            r.get("column-number") or r.get("columnNumber"),
            r.get("status-code") or r.get("statusCode"),
            r.get("disposition") or "report",
            json.dumps(r),
        ))

    if rows:
        await db.pool.executemany(
            """
            INSERT INTO csp_violations (
              ip_hash, user_agent, document_uri, referrer,
              violated_directive, effective_directive, blocked_uri,
              source_file, line_number, column_number, status_code,
              disposition, raw_report
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
            """,
            rows,
        )


# ── A4 — TOTP MFA enrollment endpoints ─────────────────────────────
from fastapi import Depends
from pydantic import BaseModel, Field
from .. import totp as totp_helper
from ..auth import get_current_user, verify_password


class TotpEnrollStartResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_data_url: str


class TotpEnrollConfirmRequest(BaseModel):
    secret: str = Field(..., min_length=16, max_length=64)
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class TotpEnrollConfirmResponse(BaseModel):
    enrolled: bool
    recovery_codes: list[str]


class TotpDisableRequest(BaseModel):
    password: str
    code: str = Field(..., min_length=6, max_length=10)


class TotpStatusResponse(BaseModel):
    enrolled: bool
    enrolled_at: str | None = None
    recovery_codes_remaining: int = 0


@router.get("/security/totp/status", response_model=TotpStatusResponse)
async def totp_status(user: dict = Depends(get_current_user)):
    row = await db.pool.fetchrow(
        "SELECT enrolled_at, recovery_codes FROM user_totp WHERE user_id = $1",
        user["id"],
    )
    if not row:
        return TotpStatusResponse(enrolled=False)
    remaining = sum(1 for c in row["recovery_codes"] if c is not None) if row["recovery_codes"] else 0
    return TotpStatusResponse(
        enrolled=True,
        enrolled_at=row["enrolled_at"].isoformat() if row["enrolled_at"] else None,
        recovery_codes_remaining=remaining,
    )


@router.post("/security/totp/enroll-start", response_model=TotpEnrollStartResponse)
async def totp_enroll_start(user: dict = Depends(get_current_user)):
    existing = await db.pool.fetchval("SELECT 1 FROM user_totp WHERE user_id = $1", user["id"])
    if existing:
        raise HTTPException(status_code=409, detail="TOTP deja active. Disable first.")
    secret = totp_helper.generate_secret()
    uri = totp_helper.provisioning_uri(secret, user["username"])
    return TotpEnrollStartResponse(
        secret=secret,
        provisioning_uri=uri,
        qr_data_url=totp_helper.qr_data_url(uri),
    )


@router.post("/security/totp/enroll-confirm", response_model=TotpEnrollConfirmResponse)
async def totp_enroll_confirm(req: TotpEnrollConfirmRequest, user: dict = Depends(get_current_user)):
    if not totp_helper.verify_code(req.secret, req.code):
        raise HTTPException(status_code=400, detail="Code TOTP invalide. Verifiez l'horloge de votre app.")
    existing = await db.pool.fetchval("SELECT 1 FROM user_totp WHERE user_id = $1", user["id"])
    if existing:
        raise HTTPException(status_code=409, detail="TOTP deja active.")
    plain_codes = totp_helper.generate_recovery_codes()
    hashed = totp_helper.hash_recovery_codes(plain_codes)
    await db.pool.execute(
        "INSERT INTO user_totp (user_id, secret, recovery_codes) VALUES ($1, $2, $3)",
        user["id"], req.secret, json.dumps(hashed),
    )
    logger.info("totp_enrolled user_id=%d", user["id"])
    return TotpEnrollConfirmResponse(enrolled=True, recovery_codes=plain_codes)


@router.post("/security/totp/disable", status_code=204)
async def totp_disable(req: TotpDisableRequest, user: dict = Depends(get_current_user)):
    full_user = await db.pool.fetchrow(
        "SELECT password_hash FROM users WHERE id = $1", user["id"]
    )
    if not full_user or not verify_password(req.password, full_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Mot de passe incorrect")
    row = await db.pool.fetchrow(
        "SELECT secret, recovery_codes FROM user_totp WHERE user_id = $1", user["id"]
    )
    if not row:
        raise HTTPException(status_code=404, detail="TOTP non active")
    code_ok = totp_helper.verify_code(row["secret"], req.code)
    if not code_ok:
        ok, _ = totp_helper.verify_and_consume_recovery_code(row["recovery_codes"], req.code)
        code_ok = ok
    if not code_ok:
        raise HTTPException(status_code=401, detail="Code TOTP/recovery invalide")
    await db.pool.execute("DELETE FROM user_totp WHERE user_id = $1", user["id"])
    logger.warning("totp_disabled user_id=%d", user["id"])
