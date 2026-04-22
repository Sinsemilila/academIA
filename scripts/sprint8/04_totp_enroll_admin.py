#!/usr/bin/env python3
"""Refactor 2026-H2 Phase A4 — Enroll TOTP for an admin (or any) user via CLI.

Usage :
    python3 scripts/sprint8/04_totp_enroll_admin.py <username>

Why a CLI instead of UI : Phase A4a delivers backend only. The /settings UI
for self-enrollment lands in A4b. To protect the admin account TODAY, this
script :
  1. Generates a TOTP secret + recovery codes
  2. Prints the otpauth:// URI (paste in any TOTP app : Google Authenticator,
     1Password, Bitwarden, Aegis, Raivo, etc.) AND a terminal-rendered QR code
  3. Prompts user to scan + enter the first TOTP code to confirm
  4. Inserts row in user_totp + prints the 10 recovery codes (write down !)

Idempotent : refuses to re-enroll if user_totp row already exists. To re-enroll
disable first via the API or DELETE FROM user_totp WHERE user_id = ...
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Bootstrap : add backend/app to path so we can import totp + crypto helpers
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "webapp" / "backend"))

from app import totp as totp_helper  # noqa: E402

DB_USER = "sinse"
DB_NAME = "academie_db"
DB_CONTAINER = "postgres-academie"


def psql(sql: str, *params) -> str:
    """Run psql via docker exec ; return stdout. Use $1,$2... placeholders."""
    cmd = ["docker", "exec", "-i", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-tA"]
    if params:
        # asyncpg-style $N positional ; use psql variable substitution -v
        for i, p in enumerate(params, 1):
            cmd.extend(["-v", f"v{i}={p}"])
            sql = sql.replace(f"${i}", f":'v{i}'")
    cmd.extend(["-c", sql])
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: 04_totp_enroll_admin.py <username>", file=sys.stderr)
        return 2
    username = sys.argv[1]

    user_id_str = psql(
        "SELECT id FROM users WHERE username = $1", username
    )
    if not user_id_str:
        print(f"error: user {username!r} not found", file=sys.stderr)
        return 3
    user_id = int(user_id_str)

    existing = psql("SELECT 1 FROM user_totp WHERE user_id = $1", user_id)
    if existing:
        print(f"error: TOTP already enrolled for {username!r}.", file=sys.stderr)
        print("  to re-enroll: DELETE FROM user_totp WHERE user_id = "
              f"{user_id}; first.", file=sys.stderr)
        return 4

    secret = totp_helper.generate_secret()
    uri = totp_helper.provisioning_uri(secret, username)

    print()
    print("=" * 72)
    print(f"  TOTP enrollment for user: {username}  (user_id={user_id})")
    print("=" * 72)
    print()
    print("Method 1 — Scan QR code (terminal) :")
    print()
    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(uri)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except Exception as e:  # pragma: no cover
        print(f"  (terminal QR rendering failed: {e})")
    print()
    print("Method 2 — Paste this URI manually in your TOTP app :")
    print()
    print(f"  {uri}")
    print()
    print("Method 3 — Enter the secret manually if QR/URI unsupported :")
    print()
    print(f"  Secret (base32) : {secret}")
    print(f"  Issuer          : AcademIA")
    print(f"  Account         : {username}")
    print(f"  Algorithm       : SHA1, 6 digits, 30s period (RFC 6238 default)")
    print()
    print("=" * 72)
    print()
    code = input("Enter the 6-digit code shown by your TOTP app to confirm: ").strip()
    if not totp_helper.verify_code(secret, code):
        print("error: code invalid. Check device clock + retry.", file=sys.stderr)
        return 5

    plain_codes = totp_helper.generate_recovery_codes()
    hashed = totp_helper.hash_recovery_codes(plain_codes)

    psql(
        "INSERT INTO user_totp (user_id, secret, recovery_codes) VALUES ($1, $2, $3)",
        user_id, secret, json.dumps(hashed),
    )

    print()
    print("✅ TOTP enrolled successfully.")
    print()
    print("=" * 72)
    print("  RECOVERY CODES — Write these down NOW (each can only be used once)")
    print("=" * 72)
    for c in plain_codes:
        print(f"  {c}")
    print("=" * 72)
    print()
    print("These codes are now stored hashed in user_totp.recovery_codes.")
    print("Use them via /api/auth/login-mfa if you lose your TOTP device.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
