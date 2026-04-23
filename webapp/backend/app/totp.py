"""
Refactor 2026-H2 Phase A4 — TOTP MFA helpers.
Phase A4b polish (Session 47) — Fernet at-rest encryption for stored secrets.

Wraps pyotp + qrcode for enrollment, verify, and recovery codes.
"""

import base64
import io
import os
import secrets
import string

import pyotp
import qrcode
from cryptography.fernet import Fernet, InvalidToken
from passlib.context import CryptContext

ISSUER = "AcademIA"
RECOVERY_CODE_COUNT = 10
RECOVERY_CODE_LENGTH = 10  # 10 base32 chars = 50 bits entropy

# Same scheme as auth — recovery codes hashed with argon2id (bcrypt fallback).
_recovery_pwd = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto", argon2__type="ID")

# ── Fernet at-rest encryption for TOTP secret (A4b polish) ─────────────
# Stored ciphertext is base64-Fernet — detection via magic prefix `gAAAAA`
# (Fernet token version byte 0x80 → base64 starts with 'g'). Backward-compat :
# legacy plain secrets without that prefix are returned as-is on decrypt.
_FERNET_PREFIX = "gAAAAA"


def _fernet() -> Fernet | None:
    key = os.environ.get("TOTP_FERNET_KEY")
    if not key:
        return None
    return Fernet(key.encode())


def encrypt_secret(plain: str) -> str:
    """Encrypt a TOTP secret for at-rest storage. If TOTP_FERNET_KEY is not
    set, returns the plain secret unchanged (warn-only — code path used in
    dev/test where the key may be absent)."""
    f = _fernet()
    if f is None:
        return plain
    return f.encrypt(plain.encode()).decode()


def decrypt_secret(stored: str) -> str:
    """Decrypt if the stored value looks Fernet-encrypted ; otherwise return
    as-is (legacy compatibility for rows enrolled before A4b polish)."""
    if not stored or not stored.startswith(_FERNET_PREFIX):
        return stored
    f = _fernet()
    if f is None:
        raise RuntimeError("TOTP secret is encrypted but TOTP_FERNET_KEY is missing")
    try:
        return f.decrypt(stored.encode()).decode()
    except InvalidToken as e:
        raise RuntimeError("TOTP secret decrypt failed (wrong key?)") from e


def generate_secret() -> str:
    """RFC 4226 base32 secret, 160 bits."""
    return pyotp.random_base32()


def provisioning_uri(secret: str, username: str) -> str:
    """otpauth://totp/AcademIA:<username>?secret=...&issuer=AcademIA"""
    return pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name=ISSUER)


def qr_data_url(uri: str) -> str:
    """Render the provisioning URI as a base64 PNG data: URL."""
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def verify_code(secret: str, code: str) -> bool:
    """RFC 6238 verify with 1-step (±30s) tolerance for clock drift."""
    if not code or not code.isdigit() or len(code) != 6:
        return False
    return pyotp.TOTP(secret).verify(code, valid_window=1)


def generate_recovery_codes() -> list[str]:
    """Generate `RECOVERY_CODE_COUNT` codes of `RECOVERY_CODE_LENGTH` base32 chars."""
    alphabet = string.ascii_uppercase + string.digits
    return [
        "".join(secrets.choice(alphabet) for _ in range(RECOVERY_CODE_LENGTH))
        for _ in range(RECOVERY_CODE_COUNT)
    ]


def hash_recovery_codes(codes: list[str]) -> list[str]:
    """Hash each code for storage. List index = code position (used codes will be set to None)."""
    return [_recovery_pwd.hash(c) for c in codes]


def verify_and_consume_recovery_code(stored: list, code: str) -> tuple[bool, list]:
    """If `code` matches any non-null hash in `stored`, return (True, new list with that hash nulled).
    Otherwise (False, stored unchanged).
    """
    if not code or not isinstance(code, str):
        return False, stored
    code_norm = code.strip().upper().replace("-", "").replace(" ", "")
    for i, h in enumerate(stored):
        if h is None:
            continue
        try:
            if _recovery_pwd.verify(code_norm, h):
                new = list(stored)
                new[i] = None
                return True, new
        except Exception:
            continue
    return False, stored
