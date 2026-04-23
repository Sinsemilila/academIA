#!/usr/bin/env python3
"""
Refactor 2026-H2 Phase A4b polish — encrypt existing TOTP secrets at rest.

Idempotent : ré-exécutable en toute sécurité (skip rows déjà chiffrées).

Usage :
  docker exec academie-api python /app/scripts/sprint8/10_fernet_encrypt_totp.py
"""
import asyncio
import os
import sys

import asyncpg

# Reuse the encrypt helper to guarantee identical Fernet config (same key,
# same prefix detection).
sys.path.insert(0, "/app")
from app.totp import _FERNET_PREFIX, encrypt_secret  # noqa: E402


async def main():
    if not os.environ.get("TOTP_FERNET_KEY"):
        print("ERROR: TOTP_FERNET_KEY missing in env", file=sys.stderr)
        sys.exit(1)
    dsn = os.environ["DATABASE_URL"]
    conn = await asyncpg.connect(dsn)
    try:
        rows = await conn.fetch("SELECT user_id, secret FROM user_totp")
        encrypted = 0
        skipped = 0
        for r in rows:
            secret = r["secret"]
            if secret.startswith(_FERNET_PREFIX):
                skipped += 1
                continue
            new = encrypt_secret(secret)
            await conn.execute(
                "UPDATE user_totp SET secret = $1 WHERE user_id = $2",
                new, r["user_id"],
            )
            encrypted += 1
        print(f"Encrypted: {encrypted}  Skipped (already Fernet): {skipped}  Total rows: {len(rows)}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
