from fastapi import APIRouter, Depends, HTTPException, Request
from ..models import LoginRequest, TokenResponse, RefreshRequest, UserResponse, UserCreate
from ..auth import (
    hash_password, verify_password, verify_and_rehash,
    create_access_token, create_refresh_token, decode_refresh_token,
    get_current_user, require_admin,
)
from ..rate_limit import limiter
from .. import database as db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, request: Request):
    # Rate limit: 5 login attempts per minute per IP
    limiter.check(request, max_requests=5, window_seconds=60)
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, username, password_hash FROM users WHERE username = $1",
            req.username,
        )
    if not row:
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    ok, new_hash = verify_and_rehash(req.password, row["password_hash"])
    if not ok:
        raise HTTPException(status_code=401, detail="Identifiants incorrects")

    # Phase A2 — silent migration bcrypt → argon2id on successful login.
    if new_hash:
        async with db.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET password_hash = $1 WHERE id = $2",
                new_hash, row["id"],
            )

    # Ensure eleve_id points to the correct eleve (fix UUID/user_N drift from Dify)
    async with db.pool.acquire() as conn:
        dify_user = row.get("dify_user_id") or f"user_{row['id']}"
        eleve = await conn.fetchrow(
            "SELECT id FROM eleves WHERE username = $1 OR username = $2 OR username = $3",
            req.username, dify_user, str(row.get("dify_user_id", ""))
        )
        if eleve:
            # Fix eleve username to match webapp username + link
            await conn.execute("UPDATE eleves SET username = $1 WHERE id = $2 AND username != $1", req.username, eleve["id"])
            await conn.execute(
                "UPDATE users SET eleve_id = $1 WHERE id = $2 AND (eleve_id IS NULL OR eleve_id != $1)",
                eleve["id"], row["id"],
            )

    access = create_access_token(row["id"], row["username"])
    refresh = create_refresh_token(row["id"], row["username"])
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, request: Request):
    """Exchange a valid refresh token for a new access + refresh pair."""
    limiter.check(request, max_requests=10, window_seconds=60)
    payload = decode_refresh_token(req.refresh_token)
    user_id = int(payload["sub"])
    username = payload["username"]

    # Verify user still exists
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id FROM users WHERE id = $1", user_id)
    if not row:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")

    access = create_access_token(user_id, username)
    refresh_new = create_refresh_token(user_id, username)
    return TokenResponse(access_token=access, refresh_token=refresh_new)


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
        # Create webapp user
        row = await conn.fetchrow(
            """INSERT INTO users (username, password_hash, display_name, exam_access)
               VALUES ($1, $2, $3, $4)
               RETURNING id, username, display_name, is_admin, exam_access""",
            req.username, hashed, req.display_name, req.exam_access,
        )
        # Also create matching eleve if not exists
        await conn.execute(
            """INSERT INTO eleves (username, created_at)
               VALUES ($1, NOW())
               ON CONFLICT (username) DO NOTHING""",
            req.username,
        )
        # Link eleve_id
        eleve = await conn.fetchrow(
            "SELECT id FROM eleves WHERE username = $1", req.username
        )
        if eleve:
            await conn.execute(
                "UPDATE users SET eleve_id = $1 WHERE id = $2",
                eleve["id"], row["id"],
            )

    return UserResponse(**dict(row))
