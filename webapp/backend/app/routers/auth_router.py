"""Refactor 2026-H2 Phase A1 — auth via opaque session cookies + CSRF.

JWT token issuance + refresh removed. Login now creates a Redis session and
sets two cookies : __Host-as_session (HttpOnly) + csrf_token (JS-readable
for double-submit). Logout endpoints clear cookies + drop Redis state.
"""
import json

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from .. import database as db
from .. import sessions as session_store
from .. import totp as totp_helper
from ..auth import (
    COOKIE_CSRF,
    COOKIE_SESSION,
    get_current_user,
    hash_password,
    require_admin,
    verify_and_rehash,
    verify_password,
)
from ..models import LoginRequest, UserCreate, UserResponse
from ..rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _set_session_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    """Set the two A1 cookies. __Host- prefix forces Secure + Path=/ + no Domain."""
    response.set_cookie(
        key=COOKIE_SESSION,
        value=session_token,
        max_age=session_store.SESSION_TTL_SECONDS,
        path="/",
        secure=True,
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        key=COOKIE_CSRF,
        value=csrf_token,
        max_age=session_store.SESSION_TTL_SECONDS,
        path="/",
        secure=True,
        httponly=False,  # JS reads this for X-CSRF-Token header
        samesite="lax",
    )


def _clear_session_cookies(response: Response) -> None:
    response.delete_cookie(COOKIE_SESSION, path="/")
    response.delete_cookie(COOKIE_CSRF, path="/")


async def _issue_session_response(
    response: Response, request: Request, user_row: dict
) -> dict:
    """Create Redis session + set cookies + return user payload (no tokens in body)."""
    token, csrf = await session_store.create_session(
        user_id=user_row["id"],
        username=user_row["username"],
        ip=_client_ip(request),
        user_agent=request.headers.get("user-agent", ""),
    )
    _set_session_cookies(response, token, csrf)
    return {
        "user": {
            "id": user_row["id"],
            "username": user_row["username"],
            "is_admin": bool(user_row.get("is_admin", False)),
        }
    }


@router.post("/login")
async def login(req: LoginRequest, request: Request, response: Response):
    limiter.check(request, max_requests=5, window_seconds=60)
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, username, password_hash, is_admin, dify_user_id, eleve_id FROM users WHERE username = $1",
            req.username,
        )
    if not row:
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    ok, new_hash = verify_and_rehash(req.password, row["password_hash"])
    if not ok:
        raise HTTPException(status_code=401, detail="Identifiants incorrects")

    if new_hash:
        async with db.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET password_hash = $1 WHERE id = $2",
                new_hash, row["id"],
            )

    has_totp = await db.pool.fetchval(
        "SELECT 1 FROM user_totp WHERE user_id = $1", row["id"]
    )
    if has_totp:
        return {"mfa_required": True, "username": req.username}

    # Ensure eleve_id linkage (legacy logic preserved)
    async with db.pool.acquire() as conn:
        dify_user = row.get("dify_user_id") or f"user_{row['id']}"
        eleve = await conn.fetchrow(
            "SELECT id FROM eleves WHERE username = $1 OR username = $2 OR username = $3",
            req.username, dify_user, str(row.get("dify_user_id", ""))
        )
        if eleve:
            await conn.execute("UPDATE eleves SET username = $1 WHERE id = $2 AND username != $1", req.username, eleve["id"])
            await conn.execute(
                "UPDATE users SET eleve_id = $1 WHERE id = $2 AND (eleve_id IS NULL OR eleve_id != $1)",
                eleve["id"], row["id"],
            )

    return await _issue_session_response(response, request, dict(row))


class LoginMfaRequest(BaseModel):
    username: str
    password: str
    code: str = Field(..., min_length=6, max_length=10)


@router.post("/login-mfa")
async def login_mfa(req: LoginMfaRequest, request: Request, response: Response):
    """Phase A4 — second factor verification after /login returned mfa_required."""
    limiter.check(request, max_requests=5, window_seconds=60)
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, username, password_hash, is_admin FROM users WHERE username = $1",
            req.username,
        )
    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")

    totp_row = await db.pool.fetchrow(
        "SELECT secret, recovery_codes FROM user_totp WHERE user_id = $1", row["id"]
    )
    if not totp_row:
        raise HTTPException(status_code=400, detail="MFA non active pour cet utilisateur")

    code_ok = totp_helper.verify_code(totp_row["secret"], req.code)
    used_recovery = False
    if not code_ok:
        ok, new_codes = totp_helper.verify_and_consume_recovery_code(
            totp_row["recovery_codes"], req.code
        )
        if ok:
            code_ok = True
            used_recovery = True
            await db.pool.execute(
                "UPDATE user_totp SET recovery_codes = $1, recovery_codes_used = recovery_codes_used + 1, last_used_at = now() WHERE user_id = $2",
                json.dumps(new_codes), row["id"],
            )
    if not code_ok:
        raise HTTPException(status_code=401, detail="Code TOTP/recovery invalide")

    if not used_recovery:
        await db.pool.execute(
            "UPDATE user_totp SET last_used_at = now() WHERE user_id = $1", row["id"]
        )

    return await _issue_session_response(response, request, dict(row))


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response):
    """Drop current session (no auth required — best effort)."""
    token = request.cookies.get(COOKIE_SESSION)
    if token:
        await session_store.delete_session(token)
    _clear_session_cookies(response)


@router.post("/logout-all-sessions", status_code=204)
async def logout_all_sessions(
    request: Request, response: Response, user: dict = Depends(get_current_user),
):
    """Revoke ALL sessions for the current user (including this one)."""
    limiter.check(request, max_requests=5, window_seconds=60)
    await session_store.delete_all_sessions_for_user(user["id"])
    _clear_session_cookies(response)


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        username=user["username"],
        display_name=user.get("display_name"),
        is_admin=user["is_admin"],
        exam_access=user["exam_access"],
    )


@router.post("/users", response_model=UserResponse)
async def create_user(req: UserCreate, admin: dict = Depends(require_admin)):
    hashed = hash_password(req.password)
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO users (username, password_hash, display_name, exam_access)
               VALUES ($1, $2, $3, $4)
               RETURNING id, username, display_name, is_admin, exam_access""",
            req.username, hashed, req.display_name, req.exam_access,
        )
        await conn.execute(
            """INSERT INTO eleves (username, created_at)
               VALUES ($1, NOW())
               ON CONFLICT (username) DO NOTHING""",
            req.username,
        )
        eleve = await conn.fetchrow(
            "SELECT id FROM eleves WHERE username = $1", req.username
        )
        if eleve:
            await conn.execute(
                "UPDATE users SET eleve_id = $1 WHERE id = $2",
                eleve["id"], row["id"],
            )
    return UserResponse(**dict(row))
