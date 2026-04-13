import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from . import database as db

# ── Config ──────────────────────────────────────────────
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-only-not-for-prod")
REFRESH_SECRET = os.environ.get("JWT_REFRESH_SECRET", "dev-only-not-for-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# ── Password helpers ────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT helpers ─────────────────────────────────────────
def create_access_token(user_id: int, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "username": username,
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, REFRESH_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise JWTError("Not an access token")
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expire",
        )


def decode_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, REFRESH_SECRET, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise JWTError("Not a refresh token")
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide ou expire",
        )


# ── Dependency: current user ────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    payload = decode_token(credentials.credentials)
    user_id = int(payload["sub"])

    async with db.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        if not row:
            raise HTTPException(status_code=401, detail="Utilisateur introuvable")
        # Track last seen (debounced: only update if >5 min since last update)
        await conn.execute(
            "UPDATE users SET last_seen_at = NOW() WHERE id = $1 AND (last_seen_at IS NULL OR last_seen_at < NOW() - INTERVAL '5 minutes')",
            user_id)
        return dict(row)


async def require_admin(user: dict = Depends(get_current_user)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin requis")
    return user
