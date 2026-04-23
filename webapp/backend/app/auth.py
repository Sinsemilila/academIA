"""
Refactor 2026-H2 Phase A1 — auth via opaque session cookie.

JWT helpers removed (kept only password hashing). Session storage in Redis,
HttpOnly cookie __Host-as_session, CSRF double-submit via csrf_token cookie.

Public surface :
  hash_password, verify_password, verify_and_rehash  (A2 unchanged)
  get_current_user(request)                          (NEW : cookie-based)
  require_admin(user)                                (unchanged)
  COOKIE_SESSION, COOKIE_CSRF                        (cookie names)
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from passlib.context import CryptContext

from . import database as db
from . import sessions as session_store

COOKIE_SESSION = "as_session"
COOKIE_CSRF = "csrf_token"

# Refactor 2026-H2 Phase A2 — Argon2id + bcrypt rehash-on-login.
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__type="ID",
)


# ── Password helpers ────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def verify_and_rehash(plain: str, hashed: str) -> tuple[bool, str | None]:
    """Verify ; if scheme deprecated, return new hash for silent UPDATE."""
    return pwd_context.verify_and_update(plain, hashed)


# ── Dependency: current user via session cookie ─────────
async def get_current_user(request: Request) -> dict:
    token = request.cookies.get(COOKIE_SESSION)
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifie")
    sess = await session_store.get_session(token)
    if not sess:
        raise HTTPException(status_code=401, detail="Session expiree ou invalide")

    async with db.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", sess["user_id"])
        if not row:
            raise HTTPException(status_code=401, detail="Utilisateur introuvable")
        await conn.execute(
            "UPDATE users SET last_seen_at = NOW() WHERE id = $1 "
            "AND (last_seen_at IS NULL OR last_seen_at < NOW() - INTERVAL '5 minutes')",
            sess["user_id"],
        )
        user = dict(row)
        user["_session_token"] = token  # exposed for logout-all "keep current"
        return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin requis")
    return user
