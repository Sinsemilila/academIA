from fastapi import APIRouter, Depends, HTTPException, Request
from ..models import LoginRequest, TokenResponse, RefreshRequest, UserResponse, UserCreate
from ..auth import (
    hash_password, verify_password,
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
    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")

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
