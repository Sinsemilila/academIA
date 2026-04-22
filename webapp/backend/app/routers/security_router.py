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
